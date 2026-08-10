"""Aufgabe: Drei Pixel sequenziell und parallel bewegen."""

import pykim
from pykim.trainer.models import CheckReport, CheckResult, Exercise
from pykim.trainer.source_analysis import uses_parallel


NAME = "mehrere-pixel"
TITLE = "Drei Pixel gemeinsam bewegen"


def _paint_line(
    cells: dict[tuple[int, int], int],
    start: tuple[int, int],
    end: tuple[int, int],
    color: int,
) -> None:
    x1, y1 = start
    x2, y2 = end
    dx = 0 if x1 == x2 else (1 if x2 > x1 else -1)
    dy = 0 if y1 == y2 else (1 if y2 > y1 else -1)
    length = max(abs(x2 - x1), abs(y2 - y1))
    for distance in range(length + 1):
        cells[(x1 + dx * distance, y1 + dy * distance)] = color


def _expected_cells() -> dict[tuple[int, int], int]:
    """Baue das erwartete Farbbild in derselben Befehlsreihenfolge auf."""
    cells: dict[tuple[int, int], int] = {}

    # Startpixel und erster paralleler Block.
    _paint_line(cells, (20, 20), (35, 20), 2)
    _paint_line(cells, (60, 20), (45, 20), 9)
    _paint_line(cells, (40, 60), (40, 40), 12)

    # Sequenzieller Mittelteil.
    _paint_line(cells, (35, 20), (35, 30), 2)
    _paint_line(cells, (45, 20), (45, 40), 9)
    _paint_line(cells, (40, 40), (50, 40), 12)

    # Zweiter paralleler Block; bei Kreuzungen zählt die Schreibreihenfolge.
    _paint_line(cells, (35, 30), (50, 30), 2)
    _paint_line(cells, (45, 40), (30, 40), 9)
    _paint_line(cells, (50, 40), (50, 25), 12)
    return cells


def _painted_cells() -> dict[tuple[int, int], int]:
    return {
        (x, y): color
        for y, row in enumerate(pykim.world.cells)
        for x, color in enumerate(row)
        if color != 0
    }


def check(source: str) -> CheckReport:
    pixels = {pixel.name: pixel for pixel in pykim.world.pixels}
    expected_positions = {
        "KIM": (50, 30),
        "MIA": (30, 40),
        "LEO": (50, 25),
    }
    positions_correct = all(
        name in pixels
        and (pixels[name].get_x(), pixels[name].get_y()) == position
        for name, position in expected_positions.items()
    )
    leo_hidden = "LEO" in pixels and not pixels["LEO"].visible

    results = (
        CheckResult(
            set(pixels) == {"KIM", "MIA", "LEO"},
            "Die Welt enthält genau KIM, MIA und LEO.",
            "Die Welt enthält noch nicht genau die drei geforderten Pixel.",
            "Erzeuge MIA und LEO mit world.new_pixel(...).",
        ),
        CheckResult(
            positions_correct,
            "Alle drei Pixel stehen an ihrer richtigen Endposition.",
            "Mindestens ein Pixel steht noch an der falschen Endposition.",
            "Prüfe die parallelen und die sequenziellen Bewegungen getrennt.",
        ),
        CheckResult(
            _painted_cells() == _expected_cells(),
            "Alle farbigen Linien stimmen exakt mit der Vorlage überein.",
            "Die gezeichneten Pixel oder ihre Farben weichen von der Vorlage ab.",
            "KIM zeichnet purple, MIA orange und LEO cyan.",
        ),
        CheckResult(
            leo_hidden,
            "LEO ist am Ende versteckt und seine Spur bleibt sichtbar.",
            "LEO ist am Ende noch sichtbar.",
            "Rufe leo.hide() erst nach den Bewegungen auf.",
        ),
        CheckResult(
            uses_parallel(source),
            "Du verwendest mindestens einen world.parallel()-Block.",
            "Die Bewegungen werden noch nicht parallel ausgeführt.",
            "Setze gleichzeitige Bewegungen in with world.parallel():.",
        ),
    )
    return CheckReport(TITLE, results)


EXERCISE = Exercise(NAME, TITLE, check)
