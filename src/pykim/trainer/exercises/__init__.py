"""Registry der sicher aus YAML geladenen PyKIM-Aufgaben."""

from pathlib import Path

from pykim.trainer.definitions import load_exercises
from pykim.trainer.models import Exercise


def _discover_exercises() -> dict[str, Exercise]:
    from pykim.guide.updates import active_content_root

    packaged_root = Path(__file__).resolve().parents[2] / "guide"
    bundled = packaged_root / "Trainer" / "definitions.yml"
    updated = active_content_root(packaged_root) / "Trainer" / "definitions.yml"
    return load_exercises(updated if updated.is_file() else bundled)


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
