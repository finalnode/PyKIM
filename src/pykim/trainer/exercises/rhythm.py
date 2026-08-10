"""Aufgabe: Ein Motiv mit unterschiedlichen Längen wiederholen."""

from pykim.trainer import ExerciseBuilder

MOTIF = [("C4", 1), ("E4", 1), ("G4", 2), (None, 1)]

EXERCISE = (
    ExerciseBuilder("rhythmus-motiv", "Rhythmisches Tonmotiv")
    .expect_audio(
        MOTIF * 2,
        success="Das Motiv wird zweimal mit den richtigen Ton- und Pausenlängen gespielt.",
        failure="Das Motiv oder seine Wiederholung stimmt noch nicht vollständig.",
        hint="Spiele C4 (1), E4 (1), G4 (2), Pause (1) zweimal.",
    )
    .require_function(
        success="Das Motiv ist in einer eigenen Funktion gekapselt.",
        hint="Definiere beispielsweise def spiele_motiv():.",
    )
    .require_loop(
        success="Eine Schleife übernimmt die Wiederholung.",
        hint="Rufe die Motivfunktion in einer for-Schleife zweimal auf.",
    )
    .optimize_lines(optimal=10)
    .build()
)
