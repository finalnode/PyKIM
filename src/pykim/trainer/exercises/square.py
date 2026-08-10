"""Aufgabe: Quadrat mit Kantenlänge 5."""

import pykim
from pykim.testing import get_painted_pixels
from pykim.trainer.models import CheckReport, CheckResult, Exercise


NAME = "quadrat-5"
TITLE = "Quadrat mit Kantenlänge 5"
START = (50, 50)
SIDE = 5


def check(_source: str) -> CheckReport:
    pixels = get_painted_pixels()
    current_position = (pykim.kim.get_x(), pykim.kim.get_y())

    if pixels:
        xs = [x for x, _ in pixels]
        ys = [y for _, y in pixels]
        left, right = min(xs), max(xs)
        top, bottom = min(ys), max(ys)
        width, height = right - left, bottom - top
        expected_outline = {
            (x, y)
            for x in range(left, right + 1)
            for y in range(top, bottom + 1)
            if x in (left, right) or y in (top, bottom)
        }
        start_is_corner = START in {
            (left, top),
            (right, top),
            (left, bottom),
            (right, bottom),
        }
    else:
        width = height = 0
        expected_outline: set[tuple[int, int]] = set()
        start_is_corner = False

    results = (
        CheckResult(
            current_position == START and start_is_corner,
            "KIM hat bei (50, 50) gezeichnet und ist dorthin zurückgekehrt.",
            "Start oder Ende des Quadrats liegt nicht bei (50, 50).",
            "Setze KIM zuerst mit set_x(50) und set_y(50) an den Startpunkt.",
        ),
        CheckResult(
            width == SIDE,
            "Das Quadrat ist 5 Pixel breit.",
            f"Die Zeichnung ist momentan {width} Pixel breit.",
            "Eine waagerechte Seite soll genau 5 Schritte lang sein.",
        ),
        CheckResult(
            height == SIDE,
            "Das Quadrat ist 5 Pixel hoch.",
            f"Die Zeichnung ist momentan {height} Pixel hoch.",
            "Eine senkrechte Seite soll genau 5 Schritte lang sein.",
        ),
        CheckResult(
            bool(pixels) and expected_outline <= pixels,
            "Alle vier Seiten sind vollständig.",
            "Mindestens eine Seite ist noch nicht vollständig.",
            "Beginne die Farbspur vor der ersten Bewegung und zeichne vier Seiten.",
        ),
        CheckResult(
            bool(pixels) and pixels <= expected_outline,
            "Es wurden keine zusätzlichen Pixel angemalt.",
            "Es wurden Pixel innerhalb oder außerhalb des Quadratrands angemalt.",
            "Beende die Farbspur, bevor du nach dem Quadrat weitergehst.",
        ),
    )
    return CheckReport(TITLE, results)


EXERCISE = Exercise(NAME, TITLE, check)
