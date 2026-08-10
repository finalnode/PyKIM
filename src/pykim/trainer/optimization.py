"""Aufgabenspezifische Bewertung von Kontrollstrukturen und Codekürze."""

import ast

from .models import OptimizationResult

_MOVEMENTS = {"up", "down", "left", "right"}


def _parse(source: str) -> ast.AST | None:
    if not source:
        return None
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def evaluate_stairs(source: str) -> OptimizationResult:
    """Bewerte die Treppenlösung auf einer nachvollziehbaren 10er-Skala."""
    tree = _parse(source)
    if tree is None:
        return OptimizationResult(
            0,
            ("Der Quelltext konnte nicht auf Optimierung geprüft werden.",),
        )

    uses_loop = any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree))
    movement_calls = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _call_name(node) in _MOVEMENTS
    )

    # Sechs Punkte für die passende Kontrollstruktur. Bis zu vier weitere
    # Punkte gibt es für nur zwei verschieden notierte Bewegungsaufrufe.
    structure_score = 6 if uses_loop else 0
    length_score = (
        0
        if movement_calls == 0
        else min(4, max(1, round(8 / movement_calls)))
    )
    tips: list[str] = []
    if not uses_loop:
        tips.append("Nutze eine Schleife, statt dieselben Befehle zu wiederholen.")
    if movement_calls > 2:
        tips.append(
            "Schreibe right(5) und down(5) jeweils nur einmal in den Schleifenblock."
        )
    if movement_calls == 0:
        tips.append("In der Lösung wurden keine Bewegungsbefehle erkannt.")

    return OptimizationResult(structure_score + length_score, tuple(tips))
