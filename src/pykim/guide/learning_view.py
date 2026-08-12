"""Wiederverwendbare Lernstands-, Test- und Fehlerdarstellung der Suite."""

import re

from pykim.trainer.exercises import get_exercise
from pykim.trainer.activities import get_activity

from .library import task_names
from .progress import load_progress
from .components import empty_state, section_heading


def latest_attempts(progress: dict[str, object]) -> dict[str, dict[str, object]]:
    latest: dict[str, dict[str, object]] = {}
    attempts = progress.get("attempts", [])
    if isinstance(attempts, list):
        for attempt in attempts:
            if isinstance(attempt, dict) and isinstance(attempt.get("exercise"), str):
                latest[attempt["exercise"]] = attempt
    return latest


def render_test_results(ui, exercise_name: str) -> None:
    attempt = latest_attempts(load_progress()).get(exercise_name)
    if attempt is None:
        empty_state(
            ui,
            "Automatische Tests",
            "Noch kein Testlauf vorhanden. Starte dein Programm, um die "
            "einzelnen Prüffälle auszuführen.",
            icon="fact_check",
        )
        return

    tests = attempt.get("tests", [])
    passed_tests = int(attempt.get("passed", 0))
    total_tests = int(attempt.get("total", len(tests)))
    with ui.row().classes("w-full items-center gap-3 mt-3"):
        ui.label("Automatische Tests").classes("text-lg font-bold")
        ui.badge(
            f"{passed_tests} / {total_tests} bestanden",
            color="positive" if passed_tests == total_tests else "negative",
        )
    with ui.expansion("Testdetails anzeigen", icon="fact_check").classes(
        "w-full border rounded"
    ):
        for index, test in enumerate(tests, start=1):
            passed = bool(test["passed"])
            style = "pykim-test-passed" if passed else "pykim-test-failed"
            with ui.card().classes(f"w-full pykim-test-result {style}"):
                with ui.row().classes("w-full items-center"):
                    ui.icon(
                        "check_circle" if passed else "cancel",
                        color="positive" if passed else "negative",
                    )
                    ui.label(f"Testfall {index}").classes("font-bold")
                    ui.space()
                    ui.badge(
                        "BESTANDEN" if passed else "FEHLGESCHLAGEN",
                        color="positive" if passed else "negative",
                    )
                ui.label(test["message"]).classes("text-base")
                if test.get("hint"):
                    ui.label(f"Tipp: {test['hint']}").classes("w-full pykim-test-hint")


def render_overview(ui) -> None:
    progress = load_progress()
    latest = latest_attempts(progress)
    completed = sum(bool(item.get("successful")) for item in latest.values())
    section_heading(ui, "Mein Lernstand")
    ui.linear_progress(value=completed / max(1, len(task_names())))
    ui.label(f"{completed} von {len(task_names())} Aufgaben vollständig gelöst")
    with ui.grid(columns=2).classes("w-full gap-4"):
        for name in task_names():
            activity = get_activity(name)
            exercise = None if activity is not None and activity.mode == "matching" else get_exercise(name)
            attempt = latest.get(name)
            with ui.card().classes("w-full"):
                ui.label(activity.title if exercise is None else exercise.title).classes("font-bold")
                if attempt is None:
                    ui.label("Noch nicht begonnen").classes("text-grey")
                else:
                    ui.label(f"Tests: {attempt['passed']}/{attempt['total']}")
                    optimization = attempt.get("optimization")
                    if isinstance(optimization, dict):
                        ui.label(f"Optimierung: {optimization['score']} %")


def friendly_python_error(stderr: str) -> tuple[int | None, str]:
    matches = re.findall(r'File "[^"]+", line (\d+)', stderr)
    line = int(matches[-1]) if matches else None
    last = next(
        (item.strip() for item in reversed(stderr.splitlines()) if item.strip()), ""
    )
    translations = {
        "SyntaxError": "Syntaxfehler",
        "IndentationError": "Einrückungsfehler",
        "NameError": "Unbekannter Name",
        "TypeError": "Falscher Datentyp oder Funktionsaufruf",
        "IndexError": "Ungültiger Listenindex",
    }
    for technical, german in translations.items():
        if technical in last:
            return line, f"{german}: {last.partition(':')[2].strip()}"
    return line, last or "Das Programm wurde mit einem Fehler beendet."


__all__ = ["friendly_python_error", "latest_attempts", "render_overview", "render_test_results"]
