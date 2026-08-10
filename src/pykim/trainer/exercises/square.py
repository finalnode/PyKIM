"""Aufgabe: Quadrat mit Kantenlänge 5."""

from pykim.trainer import ExerciseBuilder

EXERCISE = (
    ExerciseBuilder("quadrat-5", "Quadrat mit Kantenlänge 5")
    .expect_square(start=(50, 50), side=5)
    .optimize_lines(optimal=10)
    .build()
)
