"""Optionale Host-Schnittstelle für externe Traineranwendungen.

PyKIM kennt weder Kurszustand noch in:si. Eine Host-Anwendung kann einen
Provider explizit, über die Umgebungsvariable ``PYKIM_TRAINER_PROVIDER`` oder
über einen Python-Entry-Point bereitstellen.
"""

from __future__ import annotations

import importlib
import os
from importlib import metadata
from typing import Protocol


PROVIDER_ENV = "PYKIM_TRAINER_PROVIDER"
ENTRY_POINT_GROUP = "pykim.trainer_provider"


class TrainerProvider(Protocol):
    def get_world_setup(self, exercise_name: str): ...

    def check_exercise(
        self,
        name: str,
        source: str,
        namespace: dict[str, object] | None = None,
    ): ...


_configured_provider: TrainerProvider | None = None


def configure_trainer_provider(provider: TrainerProvider | None) -> None:
    """Setze einen Provider für den aktuellen Prozess, vor allem für Hosts/Tests."""
    global _configured_provider
    _configured_provider = provider


def _from_spec(spec: str) -> TrainerProvider:
    module_name, separator, attribute = spec.partition(":")
    if not module_name or not separator or not attribute:
        raise RuntimeError(
            f"Ungültiger Trainer-Provider {spec!r}; erwartet wird 'modul:objekt'."
        )
    module = importlib.import_module(module_name)
    return getattr(module, attribute)


def trainer_provider() -> TrainerProvider:
    if _configured_provider is not None:
        return _configured_provider
    configured = os.environ.get(PROVIDER_ENV, "").strip()
    if configured:
        return _from_spec(configured)
    providers = tuple(metadata.entry_points().select(group=ENTRY_POINT_GROUP))
    if len(providers) == 1:
        return providers[0].load()
    if len(providers) > 1:
        names = ", ".join(sorted(provider.name for provider in providers))
        raise RuntimeError(f"Mehrere PyKIM-Trainer-Provider gefunden: {names}.")
    raise RuntimeError(
        "Für prepare() oder run(check=...) ist eine Traineranwendung nötig. "
        "Starte die Aufgabe über in:si oder konfiguriere einen Trainer-Provider."
    )


__all__ = [
    "ENTRY_POINT_GROUP",
    "PROVIDER_ENV",
    "TrainerProvider",
    "configure_trainer_provider",
    "trainer_provider",
]
