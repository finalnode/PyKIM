"""Aufgabe: Eine C-Dur-Tonleiter spielen."""

from pykim.trainer import ExerciseBuilder

NOTES = ("C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5")

EXERCISE = (
    ExerciseBuilder("tonleiter-c-dur", "C-Dur-Tonleiter")
    .expect_audio(
        [(note, 1) for note in NOTES],
        success="Die C-Dur-Tonleiter enthält alle acht Töne in der richtigen Reihenfolge.",
        failure="Tonhöhen, Reihenfolge oder Tonlängen stimmen noch nicht.",
        hint="Spiele C4 bis C5 mit jeweils einem Beat.",
    )
    .require_loop(
        success="Du spielst die Tonleiter mithilfe einer Schleife.",
        failure="Die Tonleiter wurde noch ohne Schleife formuliert.",
        hint="Speichere die Notennamen in einer Liste und durchlaufe sie mit for.",
    )
    .optimize_lines(optimal=6)
    .build()
)
