"""Automatische Registry aller lokalen PyKIM-Aufgaben."""

from importlib import import_module
from pkgutil import iter_modules

from pykim.trainer.models import Exercise


def _discover_exercises() -> dict[str, Exercise]:
    exercises: dict[str, Exercise] = {}
    package = __name__
    for module_info in iter_modules(__path__):
        if module_info.name.startswith("_"):
            continue
        module = import_module(f"{package}.{module_info.name}")
        exercise = getattr(module, "EXERCISE", None)
        if exercise is None:
            continue
        if not isinstance(exercise, Exercise):
            raise TypeError(
                f"{module.__name__}.EXERCISE muss mit ExerciseBuilder.build() "
                "erzeugt werden."
            )
        if exercise.name in exercises:
            raise ValueError(f"Die Aufgabenkennung {exercise.name!r} ist doppelt.")
        exercises[exercise.name] = exercise
    return exercises


_EXERCISES = _discover_exercises()


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
