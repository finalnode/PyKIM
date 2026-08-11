"""Kompatible Aufgaben-API, erzeugt aus den Markdown-Quelldateien."""

from pykim.guide.library import TaskAssignment as Assignment
from pykim.guide.library import task_assignment, task_names


ASSIGNMENTS = {name: task_assignment(name) for name in task_names()}


def get_assignment(name: str) -> Assignment:
    try:
        return ASSIGNMENTS[name]
    except KeyError:
        raise ValueError(f"Für {name!r} fehlt die Aufgabenstellung.") from None
