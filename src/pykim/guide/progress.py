"""Synchronisierbarer Lernfortschritt im jeweiligen Kursordner."""

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from pykim.trainer.models import CheckReport

from .course import get_course_directory


def _empty_progress() -> dict[str, object]:
    return {"format": 1, "attempts": [], "journal": {}}


def progress_file(course: Path | None = None) -> Path | None:
    course = get_course_directory() if course is None else course
    return None if course is None else course / ".pykim" / "progress.json"


def load_progress(course: Path | None = None) -> dict[str, object]:
    target = progress_file(course)
    if target is None or not target.exists():
        return _empty_progress()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else _empty_progress()
    except (OSError, ValueError):
        return _empty_progress()


def _save(data: dict[str, object], course: Path | None = None) -> None:
    target = progress_file(course)
    if target is None:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    # Schreiben und Ersetzen verhindert halbe JSON-Dateien bei Abbruch oder Sync.
    with NamedTemporaryFile(
        "w", encoding="utf-8", dir=target.parent, delete=False
    ) as temporary:
        json.dump(data, temporary, ensure_ascii=False, indent=2)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, target)


def record_attempt(
    exercise: str,
    report: CheckReport,
    source: str = "",
    *,
    course: Path | None = None,
) -> bool:
    """Speichere einen Trainerlauf; ohne Kurskonfiguration geschieht nichts."""
    target = progress_file(course)
    if target is None:
        return False
    data = load_progress(course)
    attempts = data.setdefault("attempts", [])
    if not isinstance(attempts, list):
        attempts = data["attempts"] = []
    optimization = report.optimization
    attempts.append(
        {
            "exercise": exercise,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "passed": report.passed,
            "total": len(report.results),
            "successful": report.successful,
            "optimization": None if optimization is None else {
                "score": optimization.score,
                "maximum": optimization.maximum,
            },
            "tests": [
                {
                    "index": index,
                    "passed": result.passed,
                    "message": result.message,
                    "hint": result.hint if not result.passed else "",
                }
                for index, result in enumerate(report.results, start=1)
            ],
            "source": source,
        }
    )
    _save(data, course)
    return True


def save_journal_entry(
    exercise: str,
    text: str,
    *,
    course: Path | None = None,
) -> None:
    data = load_progress(course)
    journal = data.setdefault("journal", {})
    if not isinstance(journal, dict):
        journal = data["journal"] = {}
    journal[exercise] = {
        "text": text,
        "updated": datetime.now(timezone.utc).isoformat(),
    }
    _save(data, course)


def remove_packaged_example_attempts(course: Path | None = None) -> int:
    """Entferne irrtümlich erfasste Musterlösungen und sichere den alten Stand."""
    target = progress_file(course)
    if target is None or not target.exists():
        return 0
    from .examples import example_programs

    example_sources = {example.source for example in example_programs()}
    data = load_progress(course)
    attempts = data.get("attempts", [])
    if not isinstance(attempts, list):
        return 0
    retained = [
        attempt
        for attempt in attempts
        if not isinstance(attempt, dict) or attempt.get("source") not in example_sources
    ]
    removed = len(attempts) - len(retained)
    if removed:
        backup = target.with_name("progress.before-example-cleanup.json")
        if not backup.exists():
            shutil.copy2(target, backup)
        data["attempts"] = retained
        _save(data, course)
    return removed
