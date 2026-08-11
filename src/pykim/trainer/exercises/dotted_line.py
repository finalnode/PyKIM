"""Aufgabe: Eine regelmäßige gepunktete Linie zeichnen."""

from pykim.trainer import ExerciseBuilder

EXPECTED = {(20 + 2 * index, 20): "purple" for index in range(8)}

EXERCISE = (
    ExerciseBuilder("punktlinie-8", "Punktlinie mit 8 Punkten")
    .expect_pixels(
        EXPECTED,
        success="Die acht violetten Punkte liegen exakt an den richtigen Stellen.",
        failure="Die Punktlinie enthält falsche, fehlende oder zusätzliche Pixel.",
        hint="Beginne bei (20, 20), male einen Pixel und gehe dann 2 Schritte weiter.",
    )
    .expect_position(
        (36, 20),
        success="KIM steht hinter dem letzten Punkt an der richtigen Endposition.",
        hint="Wiederhole auch nach dem achten Punkt die Bewegung um 2 Schritte.",
    )
    .require_loop(
        success="Du verwendest eine Schleife für die acht Wiederholungen.",
        failure="Die Punktlinie wurde noch ohne Schleife formuliert.",
        hint="Setze paint(), paint_stop() und right(2) in eine for-Schleife.",
    )
    .optimize_lines(optimal=10)
    .build()
)
