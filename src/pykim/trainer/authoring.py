"""Prüfung, Vorschau und Quellcodeentwürfe für Trainer-Autorinnen und -Autoren."""

import re
from dataclasses import dataclass

import yaml

from .models import Exercise

RULE_LABELS = {
    "pixels": "Zeichnung und Farben",
    "position": "Endposition",
    "positions": "Endpositionen mehrerer Pixel",
    "pixel-names": "Figuren in der Welt",
    "visibility": "Sichtbarkeit",
    "audio": "Töne und Tonlängen",
    "loop": "Schleife verwendet",
    "nested-loop": "Verschachtelte Schleifen",
    "condition": "Bedingung verwendet",
    "function": "Eigene Funktion",
    "calls": "Funktionsaufrufe",
    "parallel": "Parallele Ausführung",
    "class": "Eigene Klasse",
    "methods": "Klassenmethoden",
    "super-init": "Basiskonstruktor",
    "pixel-count": "Anzahl gezeichneter Pixel",
    "no-extra-pixels": "Keine zusätzlichen Pixel",
    "dynamic": "Dynamische Fachprüfung",
    "custom": "Eigene Sonderprüfung",
}

RULE_TEMPLATES = {
    "pixels": {"type": "pixels", "cells": [[20, 20, "purple"]]},
    "position": {"type": "position", "position": [20, 20]},
    "loop": {"type": "loop"},
    "nested-loop": {"type": "nested-loop"},
    "condition": {"type": "condition"},
    "function": {"type": "function"},
    "audio": {"type": "audio", "events": [["C4", 1], ["E4", 1]]},
    "parallel": {"type": "parallel"},
    "class": {"type": "class", "name": "MeinPixel", "base": "Pixel"},
}


@dataclass(frozen=True)
class AuditIssue:
    level: str
    message: str


@dataclass(frozen=True)
class ExerciseAudit:
    exercise: Exercise
    issues: tuple[AuditIssue, ...]

    @property
    def valid(self) -> bool:
        return not any(issue.level == "error" for issue in self.issues)


def audit_exercise(exercise: Exercise) -> ExerciseAudit:
    """Finde technische Fehler und redaktionelle Schwächen einer Aufgabe."""
    issues: list[AuditIssue] = []
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", exercise.name):
        issues.append(AuditIssue("error", "Die Kennung muss ein kebab-case-Name sein."))
    if not exercise.title.strip():
        issues.append(AuditIssue("error", "Der sichtbare Titel fehlt."))
    if not exercise.rules:
        issues.append(AuditIssue("error", "Die Aufgabe besitzt keine Prüfbausteine."))
    if not exercise.definition_hash:
        issues.append(AuditIssue("error", "Der stabile Definitions-Hash fehlt."))
    for index, rule in enumerate(exercise.rules, start=1):
        if not rule.success.strip() or not rule.failure.strip():
            issues.append(
                AuditIssue("error", f"Prüfbaustein {index} hat unvollständiges Feedback.")
            )
        if not rule.hint.strip():
            issues.append(
                AuditIssue("warning", f"Prüfbaustein {index} hat noch keinen Tipp.")
            )
    return ExerciseAudit(exercise, tuple(issues))


def generate_exercise_source(
    name: str,
    title: str,
    rules: tuple[str, ...] | list[str],
    *,
    optimal_lines: int | None = None,
) -> str:
    """Erzeuge eine sichere YAML-Trainingsdefinition aus UI-Bausteinen."""
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError("Die Kennung muss aus Kleinbuchstaben, Zahlen und Bindestrichen bestehen.")
    if not title.strip():
        raise ValueError("Bitte gib einen Titel an.")
    if not rules:
        raise ValueError("Wähle mindestens einen Prüfbaustein aus.")
    unknown = set(rules) - set(RULE_TEMPLATES)
    if unknown:
        raise ValueError(f"Unbekannte Prüfbausteine: {', '.join(sorted(unknown))}")
    definition = {
        "format": 1,
        "exercises": [{
            "id": name,
            "title": title.strip(),
            "tests": [dict(RULE_TEMPLATES[rule]) for rule in rules],
        }],
    }
    if optimal_lines is not None:
        if optimal_lines < 1:
            raise ValueError("Die optimale Zeilenzahl muss mindestens 1 sein.")
        definition["exercises"][0]["optimization"] = {"optimal_lines": optimal_lines}
    return yaml.safe_dump(definition, allow_unicode=True, sort_keys=False)


__all__ = [
    "AuditIssue",
    "ExerciseAudit",
    "RULE_LABELS",
    "RULE_TEMPLATES",
    "audit_exercise",
    "generate_exercise_source",
]
