"""Aufgabe: Eine eigene Pixel-Unterklasse entwickeln."""

from pykim.trainer import ExerciseBuilder

EXERCISE = (
    ExerciseBuilder("musik-pixel-klasse", "Eigene MusikPixel-Klasse")
    .require_class(
        "MusikPixel",
        base="Pixel",
        success="MusikPixel erbt von der PyKIM-Klasse Pixel.",
        failure="Die Klasse MusikPixel mit Pixel als Basisklasse fehlt noch.",
        hint="Beginne mit class MusikPixel(Pixel):.",
    )
    .require_super_init(
        "MusikPixel",
        success="Der Konstruktor erweitert den geerbten Pixelzustand.",
    )
    .require_methods(
        "MusikPixel", "update", "draw",
        success="MusikPixel überschreibt update() und draw() mit eigenem Verhalten.",
        failure="Die Klasse überschreibt update() und draw() noch nicht vollständig.",
    )
    .require_calls(
        "spawn",
        success="Du erzeugst deine Unterklasse mit world.spawn().",
        failure="Es wurde noch keine MusikPixel-Instanz mit world.spawn() erzeugt.",
        hint="Nutze world.spawn(MusikPixel, 'MIA', ...).",
    )
    .optimize_lines(optimal=22)
    .build()
)
