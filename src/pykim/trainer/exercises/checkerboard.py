"""Aufgabe: Ein zweifarbiges 8-mal-8-Schachbrett zeichnen."""

from pykim.trainer import ExerciseBuilder

EXPECTED = {
    (20 + x, 20 + y): "purple" if (x + y) % 2 == 0 else "orange"
    for y in range(8)
    for x in range(8)
}

EXERCISE = (
    ExerciseBuilder("schachbrett-8", "Zweifarbiges 8-mal-8-Schachbrett")
    .expect_pixels(
        EXPECTED,
        success="Alle 64 Schachbrettfelder besitzen Position und Farbe der Vorlage.",
        failure="Felder, Farben oder Größe des Schachbretts stimmen noch nicht.",
        hint="Nutze purple für gerade und orange für ungerade Koordinatensummen.",
    )
    .require_nested_loop(
        success="Du durchläufst Zeilen und Spalten mit verschachtelten Schleifen.",
        hint="Verwende eine Schleife für y und darin eine zweite für x.",
    )
    .require_condition(
        success="Eine Bedingung wählt die Farbe jedes Feldes aus.",
        hint="Prüfe mit modulo 2, ob x + y gerade oder ungerade ist.",
    )
    .require_function(
        success="Das Zeichnen eines Feldes ist in einer Funktion gekapselt.",
        hint="Definiere eine Funktion mit x, y und color als Parametern.",
    )
    .optimize_lines(optimal=15)
    .build()
)
