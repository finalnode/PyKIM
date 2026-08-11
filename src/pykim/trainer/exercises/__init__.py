"""Registry aller mitgelieferten und lokal ergänzten PyKIM-Aufgaben."""

from importlib import import_module
from pkgutil import iter_modules

from pykim.trainer.models import Exercise
from pykim.trainer.authoring import audit_exercise


# PyInstaller-Archive besitzen keinen normal durchsuchbaren Paketordner. Die
# mitgelieferten Aufgaben müssen daher ausdrücklich bekannt sein. Im
# Entwicklungsbetrieb ergänzt ``iter_modules`` weiterhin neue Autorendateien
# automatisch.
BUILTIN_MODULES = (
    "checkerboard",
    "color_melody",
    "custom_pixel",
    "dotted_line",
    "four_squares",
    "interactive",
    "multiple_pixels",
    "rhythm",
    "scale",
    "square",
    "stairs",
)


def _discover_exercises() -> dict[str, Exercise]:
    exercises: dict[str, Exercise] = {}
    package = __name__
    discovered = {
        module_info.name
        for module_info in iter_modules(__path__)
        if not module_info.name.startswith("_")
    }
    for module_name in sorted(set(BUILTIN_MODULES) | discovered):
        module = import_module(f"{package}.{module_name}")
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
        audit = audit_exercise(exercise)
        errors = [issue.message for issue in audit.issues if issue.level == "error"]
        if errors:
            raise ValueError(f"Ungültige Aufgabe {exercise.name!r}: {' '.join(errors)}")
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
