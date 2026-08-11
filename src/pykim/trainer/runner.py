"""Zentraler Einstiegspunkt für die Prüfung aus pykim.run()."""

import os

from .exercises import get_exercise
from .feedback import print_report
from .models import CheckReport


def _refresh_remote_trainers() -> None:
    """Prüfe vor der Bewertung die vom Kurszertifikat festgelegten Trainer."""
    try:
        from pykim.guide.course import get_course_directory
        from pykim.guide.updates import verify_certificate_trainers
        from pykim.submission.export import (
            course_certificate_info,
            verify_installed_course_certificate,
        )

        course = get_course_directory()
        if course is None:
            return
        certificate = course_certificate_info(course)
        if certificate is None or certificate.content is None:
            return
        certificate, authorization = verify_installed_course_certificate(
            course, allow_offline=True
        )
        if not authorization.checked_online:
            print("\nHinweis: Zertifikatsprüfung offline; verwende das zuletzt zugelassene Zertifikat.")
        result = verify_certificate_trainers(certificate.content)
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


def check_exercise(name: str, source: str) -> CheckReport:
    _refresh_remote_trainers()
    exercise = get_exercise(name)
    report = exercise.checker(source)
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
