"""Prüfung, Vorschau und Quellcodeentwürfe für Trainer-Autorinnen und -Autoren."""

import re
from dataclasses import dataclass

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
    "pixels": '.expect_pixels({(20, 20): "purple"})',
    "position": ".expect_position((20, 20))",
    "loop": ".require_loop()",
    "nested-loop": ".require_nested_loop()",
    "condition": ".require_condition()",
    "function": ".require_function()",
    "audio": '.expect_audio([("C4", 1), ("E4", 1)])',
    "parallel": ".require_parallel()",
    "class": '.require_class("MeinPixel", base="Pixel")',
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
    """Erzeuge einen direkt speicherbaren Builder-Entwurf aus UI-Bausteinen."""
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError("Die Kennung muss aus Kleinbuchstaben, Zahlen und Bindestrichen bestehen.")
    if not title.strip():
        raise ValueError("Bitte gib einen Titel an.")
    if not rules:
        raise ValueError("Wähle mindestens einen Prüfbaustein aus.")
    unknown = set(rules) - set(RULE_TEMPLATES)
    if unknown:
        raise ValueError(f"Unbekannte Prüfbausteine: {', '.join(sorted(unknown))}")
    lines = [
        '"""Aufgabe: ' + title.strip() + '."""',
        "",
        "from pykim.trainer import ExerciseBuilder",
        "",
        "EXERCISE = (",
        f'    ExerciseBuilder("{name}", {title.strip()!r})',
    ]
    lines.extend(f"    {RULE_TEMPLATES[rule]}" for rule in rules)
    if optimal_lines is not None:
        if optimal_lines < 1:
            raise ValueError("Die optimale Zeilenzahl muss mindestens 1 sein.")
        lines.append(f"    .optimize_lines(optimal={optimal_lines})")
    lines.extend(("    .build()", ")", ""))
    return "\n".join(lines)


__all__ = [
    "AuditIssue",
    "ExerciseAudit",
    "RULE_LABELS",
    "RULE_TEMPLATES",
    "audit_exercise",
    "generate_exercise_source",
]
