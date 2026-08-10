"""Aufgabe: Treppe mit fünf Stufen und einer Schleife."""

from pykim.trainer import ExerciseBuilder


def expected_pixels() -> set[tuple[int, int]]:
    x, y = 50, 50
    pixels = {(x, y)}
    for _ in range(5):
        pixels.update((x + distance, y) for distance in range(1, 6))
        x += 5
        pixels.update((x, y + distance) for distance in range(1, 6))
        y += 5
    return pixels


EXPECTED = expected_pixels()

EXERCISE = (
    ExerciseBuilder("treppe-5", "Treppe mit 5 Stufen")
    .expect_position(
        (75, 75),
        success="KIM steht am unteren Ende der Treppe.",
        failure="KIM steht noch nicht am unteren Ende der Treppe.",
        hint="Jede Stufe führt KIM 5 Pixel nach rechts und 5 Pixel nach unten.",
    )
    .expect_pixels(
        EXPECTED,
        exact=False,
        success="Alle 5 Stufen sind vollständig gezeichnet.",
        failure="Mindestens eine der 5 Stufen ist noch unvollständig.",
        hint="Wiederhole eine waagerechte und eine senkrechte Bewegung fünfmal.",
    )
    .expect_no_extra_pixels(
        EXPECTED,
        hint="Pro Wiederholung werden nur zwei Bewegungen benötigt.",
    )
    .expect_pixel_count(
        len(EXPECTED),
        success="Die Treppe besitzt genau die richtige Länge.",
        hint="Beginne die Farbspur am Startpunkt und lasse sie bis zum Ende an.",
    )
    .require_loop(
        success="Du verwendest eine Schleife und vermeidest Wiederholungen.",
        failure="Die Zeichnung stimmt vielleicht, aber dein Code lässt sich noch kürzen.",
        hint="Schreibe die zwei Bewegungen in eine for-Schleife mit range(5).",
    )
    .optimize_lines(optimal=8)
    .build()
)
