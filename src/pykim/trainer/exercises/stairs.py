"""Aufgabe: Treppe mit fünf Stufen und einer Schleife."""

import pykim
from pykim.testing import get_painted_pixels
from pykim.trainer.models import CheckReport, CheckResult, Exercise
from pykim.trainer.optimization import evaluate_stairs
from pykim.trainer.source_analysis import uses_loop


NAME = "treppe-5"
TITLE = "Treppe mit 5 Stufen"
START = (50, 50)
STEPS = 5
SIZE = 5


def expected_pixels() -> set[tuple[int, int]]:
    x, y = START
    pixels = {(x, y)}
    for _ in range(STEPS):
        for distance in range(1, SIZE + 1):
            pixels.add((x + distance, y))
        x += SIZE
        for distance in range(1, SIZE + 1):
            pixels.add((x, y + distance))
        y += SIZE
    return pixels


def check(source: str) -> CheckReport:
    pixels = get_painted_pixels()
    expected = expected_pixels()
    expected_end = (START[0] + STEPS * SIZE, START[1] + STEPS * SIZE)

    results = (
        CheckResult(
            (pykim.kim.get_x(), pykim.kim.get_y()) == expected_end,
            "KIM steht am unteren Ende der Treppe.",
            "KIM steht noch nicht am unteren Ende der Treppe.",
            "Jede Stufe führt KIM 5 Pixel nach rechts und 5 Pixel nach unten.",
        ),
        CheckResult(
            expected <= pixels,
            "Alle 5 Stufen sind vollständig gezeichnet.",
            "Mindestens eine der 5 Stufen ist noch unvollständig.",
            "Wiederhole eine waagerechte und eine senkrechte Bewegung fünfmal.",
        ),
        CheckResult(
            bool(pixels) and pixels <= expected,
            "Es wurden keine zusätzlichen Pixel angemalt.",
            "Es wurden Pixel außerhalb der Treppe angemalt.",
            "Pro Wiederholung werden nur zwei Bewegungen benötigt.",
        ),
        CheckResult(
            len(pixels) == len(expected),
            "Die Treppe besitzt genau die richtige Länge.",
            f"Die Treppe benötigt {len(expected)} angemalte Pixel; du hast "
            f"{len(pixels)} angemalt.",
            "Beginne die Farbspur am Startpunkt und lasse sie bis zum Ende an.",
        ),
        CheckResult(
            uses_loop(source),
            "Du verwendest eine Schleife und vermeidest Wiederholungen.",
            "Die Zeichnung stimmt vielleicht, aber dein Code lässt sich noch kürzen.",
            "Schreibe die zwei Bewegungen in eine for-Schleife mit range(5).",
        ),
    )
    return CheckReport(TITLE, results, evaluate_stairs(source))


EXERCISE = Exercise(NAME, TITLE, check)
