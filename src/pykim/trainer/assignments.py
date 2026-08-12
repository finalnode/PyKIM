"""Kompatible Aufgaben-API, erzeugt aus den Markdown-Quelldateien."""

from pykim.guide.library import TaskAssignment as Assignment
from pykim.guide.library import task_assignment
from pykim.trainer.exercises import exercise_names


ASSIGNMENTS = {name: task_assignment(name) for name in exercise_names()}


def refresh_assignments() -> tuple[str, ...]:
    """Lade Aufgabenmetadaten nach einer Inhaltssynchronisation neu."""
    global ASSIGNMENTS
    ASSIGNMENTS = {name: task_assignment(name) for name in exercise_names()}
    return tuple(sorted(ASSIGNMENTS))


def get_assignment(name: str) -> Assignment:
    try:
        return ASSIGNMENTS[name]
    except KeyError:
        raise ValueError(f"Für {name!r} fehlt die Aufgabenstellung.") from None
