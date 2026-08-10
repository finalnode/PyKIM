"""Registry aller lokal verfügbaren PyKIM-Aufgaben."""

from pykim.trainer.models import Exercise

from .square import EXERCISE as SQUARE
from .stairs import EXERCISE as STAIRS
from .multiple_pixels import EXERCISE as MULTIPLE_PIXELS


_EXERCISES = {
    exercise.name: exercise
    for exercise in (SQUARE, STAIRS, MULTIPLE_PIXELS)
}


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
