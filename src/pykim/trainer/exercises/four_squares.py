"""Aufgabe: Vier benachbarte Quadrate mit einer Funktion zeichnen."""

from pykim.trainer import ExerciseBuilder


def expected_pixels() -> dict[tuple[int, int], str]:
    cells = {(x, y): "purple" for x in range(20, 41) for y in (20, 25)}
    cells.update({(x, y): "purple" for x in (20, 25, 30, 35, 40) for y in range(20, 26)})
    return cells


EXERCISE = (
    ExerciseBuilder("vier-quadrate", "Vier Quadrate in einer Reihe")
    .expect_pixels(
        expected_pixels(),
        success="Alle vier violetten Quadrate sind vollständig und korrekt verbunden.",
        failure="Die vier Quadrate stimmen noch nicht exakt mit der Vorlage überein.",
        hint="Jedes Quadrat hat die Kantenlänge 5 und beginnt am Ende des vorherigen.",
    )
    .expect_position(
        (40, 20),
        success="KIM steht am rechten oberen Ende der Quadratreihe.",
        hint="Gehe nach jedem Quadrat 5 Pixel zum Start des nächsten Quadrats.",
    )
    .require_function(
        success="Du hast das Zeichnen eines Quadrats in eine Funktion ausgelagert.",
        hint="Definiere beispielsweise def zeichne_quadrat():.",
    )
    .require_loop(
        success="Du wiederholst die vier Quadrate mit einer Schleife.",
        hint="Rufe deine Quadratfunktion in einer for-Schleife viermal auf.",
    )
    .optimize_lines(optimal=14)
    .build()
)
