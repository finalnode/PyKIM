"""Die gemeinsame Farbfläche und Verwaltung mehrerer Pixel."""

import inspect
from contextlib import contextmanager
from collections.abc import Iterator

import pykim as api

from .pixel import Pixel


class World:
    """Gemeinsame Farbfläche, Ausgabe und Verwaltung aller Pixel."""

    def __init__(self) -> None:
        self.extra_pixels: list[Pixel] = []
        self._parallel_events: dict[Pixel, list[dict[str, object]]] | None = None

    @property
    def cells(self) -> list[list[int]]:
        return api._pixels

    @property
    def pixels(self) -> tuple[Pixel, ...]:
        return (api.kim, *self.extra_pixels)

    def new_pixel(self, name: str, x: int = 0, y: int = 0) -> Pixel:
        if name == "KIM" or any(pixel.name == name for pixel in self.extra_pixels):
            raise ValueError(f"Der Pixelname {name!r} wird bereits verwendet.")
        pixel = Pixel(self, name, x, y)
        self.extra_pixels.append(pixel)
        api._register_animation_pixel(pixel, x, y)
        return pixel

    def animate(self, delay: int | float = 0.1) -> None:
        api.animate(delay)

    def speed(self, value: int) -> None:
        api.speed(value)

    def _capture_parallel(
        self,
        pixel: Pixel,
        *,
        position: tuple[int, int] | None = None,
        paint: tuple[int, int, int] | None = None,
        visible: bool | None = None,
        sensor: tuple[int, int] | None = None,
    ) -> bool:
        if self._parallel_events is None:
            return False
        self._parallel_events.setdefault(pixel, []).append(
            {
                "position": position,
                "paint": paint,
                "visible": visible,
                "sensor": sensor,
            }
        )
        return True

    def _flush_parallel(self) -> None:
        events_by_pixel = self._parallel_events or {}
        self._parallel_events = None
        if not events_by_pixel or api._animation_delay_frames is None:
            return

        frame_count = max(map(len, events_by_pixel.values()))
        for frame_index in range(frame_count):
            positions = api._animation_actor_positions[-1].copy()
            visibility = api._animation_actor_visibility[-1].copy()
            paints: list[tuple[int, int, int]] = []
            sensor = None

            for pixel, events in events_by_pixel.items():
                if frame_index >= len(events):
                    continue
                event = events[frame_index]
                if event["position"] is not None:
                    positions[pixel] = event["position"]
                if event["paint"] is not None:
                    paints.append(event["paint"])
                if event["visible"] is not None:
                    visibility[pixel] = event["visible"]
                if event["sensor"] is not None:
                    sensor = event["sensor"]

            api._animation_positions.append(positions[api.kim])
            api._animation_actor_positions.append(positions)
            api._animation_actor_visibility.append(visibility)
            api._animation_paints.append(paints)
            api._animation_sensors.append(sensor)

    @contextmanager
    def parallel(self) -> Iterator[None]:
        """Zeichne die Befehle mehrerer Pixel zeitgleich statt nacheinander."""
        if self._parallel_events is not None:
            raise RuntimeError("parallel()-Blöcke können nicht verschachtelt werden.")
        self._parallel_events = {}
        try:
            yield
        finally:
            self._flush_parallel()

    def run(self, *, check: str | None = None) -> None:
        source = None
        if check is not None:
            caller = inspect.currentframe()
            caller = caller.f_back if caller is not None else None
            try:
                source = inspect.getsource(caller) if caller is not None else ""
            except (OSError, TypeError):
                source = ""
        api.run(check=check, _source=source)
