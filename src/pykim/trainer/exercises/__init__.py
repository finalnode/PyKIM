"""Registry der sicher aus YAML geladenen PyKIM-Aufgaben."""

from pykim.trainer.definitions import load_exercises
from pykim.trainer.content import trainer_content_root
from pykim.trainer.models import Exercise


def _discover_exercises(content_root=None, trainers_path: str = "Trainer") -> dict[str, Exercise]:
    updated = (content_root or trainer_content_root()) / trainers_path
    # Ein bewusst trainerloser Kurs darf nicht auf die eingebauten PyKIM-
    # Aufgaben zurückfallen. Nur der tatsächlich aktive Inhaltsstand zählt.
    return load_exercises(updated) if updated.is_dir() else {}


_EXERCISES = _discover_exercises()


def refresh_exercises(content_root=None, trainers_path: str = "Trainer") -> tuple[str, ...]:
    """Lade die Trainerdefinitionen nach einer Inhaltssynchronisation neu."""
    global _EXERCISES
    _EXERCISES = _discover_exercises(content_root, trainers_path)
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
