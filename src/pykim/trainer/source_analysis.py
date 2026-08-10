"""Kleine, fehlertolerante Analysen des Schülerprogramms."""

import ast


def uses_loop(source: str) -> bool:
    """Erkenne eine for- oder while-Schleife in gültigem Python-Quelltext."""
    if not source:
        return False
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    return any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree))


def uses_parallel(source: str) -> bool:
    """Erkenne einen with world.parallel():-Block im Schülerprogramm."""
    if not source:
        return False
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if not isinstance(node, (ast.With, ast.AsyncWith)):
            continue
        for item in node.items:
            expression = item.context_expr
            if (
                isinstance(expression, ast.Call)
                and isinstance(expression.func, ast.Attribute)
                and expression.func.attr == "parallel"
            ):
                return True
    return False
