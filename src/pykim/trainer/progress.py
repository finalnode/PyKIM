"""Minimaler, anwendungsunabhängiger Lernstand für PyKIM-Trainerläufe."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from .models import CheckReport


COURSE_ROOT_ENV = "PYKIM_COURSE_DIR"


def _progress_file() -> Path | None:
    configured = os.environ.get(COURSE_ROOT_ENV)
    if not configured:
        return None
    return Path(configured).expanduser().resolve() / ".pykim" / "progress.json"


def record_attempt(exercise: str, report: CheckReport, source: str = "") -> bool:
    """Ergänze einen Trainerlauf, wenn die Host-Anwendung einen Kurs übergibt."""
    target = _progress_file()
    if target is None:
        return False
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except (FileNotFoundError, OSError, ValueError, TypeError):
        data = {}
    data.setdefault("format", 1)
    attempts = data.setdefault("attempts", [])
    if not isinstance(attempts, list):
        attempts = data["attempts"] = []
    optimization = report.optimization
    attempts.append({
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
    })
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w", encoding="utf-8", dir=target.parent, delete=False
    ) as temporary:
        json.dump(data, temporary, ensure_ascii=False, indent=2)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, target)
    return True


__all__ = ["COURSE_ROOT_ENV", "record_attempt"]
