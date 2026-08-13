"""Registry der sicher aus YAML geladenen PyKIM-Aufgaben."""

from pathlib import Path

from pykim.trainer.definitions import load_exercises
from pykim.trainer.models import Exercise


def _discover_exercises() -> dict[str, Exercise]:
    from pykim.guide.updates import active_content_root

    packaged_root = Path(__file__).resolve().parents[2] / "guide"
    updated = active_content_root(packaged_root) / "Trainer"
    # Ein bewusst trainerloser Kurs darf nicht auf die eingebauten PyKIM-
    # Aufgaben zurückfallen. Nur der tatsächlich aktive Inhaltsstand zählt.
    return load_exercises(updated) if updated.is_dir() else {}


_EXERCISES = _discover_exercises()


def refresh_exercises() -> tuple[str, ...]:
    """Lade die Trainerdefinitionen nach einer Inhaltssynchronisation neu."""
    global _EXERCISES
    _EXERCISES = _discover_exercises()
    return exercise_names()


def get_exercise(name: str) -> Exercise:
    """Liefere eine Aufgabe oder eine verständliche Fehlermeldung."""
    try:
        return _EXERCISES[name]
    except KeyError:
        available = " und ".join(repr(item) for item in sorted(_EXERCISES))
        raise ValueError(
            f"Die Aufgabe {name!r} gibt es nicht. Verfügbar sind: {available}."
        ) from None


def exercise_names() -> tuple[str, ...]:
    """Gib die registrierten Aufgabennamen sortiert zurück."""
    return tuple(sorted(_EXERCISES))
