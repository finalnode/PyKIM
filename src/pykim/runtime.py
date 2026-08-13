"""Laufzeitgebundener Zustand einer PyKIM-Welt."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pixel import Pixel
    from .world import World


@dataclass
class Runtime:
    """Bündele den veränderlichen Zustand einer PyKIM-Ausführung.

    Die imperative API verwendet vorerst eine öffentliche Standardinstanz.
    Dadurch bleibt ``from pykim import *`` kompatibel, während Zustand nicht
    länger über viele unabhängige Modulvariablen verteilt ist.
    """

    width: int
    height: int
    default_color: int
    x: int = 0
    y: int = 0
    selected_color: int | None = None
    painting_path: bool = False
    cells: list[list[int]] = field(init=False)
    notes: deque[tuple[int, int]] = field(default_factory=deque)
    pause_frames: int = 0
    animation_delay_frames: int | None = None
    animation_positions: list[tuple[int, int]] = field(default_factory=list)
    animation_actor_positions: list[dict[object, tuple[int, int]]] = field(
        default_factory=list
    )
    animation_actor_visibility: list[dict[object, bool]] = field(
        default_factory=list
    )
    animation_paints: list[list[tuple[int, int, int]]] = field(
        default_factory=list
    )
    animation_sensors: list[tuple[int, int] | None] = field(default_factory=list)
    animation_pixels: list[list[int]] = field(default_factory=list)
    animation_index: int = 0
    animation_ticks: int = 0
    world: "World | None" = field(default=None, init=False, repr=False)
    kim: "Pixel | None" = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.cells = [[0] * self.width for _ in range(self.height)]

    def bind(self, world: "World", kim: "Pixel") -> None:
        """Verbinde die Laufzeit nach dem Aufbau mit Welt und Standardfigur."""

        self.world = world
        self.kim = kim

    def reset_state(self) -> None:
        """Setze den fachlichen und zeitlichen Zustand vollständig zurück."""

        self.x = 0
        self.y = 0
        self.selected_color = None
        self.painting_path = False
        self.cells = [[0] * self.width for _ in range(self.height)]
        self.notes.clear()
        self.pause_frames = 0
        self.animation_delay_frames = None
        self.animation_positions.clear()
        self.animation_actor_positions.clear()
        self.animation_actor_visibility.clear()
        self.animation_paints.clear()
        self.animation_sensors.clear()
        self.animation_pixels.clear()
        self.animation_index = 0
        self.animation_ticks = 0


__all__ = ["Runtime"]
