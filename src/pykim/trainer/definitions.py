"""Sicheres, deklaratives Format für PyKIM-Trainingsdefinitionen."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path

import yaml

from .authoring import audit_exercise
from .builder import ExerciseBuilder
from .models import Exercise


RULE_METHODS = {
    "loop": "require_loop",
    "nested-loop": "require_nested_loop",
    "parallel": "require_parallel",
}
FEEDBACK_KEYS = {"success", "failure", "hint"}
RULE_FIELDS = {
    "pixels": {"cells", "paths", "checkerboard", "stairs", "exact"},
    "no-extra-pixels": {"cells", "paths", "checkerboard", "stairs"},
    "pixel-count": {"count"},
    "square": {"start", "side"},
    "position": {"position", "pixel"},
    "positions": {"positions"},
    "pixel-names": {"names"},
    "visibility": {"pixel", "visible"},
    "audio": {"events"},
    "loop": {"kind"},
    "nested-loop": set(),
    "parallel": set(),
    "condition": {"calls"},
    "function": {"name", "parameters", "returns"},
    "function-cases": {"name", "cases"},
    "calls": {"names"},
    "class": {"name", "base"},
    "methods": {"class", "names"},
    "super-init": {"class"},
}


def _position(value, label: str = "Position") -> tuple[int, int]:
    if not isinstance(value, list) or len(value) != 2 or not all(
        isinstance(item, int) and not isinstance(item, bool) for item in value
    ):
        raise ValueError(f"{label} muss als [x, y] mit ganzen Zahlen angegeben werden.")
    return value[0], value[1]


def _feedback(rule: dict) -> dict[str, str]:
    result = {}
    for key in FEEDBACK_KEYS:
        if key in rule:
            if not isinstance(rule[key], str):
                raise ValueError(f"{key} muss Text sein.")
            result[key] = rule[key]
    return result


def _line(cells: dict, start, end, color=None) -> None:
    x1, y1 = _position(start, "Linienstart")
    x2, y2 = _position(end, "Linienende")
    dx = 0 if x1 == x2 else (1 if x2 > x1 else -1)
    dy = 0 if y1 == y2 else (1 if y2 > y1 else -1)
    if dx and dy and abs(x2 - x1) != abs(y2 - y1):
        raise ValueError("Linien müssen waagerecht, senkrecht oder diagonal verlaufen.")
    for distance in range(max(abs(x2 - x1), abs(y2 - y1)) + 1):
        cells[(x1 + dx * distance, y1 + dy * distance)] = color


def _expected_pixels(rule: dict):
    colorless = True
    cells: dict[tuple[int, int], str | int | None] = {}
    for item in rule.get("cells", []):
        if not isinstance(item, list) or len(item) not in {2, 3}:
            raise ValueError("Ein Pixel muss als [x, y] oder [x, y, farbe] angegeben werden.")
        position = _position(item[:2], "Pixel")
        color = item[2] if len(item) == 3 else None
        colorless = colorless and color is None
        cells[position] = color
    for path in rule.get("paths", []):
        if not isinstance(path, dict):
            raise ValueError("Ein Pfad muss start, end und optional color enthalten.")
        color = path.get("color")
        colorless = colorless and color is None
        _line(cells, path.get("start"), path.get("end"), color)
    if "checkerboard" in rule:
        spec = rule["checkerboard"]
        x, y = _position(spec.get("start"), "Schachbrettstart")
        width, height = spec.get("size", [])
        colors = spec.get("colors", [])
        if not all(isinstance(value, int) and value > 0 for value in (width, height)):
            raise ValueError("Die Schachbrettgröße muss zwei positive Zahlen enthalten.")
        if not isinstance(colors, list) or len(colors) != 2:
            raise ValueError("Ein Schachbrett benötigt genau zwei Farben.")
        colorless = False
        for offset_y in range(height):
            for offset_x in range(width):
                cells[(x + offset_x, y + offset_y)] = colors[(offset_x + offset_y) % 2]
    if "stairs" in rule:
        spec = rule["stairs"]
        x, y = _position(spec.get("start"), "Treppenstart")
        steps, size = spec.get("steps"), spec.get("size")
        if not all(isinstance(value, int) and value > 0 for value in (steps, size)):
            raise ValueError("Treppenstufen und Kantenlänge müssen positiv sein.")
        cells[(x, y)] = None
        for _ in range(steps):
            _line(cells, [x, y], [x + size, y])
            x += size
            _line(cells, [x, y], [x, y + size])
            y += size
    if not cells:
        raise ValueError("Eine Pixelprüfung benötigt cells, paths, checkerboard oder stairs.")
    return set(cells) if colorless else cells


def _apply_rule(builder: ExerciseBuilder, rule: dict) -> None:
    if not isinstance(rule, dict) or not isinstance(rule.get("type"), str):
        raise ValueError("Jeder Test benötigt einen type.")
    kind = rule["type"]
    if kind not in RULE_FIELDS:
        raise ValueError(f"Unbekannter sicherer Prüftyp: {kind!r}.")
    unknown = set(rule) - ({"type"} | FEEDBACK_KEYS | RULE_FIELDS[kind])
    if unknown:
        raise ValueError(
            f"Unbekannte Felder für Prüftyp {kind!r}: {', '.join(sorted(unknown))}."
        )
    feedback = _feedback(rule)
    if kind == "pixels":
        builder.expect_pixels(
            _expected_pixels(rule), exact=rule.get("exact", True), **feedback
        )
    elif kind == "no-extra-pixels":
        builder.expect_no_extra_pixels(_expected_pixels(rule), **feedback)
    elif kind == "pixel-count":
        count = rule.get("count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError("pixel-count.count muss eine nichtnegative ganze Zahl sein.")
        builder.expect_pixel_count(count, **feedback)
    elif kind == "square":
        builder.expect_square(_position(rule.get("start")), rule.get("side"))
    elif kind == "position":
        builder.expect_position(
            _position(rule.get("position")), pixel=rule.get("pixel", "KIM"), **feedback
        )
    elif kind == "positions":
        positions = rule.get("positions")
        if not isinstance(positions, dict):
            raise ValueError("positions muss Figuren auf [x, y] abbilden.")
        builder.expect_positions(
            {name: _position(value, name) for name, value in positions.items()}, **feedback
        )
    elif kind == "pixel-names":
        builder.expect_pixel_names(rule.get("names", []), **feedback)
    elif kind == "visibility":
        builder.expect_visibility(rule.get("pixel"), rule.get("visible"), **feedback)
    elif kind == "audio":
        events = rule.get("events")
        if not isinstance(events, list):
            raise ValueError("audio.events muss eine Liste sein.")
        builder.expect_audio([tuple(event) for event in events], **feedback)
    elif kind in RULE_METHODS:
        getattr(builder, RULE_METHODS[kind])(
            **({"kind": rule.get("kind")} if kind == "loop" else {}), **feedback
        )
    elif kind == "condition":
        builder.require_condition(calls=rule.get("calls", []), **feedback)
    elif kind == "function":
        builder.require_function(
            rule.get("name"),
            parameters=rule.get("parameters"),
            returns=rule.get("returns"),
            **feedback,
        )
    elif kind == "function-cases":
        cases = rule.get("cases")
        if not isinstance(cases, list) or not cases:
            raise ValueError("function-cases.cases muss eine nichtleere Liste sein.")
        for case in cases:
            if not isinstance(case, dict) or set(case) - {"args", "kwargs", "expected"}:
                raise ValueError("Jeder Funktionstest unterstützt args, kwargs und expected.")
            if not isinstance(case.get("args", []), list) or not isinstance(case.get("kwargs", {}), dict):
                raise ValueError("Funktionstest-Argumente sind ungültig.")
        builder.expect_function_cases(rule.get("name"), cases, **feedback)
    elif kind == "calls":
        builder.require_calls(*rule.get("names", []), **feedback)
    elif kind == "class":
        builder.require_class(rule.get("name"), base=rule.get("base"), **feedback)
    elif kind == "methods":
        builder.require_methods(rule.get("class"), *rule.get("names", []), **feedback)
    elif kind == "super-init":
        builder.require_super_init(rule.get("class"), **feedback)


def exercise_from_data(data: dict) -> Exercise:
    if not isinstance(data, dict):
        raise ValueError("Eine Aufgabe muss ein YAML-Objekt sein.")
    allowed = {"id", "title", "tests", "optimization"}
    unknown = set(data) - allowed
    if unknown:
        raise ValueError(f"Unbekannte Aufgabenfelder: {', '.join(sorted(unknown))}.")
    builder = ExerciseBuilder(data.get("id"), data.get("title"))
    tests = data.get("tests")
    if not isinstance(tests, list) or not tests:
        raise ValueError("Eine Aufgabe benötigt mindestens einen Test.")
    for rule in tests:
        _apply_rule(builder, rule)
    optimization = data.get("optimization")
    if optimization is not None:
        if not isinstance(optimization, dict) or set(optimization) != {"optimal_lines"}:
            raise ValueError("optimization unterstützt nur optimal_lines.")
        builder.optimize_lines(optimization["optimal_lines"])
    exercise = builder.build()
    digest = hashlib.sha256(
        json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return replace(exercise, definition_hash=digest)


def load_exercises(path: str | Path) -> dict[str, Exercise]:
    source = Path(path)
    documents = (
        [yaml.safe_load(item.read_text(encoding="utf-8")) for item in sorted(source.glob("*.yml"))]
        if source.is_dir()
        else [yaml.safe_load(source.read_text(encoding="utf-8"))]
    )
    definitions = []
    for data in documents:
        if not isinstance(data, dict) or data.get("format") != 1:
            raise ValueError(f"{source.name}: unbekanntes Trainingsformat.")
        if "exercises" in data:
            if not isinstance(data["exercises"], list):
                raise ValueError(f"{source.name}: exercises muss eine Liste sein.")
            definitions.extend(data["exercises"])
        else:
            definitions.append({key: value for key, value in data.items() if key != "format"})
    result = {}
    seen_names: set[str] = set()
    for definition in definitions:
        if isinstance(definition, dict) and definition.get("mode") == "answer":
            unknown = set(definition) - {"id", "title", "mode"}
            if unknown:
                raise ValueError(
                    "Unbekannte Felder für Antwortaufgabe: "
                    + ", ".join(sorted(unknown))
                )
            name = definition.get("id")
            title = definition.get("title")
            if not isinstance(name, str) or not re.fullmatch(
                r"[a-z0-9]+(?:-[a-z0-9]+)*", name
            ):
                raise ValueError("Die Kennung einer Antwortaufgabe muss kebab-case sein.")
            if not isinstance(title, str) or not title.strip():
                raise ValueError(f"Für die Antwortaufgabe {name!r} fehlt der Titel.")
            if name in seen_names:
                raise ValueError(f"Die Aufgabenkennung {name!r} ist doppelt.")
            seen_names.add(name)
            continue
        exercise = exercise_from_data(definition)
        if exercise.name in seen_names:
            raise ValueError(f"Die Aufgabenkennung {exercise.name!r} ist doppelt.")
        seen_names.add(exercise.name)
        audit = audit_exercise(exercise)
        errors = [issue.message for issue in audit.issues if issue.level == "error"]
        if errors:
            raise ValueError(f"Ungültige Aufgabe {exercise.name!r}: {' '.join(errors)}")
        result[exercise.name] = exercise
    return result


__all__ = ["exercise_from_data", "load_exercises"]
