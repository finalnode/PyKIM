"""Persönliche PyKIM- und Pyxel-Projekte im portablen Kursordner."""

from __future__ import annotations

import json
import os
import re
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .interpreter import command_for
from tempfile import NamedTemporaryFile

PROJECTS_DIRECTORY = "Projekte"
METADATA_FILE = "projekt.json"


@dataclass(frozen=True)
class StudentProject:
    slug: str
    name: str
    kind: str
    directory: Path
    entrypoint: Path
    resources: Path | None


TEMPLATES = {
    "empty": """\
\"\"\"Mein Python-Projekt.\"\"\"

print("Hallo Welt!")
""",
    "pykim": """\
\"\"\"Mein PyKIM-Projekt.\"\"\"

from pykim import *

speed(30)
paint("orange")
right(10)
paint_stop()

run()
""",
    "pyxel": """\
\"\"\"Mein Pyxel-Spiel mit eigenen Ressourcen.\"\"\"

import pyxel

pyxel.init(160, 120, title="Mein Pyxel-Spiel")
pyxel.load("ressourcen.pyxres")


def update():
    if pyxel.btnp(pyxel.KEY_Q):
        pyxel.quit()


def draw():
    pyxel.cls(0)
    pyxel.text(10, 10, "Mein Spiel", 7)


pyxel.run(update, draw)
""",
}


def project_slug(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name.strip())
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_name).strip("_")
    if not slug:
        raise ValueError("Der Projektname benötigt mindestens einen Buchstaben oder eine Zahl.")
    return slug[:60]


def projects_directory(course: str | Path) -> Path:
    return Path(course).expanduser().resolve() / PROJECTS_DIRECTORY


def _safe_child(directory: Path, value: str, label: str) -> Path:
    path = (directory / value).resolve()
    if not path.is_relative_to(directory.resolve()) or path.parent != directory.resolve():
        raise ValueError(f"Ungültiger {label} in {METADATA_FILE}.")
    return path


def _write_json(path: Path, data: dict[str, object]) -> None:
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=".projekt-", delete=False
        ) as temporary:
            json.dump(data, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def create_project(
    course: str | Path,
    name: str,
    kind: str = "pykim",
    *,
    source: str | None = None,
    parent: str = "",
    with_resources: bool | None = None,
) -> StudentProject:
    if kind not in TEMPLATES:
        raise ValueError(f"Unbekannte Projektvorlage: {kind}")
    root = projects_directory(course)
    if parent:
        parent_slug = project_slug(parent)
        root = root / parent_slug
    root.mkdir(parents=True, exist_ok=True)
    slug = project_slug(name)
    directory = root / slug
    try:
        directory.mkdir()
    except FileExistsError:
        raise FileExistsError(f"Das Projekt „{name}“ existiert bereits.") from None
    entrypoint = directory / "main.py"
    entrypoint.write_text(source if source is not None else TEMPLATES[kind], encoding="utf-8")
    if with_resources is None:
        with_resources = kind == "pyxel"
    resource_name = "ressourcen.pyxres" if with_resources else ""
    _write_json(
        directory / METADATA_FILE,
        {
            "format": 1,
            "name": name.strip(),
            "kind": kind,
            "entrypoint": entrypoint.name,
            "resources": resource_name,
        },
    )
    return load_project(directory)


def load_project(directory: str | Path) -> StudentProject:
    root = Path(directory).expanduser().resolve()
    try:
        data = json.loads((root / METADATA_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as error:
        raise ValueError(f"Projektdatei konnte nicht gelesen werden: {error}") from error
    if not isinstance(data, dict) or data.get("format") != 1:
        raise ValueError("Unbekanntes Projektformat.")
    name = data.get("name")
    kind = data.get("kind")
    entrypoint_name = data.get("entrypoint")
    resource_name = data.get("resources", "")
    if not all(isinstance(value, str) for value in (name, kind, entrypoint_name, resource_name)):
        raise ValueError("Unvollständige Projektdatei.")
    entrypoint = _safe_child(root, entrypoint_name, "Programmeinstieg")
    resources = _safe_child(root, resource_name, "Ressourcenpfad") if resource_name else None
    return StudentProject(root.name, name, kind, root, entrypoint, resources)


def student_projects(course: str | Path) -> tuple[StudentProject, ...]:
    root = projects_directory(course)
    try:
        metadata_files = tuple(root.rglob(METADATA_FILE))
    except OSError:
        return ()
    result = []
    for metadata in metadata_files:
        try:
            result.append(load_project(metadata.parent))
        except ValueError:
            continue
    return tuple(sorted(result, key=lambda project: project.name.casefold()))


def launch_project(project: StudentProject, course: str | Path) -> Path:
    course_root = Path(course).expanduser().resolve()
    if not project.directory.is_relative_to(projects_directory(course_root)):
        raise ValueError("Das Projekt liegt nicht im Kursordner.")
    if not project.entrypoint.is_file():
        raise FileNotFoundError(f"{project.entrypoint.name} wurde nicht gefunden.")
    if project.resources is not None and not project.resources.is_file():
        raise RuntimeError(
            "Die Ressourcendatei fehlt noch. Öffne zuerst den Sprite- und Musikeditor "
            "und speichere die Ressourcen."
        )
    from .runtime import selected_runtime

    python = selected_runtime(course_root).executable
    subprocess.Popen([*command_for(python), str(project.entrypoint)], cwd=project.directory)
    return project.entrypoint


def launch_project_editor(project: StudentProject, course: str | Path) -> Path:
    if project.resources is None:
        raise ValueError("Dieses Projekt besitzt keine Pyxel-Ressourcendatei.")
    from .runtime import selected_runtime
    from .system import launch_pyxel_editor

    python = selected_runtime(course).executable
    return launch_pyxel_editor(project.resources, python=python)
