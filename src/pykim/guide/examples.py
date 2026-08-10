"""Katalog der mitinstallierten PyKIM-Beispielprogramme."""

import ast
import os
import subprocess
import sys
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path


@dataclass(frozen=True)
class ExampleProgram:
    name: str
    title: str
    category: str
    description: str
    path: Path
    source: str


CATEGORIES = {
    "color_checkerboard": "Farben und Schleifen",
    "color_palette": "Farben",
    "color_sensor": "Farben und Sensoren",
    "color_tones": "Farben und Töne",
    "farben_melodie_aufgabe": "Musterlösungen",
    "follow_path": "Bewegung",
    "fuer_elise": "Musik",
    "interaktive_steuerung_aufgabe": "Musterlösungen",
    "mehrere_pixel": "Mehrere Pixel",
    "musik_pixel_aufgabe": "Musterlösungen",
    "pachelbel_canon": "Musik",
    "paint_line": "Zeichnen",
    "paint_path": "Zeichnen",
    "punktlinie_aufgabe": "Musterlösungen",
    "quadrat_aufgabe": "Musterlösungen",
    "rhythmus_aufgabe": "Musterlösungen",
    "schachbrett_aufgabe": "Musterlösungen",
    "tonleiter_aufgabe": "Musterlösungen",
    "treppe_aufgabe": "Musterlösungen",
    "vier_quadrate_aufgabe": "Musterlösungen",
}


def example_programs() -> tuple[ExampleProgram, ...]:
    result = []
    root = files("pykim.examples")
    for name, category in CATEGORIES.items():
        resource = root.joinpath(f"{name}.py")
        source = resource.read_text(encoding="utf-8")
        description = ast.get_docstring(ast.parse(source)) or "Ausführbares PyKIM-Beispiel"
        result.append(
            ExampleProgram(
                name=name,
                title=name.replace("_aufgabe", "").replace("_", " ").title(),
                category=category,
                description=description,
                path=Path(str(resource)).resolve(),
                source=source,
            )
        )
    return tuple(result)


def _example(name: str) -> ExampleProgram:
    try:
        return next(example for example in example_programs() if example.name == name)
    except StopIteration:
        raise ValueError(f"Unbekanntes PyKIM-Beispiel: {name}") from None


def launch_example(name: str) -> Path:
    """Starte ausschließlich ein Programm aus dem installierten Beispielkatalog."""
    example = _example(name)
    environment = os.environ.copy()
    environment["PYKIM_PROGRESS_MODE"] = "disabled"
    subprocess.Popen(
        [sys.executable, str(example.path)],
        cwd=example.path.parent,
        env=environment,
    )
    return example.path


def copy_example_to_course(name: str, course: str | Path) -> tuple[Path, bool]:
    """Lege eine bearbeitbare Kopie an, ohne vorhandene Schülerarbeit zu ersetzen."""
    example = _example(name)
    root = Path(course).expanduser().resolve()
    target = root / "eigene_projekte" / "beispiele" / f"{name}.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return target, False
    target.write_text(example.source, encoding="utf-8")
    return target, True
