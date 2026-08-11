"""Validiere Kursstruktur und erzeuge reproduzierbare SHA-256-Hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TESTS = {
    "pixels", "no-extra-pixels", "pixel-count", "square", "position",
    "positions", "pixel-names", "visibility", "audio", "loop",
    "nested-loop", "parallel", "condition", "function", "calls",
    "class", "methods", "super-init",
}


def content_files() -> list[Path]:
    result = [ROOT / "content.yml"]
    for folder, suffix in (("Skripte", ".md"), ("Aufgaben", ".md"), ("Trainer", ".yml")):
        result.extend(path for path in (ROOT / folder).rglob(f"*{suffix}") if path.is_file())
    return sorted(result)


def validate() -> None:
    catalog = yaml.safe_load((ROOT / "content.yml").read_text(encoding="utf-8"))
    if not isinstance(catalog, dict) or catalog.get("format") != 1:
        raise ValueError("content.yml benötigt format: 1.")
    exercises = catalog.get("exercises")
    if not isinstance(exercises, list):
        raise ValueError("content.yml benötigt eine Aufgabenliste.")
    seen = set()
    for entry in exercises:
        exercise_id = entry.get("id")
        if not isinstance(exercise_id, str) or exercise_id in seen:
            raise ValueError(f"Ungültige oder doppelte Aufgabenkennung: {exercise_id!r}")
        seen.add(exercise_id)
        assignment = ROOT / entry.get("assignment", "")
        trainer = ROOT / entry.get("trainer", "")
        if not assignment.is_file() or not trainer.is_file():
            raise ValueError(f"Aufgabe oder Trainer fehlt für {exercise_id}.")
        definition = yaml.safe_load(trainer.read_text(encoding="utf-8"))
        if definition.get("format") != 1 or definition.get("id") != exercise_id:
            raise ValueError(f"Trainerkennung stimmt nicht: {trainer}")
        tests = definition.get("tests")
        if not isinstance(tests, list) or not tests:
            raise ValueError(f"{trainer} benötigt mindestens einen Test.")
        unknown = {test.get("type") for test in tests} - ALLOWED_TESTS
        if unknown:
            raise ValueError(f"Unbekannte Prüftypen in {trainer}: {sorted(unknown)}")


def hashes() -> dict[str, object]:
    files = {
        path.relative_to(ROOT).as_posix(): {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size": path.stat().st_size,
        }
        for path in content_files()
    }
    return {"format": 1, "algorithm": "sha256", "files": files}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-hashes", action="store_true")
    options = parser.parse_args()
    validate()
    rendered = json.dumps(hashes(), ensure_ascii=False, indent=2) + "\n"
    target = ROOT / ".pykim" / "hashes.json"
    if options.write_hashes:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    elif not target.is_file() or target.read_text(encoding="utf-8") != rendered:
        raise SystemExit(".pykim/hashes.json ist nicht aktuell.")
    print(f"Kursinhalt gültig: {len(hashes()['files'])} Dateien")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
