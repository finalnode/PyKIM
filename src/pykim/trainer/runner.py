"""Zentraler Einstiegspunkt für die Prüfung aus pykim.run()."""

import os

from .exercises import get_exercise
from .feedback import print_report
from .models import CheckReport


def _refresh_remote_trainers() -> None:
    """Prüfe vor der Bewertung die von der Kurs-Setupdatei festgelegten Trainer."""
    try:
        from pykim.guide.course import get_course_directory
        from pykim.guide.updates import verify_certificate_trainers
        from pykim.guide.course_setup import (
            course_setup_info,
            verify_installed_course_setup,
        )

        course = get_course_directory()
        if course is None:
            return
        setup = course_setup_info(course)
        if setup is None:
            return
        setup, _authorization = verify_installed_course_setup(
            course, allow_offline=True
        )
        result = verify_certificate_trainers(setup)
        if not result.checked_online:
            print("\nHinweis: Repository nicht erreichbar; verwende zuletzt geprüfte Trainerdaten.")
        elif result.updated:
            from .exercises import refresh_exercises

            refresh_exercises()
            print("\nHinweis: Trainerdaten wurden mit dem Kurs-Repository synchronisiert.")
    except OSError as error:
        # Ein vorübergehend nicht erreichbares Netz darf Offline-Unterricht
        # nicht verhindern. Strukturelle und kryptografische Fehler werden
        # absichtlich nicht abgefangen.
        print(f"\nHinweis: Repository nicht erreichbar; verwende zuletzt geprüfte Trainerdaten: {error}")


def check_exercise(
    name: str,
    source: str,
    namespace: dict[str, object] | None = None,
) -> CheckReport:
    _refresh_remote_trainers()
    exercise = get_exercise(name)
    report = exercise.checker(source, namespace)
    print_report(report)
    if os.environ.get("PYKIM_PROGRESS_MODE") == "disabled":
        return report
    try:
        from pykim.guide.progress import record_attempt

        record_attempt(name, report, source)
    except OSError as error:
        # Ein nicht erreichbares Netzlaufwerk darf die eigentliche Aufgabe
        # nicht unbenutzbar machen.
        print(f"\nHinweis: Der Lernfortschritt konnte nicht gespeichert werden: {error}")
    return report
