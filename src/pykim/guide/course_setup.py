"""Schlanke Kurskonfiguration ohne Schlüssel oder Verschlüsselungsdaten."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile


SETUP_FORMAT = "pykim-course-setup-v1"
SETUP_FILENAME = "course.pykim-setup"


@dataclass(frozen=True)
class CourseSetup:
    name: str
    teacher: str
    school: str
    course: str
    repository: str
    branch: str
    scripts_path: str
    assignments_path: str
    trainers_path: str

    @property
    def certificate_name(self) -> str:
        """Kompatibilität für den vorhandenen Inhalts-Synchronisierer."""
        return self.name

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "pykim-kurs"


def _safe_path(value: object, label: str) -> str:
    path = str(value).strip().strip("/")
    if not path or path.startswith(".") or ".." in path.split("/"):
        raise ValueError(f"Der Konfigurationspfad {label} ist unsicher.")
    return path


def setup_info(data: bytes | str | Path) -> CourseSetup:
    raw = Path(data).read_bytes() if isinstance(data, Path) else (
        data.encode("utf-8") if isinstance(data, str) else data
    )
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Die Datei ist keine gültige PyKIM-Setupdatei.") from error
    required = {
        "format", "name", "teacher", "school", "course", "repository", "branch",
        "scripts_path", "assignments_path", "trainers_path",
    }
    if not isinstance(document, dict) or set(document) != required:
        raise ValueError("Die PyKIM-Setupdatei ist unvollständig.")
    if document.get("format") != SETUP_FORMAT:
        raise ValueError("Die Datei ist keine unterstützte PyKIM-Setupdatei.")
    if not all(isinstance(document.get(key), str) and document[key].strip() for key in required):
        raise ValueError("Die PyKIM-Setupdatei enthält leere Angaben.")
    name = document["name"].strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+\.pykim-setup", name):
        raise ValueError("Der Name der Setupdatei ist ungültig.")
    repository = document["repository"].strip()
    if not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?", repository):
        raise ValueError("Das Kursrepository muss eine öffentliche GitHub-HTTPS-Adresse sein.")
    branch = document["branch"].strip()
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch) or ".." in branch.split("/"):
        raise ValueError("Der Inhaltsbranch ist ungültig.")
    return CourseSetup(
        name=name,
        teacher=document["teacher"].strip(),
        school=document["school"].strip(),
        course=document["course"].strip(),
        repository=repository,
        branch=branch,
        scripts_path=_safe_path(document["scripts_path"], "scripts_path"),
        assignments_path=_safe_path(document["assignments_path"], "assignments_path"),
        trainers_path=_safe_path(document["trainers_path"], "trainers_path"),
    )


def course_setup_path(course: str | Path) -> Path:
    return Path(course).expanduser().resolve() / ".pykim" / SETUP_FILENAME


def course_setup_info(course: str | Path) -> CourseSetup | None:
    path = course_setup_path(course)
    return setup_info(path) if path.is_file() else None


def install_course_setup(data: bytes, course: str | Path) -> CourseSetup:
    """Lese, synchronisiere und installiere eine Kurs-Setupdatei."""
    info = setup_info(data)
    from .updates import sync_certificate_content

    sync_certificate_content(info)
    target = course_setup_path(course)
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("wb", dir=target.parent, delete=False) as temporary:
        temporary.write(data)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, target)
    from .course import provision_course_exercises

    provision_course_exercises(course)
    return info


def verify_installed_course_setup(course: str | Path, *, allow_offline: bool = False):
    path = course_setup_path(course)
    if not path.is_file():
        raise FileNotFoundError("Importiere zuerst die Setupdatei deiner Lehrkraft.")
    data = path.read_bytes()
    info = setup_info(data)
    # Die Setupdatei ist momentan reine Konfiguration. Eine kryptografische
    # Vertrauensprüfung wird später als getrennte Schicht ergänzt.
    from .updates import TrainerVerification

    return info, TrainerVerification(False, False)


def generate_course_setup(
    output_directory: str | Path,
    *,
    teacher: str,
    school: str,
    course: str,
    repository: str,
    branch: str = "main",
    scripts_path: str = "Skripte",
    assignments_path: str = "Aufgaben",
    trainers_path: str = "Trainer",
) -> Path:
    """Erzeuge eine schlanke Setupdatei ohne Schlüssel oder Hashfreigabe."""
    name = f"{_slug(course)}.pykim-setup"
    document = {
        "format": SETUP_FORMAT,
        "name": name,
        "teacher": teacher,
        "school": school,
        "course": course,
        "repository": repository,
        "branch": branch,
        "scripts_path": scripts_path,
        "assignments_path": assignments_path,
        "trainers_path": trainers_path,
    }
    data = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    setup_info(data)
    root = Path(output_directory).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    setup_path = root / name
    setup_path.write_bytes(data)
    return setup_path
