"""Dateisystemvertrag zwischen PyKIM-Trainern und einer Lernanwendung."""

from __future__ import annotations

import os
from pathlib import Path


CONTENT_ROOT_ENV = "PYKIM_TRAINER_CONTENT_DIR"


def trainer_content_root() -> Path:
    """Liefere den von der aufrufenden Anwendung freigegebenen Inhaltsstand.

    PyKIM kennt weder Kursverwaltung noch Repository-Synchronisation. Eine
    Anwendung wie in:si übergibt stattdessen den bereits geprüften lokalen
    Inhaltsordner über ``PYKIM_TRAINER_CONTENT_DIR``.
    """
    configured = os.environ.get(CONTENT_ROOT_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parent / "content"


__all__ = ["CONTENT_ROOT_ENV", "trainer_content_root"]
