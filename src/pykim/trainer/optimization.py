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


def _count_calls(tree: ast.AST, names: set[str]) -> int:
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _call_name(node) in names
    )


def evaluate_dotted_line(source: str) -> OptimizationResult:
    tree = _parse(source)
    if tree is None:
        return OptimizationResult(0, ("Der Quelltext konnte nicht analysiert werden.",))
    loop = any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree))
    calls = _count_calls(tree, {"paint", "right"})
    score = (6 if loop else 0) + (4 if 0 < calls <= 2 else 1 if calls else 0)
    tips = []
    if not loop:
        tips.append("Fasse die acht Wiederholungen in einer Schleife zusammen.")
    if calls > 2:
        tips.append("Notiere paint() und right(2) jeweils nur einmal.")
    return OptimizationResult(score, tuple(tips))


def evaluate_four_squares(source: str) -> OptimizationResult:
    tree = _parse(source)
    if tree is None:
        return OptimizationResult(0, ("Der Quelltext konnte nicht analysiert werden.",))
    function = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
    loop = any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree))
    movement_calls = _count_calls(tree, _MOVEMENTS)
    score = (4 if function else 0) + (4 if loop else 0)
    score += 2 if 0 < movement_calls <= 5 else 1 if movement_calls else 0
    tips = []
    if not function:
        tips.append("Lagere ein einzelnes Quadrat in eine Funktion aus.")
    if not loop:
        tips.append("Wiederhole die Quadratfunktion mit einer Schleife.")
    if movement_calls > 5:
        tips.append("Vermeide mehrfach ausgeschriebene Bewegungsbefehle.")
    return OptimizationResult(score, tuple(tips))


def evaluate_checkerboard(source: str) -> OptimizationResult:
    tree = _parse(source)
    if tree is None:
        return OptimizationResult(0, ("Der Quelltext konnte nicht analysiert werden.",))
    loops = (ast.For, ast.While)
    nested = any(
        isinstance(node, loops)
        and any(isinstance(child, loops) for child in ast.walk(node) if child is not node)
        for node in ast.walk(tree)
    )
    condition = any(isinstance(node, ast.If) for node in ast.walk(tree))
    function = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
    relevant_lines = [
        line for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    score = (4 if nested else 0) + (3 if condition else 0) + (2 if function else 0)
    score += 1 if len(relevant_lines) <= 20 else 0
    tips = []
    if not nested:
        tips.append("Nutze verschachtelte Schleifen für Zeilen und Spalten.")
    if not condition:
        tips.append("Wähle die Farbe mit einer if-Bedingung und modulo 2.")
    if not function:
        tips.append("Lagere das Zeichnen eines Feldes in eine Funktion aus.")
    if len(relevant_lines) > 20:
        tips.append("Versuche, mit höchstens 20 relevanten Codezeilen auszukommen.")
    return OptimizationResult(score, tuple(tips))
