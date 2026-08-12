"""Gemeinsame Datenmodelle für Aufgaben und Rückmeldungen."""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class RuleDefinition:
    """Menschenlesbare Beschreibung eines Trainer-Prüfbausteins."""

    kind: str
    success: str
    failure: str
    hint: str = ""


@dataclass(frozen=True)
class CheckResult:
    """Ergebnis einer einzelnen, für Lernende sichtbaren Prüfung."""

    passed: bool
    success: str
    failure: str
    hint: str = ""

    @property
    def message(self) -> str:
        return self.success if self.passed else self.failure


@dataclass(frozen=True)
class OptimizationResult:
    """Optionale Bewertung der Struktur und Kürze einer Lösung."""

    score: int
    tips: tuple[str, ...] = ()
    maximum: int = 10


@dataclass(frozen=True)
class CheckReport:
    """Gesamtergebnis einer Aufgabe."""

    title: str
    results: tuple[CheckResult, ...]
    optimization: OptimizationResult | None = None

    @property
    def passed(self) -> int:
        return sum(result.passed for result in self.results)

    @property
    def successful(self) -> bool:
        return self.passed == len(self.results)


@dataclass(frozen=True)
class Exercise:
    """Registrierbare Aufgabe mit einer einheitlichen Prüfschnittstelle."""

    name: str
    title: str
    checker: Callable[..., CheckReport]
    rules: tuple[RuleDefinition, ...] = ()
    definition_hash: str = ""
