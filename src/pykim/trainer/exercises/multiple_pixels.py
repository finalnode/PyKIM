"""Aufgabe: Drei Pixel sequenziell und parallel bewegen."""

from pykim.trainer import ExerciseBuilder


def paint_line(cells, start, end, color):
    """Erzeuge die fachliche Vorlage einer geraden Linie."""
    x1, y1 = start
    x2, y2 = end
    dx = 0 if x1 == x2 else (1 if x2 > x1 else -1)
    dy = 0 if y1 == y2 else (1 if y2 > y1 else -1)
    for distance in range(max(abs(x2 - x1), abs(y2 - y1)) + 1):
        cells[(x1 + dx * distance, y1 + dy * distance)] = color


def expected_pixels():
    cells = {}
    for start, end, color in (
        ((20, 20), (35, 20), "purple"),
        ((60, 20), (45, 20), "orange"),
        ((40, 60), (40, 40), "cyan"),
        ((35, 20), (35, 30), "purple"),
        ((45, 20), (45, 40), "orange"),
        ((40, 40), (50, 40), "cyan"),
        ((35, 30), (50, 30), "purple"),
        ((45, 40), (30, 40), "orange"),
        ((50, 40), (50, 25), "cyan"),
    ):
        paint_line(cells, start, end, color)
    return cells


EXERCISE = (
    ExerciseBuilder("mehrere-pixel", "Drei Pixel gemeinsam bewegen")
    .expect_pixel_names(
        ("KIM", "MIA", "LEO"),
        success="Die Welt enthält genau KIM, MIA und LEO.",
        failure="Die Welt enthält noch nicht genau die drei geforderten Pixel.",
        hint="Erzeuge MIA und LEO mit world.new_pixel(...).",
    )
    .expect_positions(
        {"KIM": (50, 30), "MIA": (30, 40), "LEO": (50, 25)},
        success="Alle drei Pixel stehen an ihrer richtigen Endposition.",
        hint="Prüfe die parallelen und die sequenziellen Bewegungen getrennt.",
    )
    .expect_pixels(
        expected_pixels(),
        success="Alle farbigen Linien stimmen exakt mit der Vorlage überein.",
        failure="Die gezeichneten Pixel oder ihre Farben weichen von der Vorlage ab.",
        hint="KIM zeichnet purple, MIA orange und LEO cyan.",
    )
    .expect_visibility(
        "LEO", False,
        success="LEO ist am Ende versteckt und seine Spur bleibt sichtbar.",
        failure="LEO ist am Ende noch sichtbar.",
        hint="Rufe leo.hide() erst nach den Bewegungen auf.",
    )
    .require_parallel(
        success="Du verwendest mindestens einen world.parallel()-Block.",
        failure="Die Bewegungen werden noch nicht parallel ausgeführt.",
        hint="Setze gleichzeitige Bewegungen in with world.parallel():.",
    )
    .optimize_lines(optimal=22)
    .build()
)
