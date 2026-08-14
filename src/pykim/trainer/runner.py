"""Zentraler Einstiegspunkt für die Prüfung aus pykim.run()."""

import os

from .exercises import get_exercise
from .feedback import print_report
from .models import CheckReport
from .progress import record_attempt


def check_exercise(
    name: str,
    source: str,
    namespace: dict[str, object] | None = None,
) -> CheckReport:
    exercise = get_exercise(name)
    report = exercise.checker(source, namespace)
    print_report(report)
    if os.environ.get("PYKIM_PROGRESS_MODE") == "disabled":
        return report
    try:
        record_attempt(name, report, source)
    except OSError as error:
        # Ein nicht erreichbares Netzlaufwerk darf die eigentliche Aufgabe
        # nicht unbenutzbar machen.
        print(f"\nHinweis: Der Lernfortschritt konnte nicht gespeichert werden: {error}")
    return report
