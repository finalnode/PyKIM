"""Baue und prüfe ein PyKIM-Wheel aus einer frischen Quellkopie."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
PROJECT_FILES = ("pyproject.toml", "README.md", "LICENSE")
REMOVED_MODULES = {
    "pykim/guide",
    "pykim/submission",
    "pykim/trainer/activities.py",
    "pykim/trainer/content.py",
    "pykim/trainer/exercises",
    "pykim/trainer/feedback.py",
    "pykim/trainer/progress.py",
    "pykim/trainer/runner.py",
}


def validate_wheel(wheel: str | Path) -> tuple[str, ...]:
    """Stelle sicher, dass das Wheel nur den eigenständigen PyKIM-Kern enthält."""
    path = Path(wheel)
    with zipfile.ZipFile(path) as archive:
        members = tuple(sorted(archive.namelist()))
    if not members:
        raise ValueError("Das PyKIM-Wheel ist leer.")
    for member in members:
        parts = PurePosixPath(member).parts
        top_level = parts[0] if parts else ""
        normalized = top_level.lower()
        if top_level == "pykim" or (
            normalized.startswith("pykim-") and normalized.endswith(".dist-info")
        ):
            continue
        raise ValueError(f"Fremder Paketinhalt im PyKIM-Wheel: {member}")
    for removed in sorted(REMOVED_MODULES):
        if any(
            member == removed or member.startswith(removed + "/")
            for member in members
        ):
            raise ValueError(f"Ausgelagerter Paketinhalt im PyKIM-Wheel: {removed}")
    return members


def build_wheel(output_directory: str | Path) -> Path:
    """Baue das Wheel isoliert von lokalen ``build/``-Altständen."""
    output = Path(output_directory).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pykim-package-") as temporary:
        base = Path(temporary)
        project = base / "project"
        wheels = base / "wheels"
        project.mkdir()
        wheels.mkdir()
        for name in PROJECT_FILES:
            shutil.copy2(ROOT / name, project / name)
        shutil.copytree(
            ROOT / "src",
            project / "src",
            ignore=shutil.ignore_patterns("__pycache__", "*.py[cod]", "*.egg-info"),
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                str(project),
                "--no-deps",
                "--wheel-dir",
                str(wheels),
            ],
            check=True,
        )
        built = tuple(wheels.glob("*.whl"))
        if len(built) != 1:
            raise RuntimeError(
                f"Erwartet wurde genau ein PyKIM-Wheel, gefunden: {len(built)}"
            )
        validate_wheel(built[0])
        destination = output / built[0].name
        shutil.copy2(built[0], destination)
    return destination


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="dist", help="Zielordner für das Wheel")
    options = parser.parse_args(arguments)
    wheel = build_wheel(options.output)
    print(f"Sauberes PyKIM-Wheel: {wheel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
