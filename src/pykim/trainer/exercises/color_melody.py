"""Aufgabe: Farbige Felder lesen und in Töne übersetzen."""

from pykim.trainer import ExerciseBuilder

COLORS = ("red", "green", "cyan", "yellow")
NOTES = (("C4", 1), ("E4", 1), ("G4", 1), ("C5", 2))

EXERCISE = (
    ExerciseBuilder("farben-melodie", "Melodie aus Farben")
    .expect_pixels(
        {(20 + index, 20): color for index, color in enumerate(COLORS)},
        success="Die vier Farbfelder liegen in der richtigen Reihenfolge.",
        failure="Positionen, Farben oder zusätzliche Pixel stimmen noch nicht.",
        hint="Male bei y=20 ab x=20 red, green, cyan und yellow.",
    )
    .expect_audio(
        NOTES,
        success="Jede Farbe erzeugt den vorgesehenen Ton.",
        failure="Die Farbmelodie besitzt noch falsche Töne oder Tonlängen.",
        hint="red=C4, green=E4, cyan=G4 und yellow=C5 mit zwei Beats.",
    )
    .require_loop(
        success="Eine Schleife besucht alle vier Farbfelder.",
        hint="Gehe viermal über das aktuelle Feld und danach einen Schritt nach rechts.",
    )
    .require_condition(
        calls=("get_color",),
        success="Du liest die Farbe und wählst den Ton mit einer Bedingung.",
        failure="Farbabfrage und if-Bedingung sind noch nicht vollständig erkennbar.",
        hint="Speichere get_color() und vergleiche die Farbe mit if/elif.",
    )
    .optimize_lines(optimal=21)
    .build()
)
