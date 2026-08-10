"""Aufgabe: KIM mit Tasten in einer Spielschleife steuern."""

from pykim.trainer import ExerciseBuilder

EXERCISE = (
    ExerciseBuilder("interaktive-steuerung", "Interaktive Steuerung")
    .require_function(
        "update",
        success="Dein Programm besitzt eine update()-Funktion für die Spiellogik.",
        failure="Eine update()-Funktion wurde noch nicht erkannt.",
        hint="Definiere def update(): und frage dort die Tasten ab.",
    )
    .require_function(
        "draw",
        success="Dein Programm trennt die Darstellung in eine draw()-Funktion.",
        failure="Eine draw()-Funktion wurde noch nicht erkannt.",
        hint="Definiere def draw(): und zeichne dort Welt und KIM.",
    )
    .require_calls(
        "btn",
        success="Die Bewegung reagiert auf world.btn().",
        failure="Es wurde noch keine dauerhafte Tastenabfrage erkannt.",
        hint="Nutze beispielsweise if world.btn('right'):.",
    )
    .require_calls(
        "cls", "run",
        success="Die Anzeige wird geleert und die Spielschleife gestartet.",
        failure="world.cls() oder world.run(...) fehlt noch.",
        hint="Leere in draw() die Anzeige und übergib update und draw an world.run.",
    )
    .optimize_lines(optimal=17)
    .build()
)
