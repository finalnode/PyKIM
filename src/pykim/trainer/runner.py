"""Zentraler Einstiegspunkt für die Prüfung aus pykim.run()."""

from .exercises import get_exercise
from .feedback import print_report
from .models import CheckReport


def check_exercise(name: str, source: str) -> CheckReport:
    exercise = get_exercise(name)
    report = exercise.checker(source)
    print_report(report)
    return report
