"""Die gemeinsame Farbfläche und Verwaltung mehrerer Pixel."""

import inspect
from contextlib import contextmanager
from collections.abc import Callable, Iterator
from typing import TypeVar

import pykim as api

from .pixel import Pixel

PixelType = TypeVar("PixelType", bound=Pixel)


class World:
    """Gemeinsame Farbfläche, Ausgabe und Verwaltung aller Pixel."""

    def __init__(self) -> None:
        self.extra_pixels: list[Pixel] = []
        self._parallel_events: dict[Pixel, list[dict[str, object]]] | None = None
        self._backend: object | None = None
        self._zoom = 1
        self._background_color = 0
        self._obstacle_colors: set[int] = set()

    @property
    def cells(self) -> list[list[int]]:
        return api._pixels

    @property
    def pixels(self) -> tuple[Pixel, ...]:
        return (api.kim, *self.extra_pixels)

    def new_pixel(self, name: str, x: int = 0, y: int = 0) -> Pixel:
        return self.spawn(Pixel, name, x, y)

    def spawn(
        self,
        pixel_class: type[PixelType],
        name: str,
        x: int = 0,
        y: int = 0,
        **attributes: object,
    ) -> PixelType:
        """Erzeuge eine Instanz einer eigenen Pixel-Unterklasse."""
        if not isinstance(pixel_class, type) or not issubclass(pixel_class, Pixel):
            raise TypeError("pixel_class muss eine Unterklasse von Pixel sein.")
        if name == "KIM" or any(pixel.name == name for pixel in self.extra_pixels):
            raise ValueError(f"Der Pixelname {name!r} wird bereits verwendet.")
        pixel = pixel_class(self, name, x, y, **attributes)
        self.extra_pixels.append(pixel)
        api._register_animation_pixel(pixel, x, y)
        return pixel

    @property
    def width(self) -> int:
        return api.WIDTH

    @property
    def height(self) -> int:
        return api.HEIGHT

    @property
    def frame_count(self) -> int:
        return 0 if self._backend is None else self._backend.frame_count

    @property
    def background_color(self) -> str:
        """Gib die aktuelle Hintergrundfarbe als kanonischen Farbnamen zurück."""
        return api.COLORS[self._background_color]

    @property
    def obstacle_colors(self) -> tuple[str, ...]:
        """Gib alle Hindernisfarben in Reihenfolge der Pyxel-Palette zurück."""
        return tuple(
            api.COLORS[color] for color in sorted(self._obstacle_colors)
        )

    def set_background(self, color: str | int) -> None:
        """Setze die Hintergrundfarbe und leere die logische Welt damit."""
        color_index = api._color(color)
        self._background_color = color_index
        for row in self.cells:
            row[:] = [color_index] * api.WIDTH
        if api._animation_delay_frames is not None:
            api._animation_pixels = [row[:] for row in self.cells]

    def set_obstacle(self, *colors: str | int) -> None:
        """Markiere eine oder mehrere Farben als unpassierbar."""
        if not colors:
            raise TypeError("set_obstacle() benötigt mindestens eine Farbe.")
        self._obstacle_colors.update(api._color(color) for color in colors)

    def remove_obstacle(self, *colors: str | int) -> None:
        """Mache eine oder mehrere Hindernisfarben wieder passierbar."""
        if not colors:
            raise TypeError("remove_obstacle() benötigt mindestens eine Farbe.")
        for color in colors:
            self._obstacle_colors.discard(api._color(color))

    def clear_obstacles(self) -> None:
        """Mache alle Farben wieder passierbar."""
        self._obstacle_colors.clear()

    def is_obstacle(self, x: int, y: int) -> bool:
        """Prüfe, ob die Farbe an einer Position als Hindernis gilt."""
        x, y = api._position(x, y)
        return self.cells[y][x] in self._obstacle_colors

    def get_obstacles(self, x: int, y: int) -> tuple[str, ...]:
        """Nenne Hindernisse und Weltränder auf den vier Nachbarfeldern."""
        x, y = api._position(x, y)
        obstacles = []
        for direction, (dx, dy) in api._DIRECTIONS.items():
            neighbor_x, neighbor_y = x + dx, y + dy
            if not (0 <= neighbor_x < api.WIDTH and 0 <= neighbor_y < api.HEIGHT):
                obstacles.append(direction)
            elif self.cells[neighbor_y][neighbor_x] in self._obstacle_colors:
                obstacles.append(direction)
        return tuple(obstacles)

    def count_color(self, color: str | int) -> int:
        """Zähle alle Weltfelder mit der angegebenen Farbe."""
        color_index = api._color(color)
        return sum(row.count(color_index) for row in self.cells)

    def _movement_distance(
        self, x: int, y: int, dx: int, dy: int, steps: int
    ) -> int:
        """Begrenze eine Bewegung auf das Feld vor dem ersten Hindernis."""
        for distance in range(1, steps + 1):
            if self.is_obstacle(x + dx * distance, y + dy * distance):
                return distance - 1
        return steps

    def cls(self, color: str | int = "black") -> None:
        """Leere die Anzeige; außerhalb von draw() auch die logische Welt."""
        color_index = api._color(color)
        if self._backend is not None:
            self._backend.cls(color_index)
        else:
            for row in self.cells:
                row[:] = [color_index] * api.WIDTH

    clear = cls

    def pset(self, x: int, y: int, color: str | int) -> None:
        x, y = api._position(x, y)
        color_index = api._color(color)
        if self._backend is not None:
            api._draw_cell(self._backend, x, y, color_index)
        else:
            self.cells[y][x] = color_index

    def rect(
        self, x: int, y: int, width: int, height: int, color: str | int
    ) -> None:
        """Zeichne ein gefülltes Rechteck wie pyxel.rect()."""
        x, y = api._position(x, y)
        width = api._positive_size(width, "width")
        height = api._positive_size(height, "height")
        api._position(x + width - 1, y + height - 1)
        color_index = api._color(color)
        if self._backend is not None:
            screen_x, screen_y = api._screen_position(x, y)
            zoom = self._zoom
            self._backend.rect(
                screen_x, screen_y, width * zoom, height * zoom, color_index
            )
        else:
            for row in self.cells[y:y + height]:
                row[x:x + width] = [color_index] * width

    def text(self, x: int, y: int, value: object, color: str | int = "white") -> None:
        """Zeichne Text im interaktiven draw()-Modus."""
        x, y = api._position(x, y)
        if self._backend is None:
            raise RuntimeError("world.text() kann nur innerhalb von draw() verwendet werden.")
        screen_x, screen_y = api._screen_position(x, y)
        self._backend.text(screen_x, screen_y, str(value), api._color(color))

    def btn(self, key: str) -> bool:
        return self._key_query("btn", key)

    def btnp(self, key: str) -> bool:
        return self._key_query("btnp", key)

    def btnr(self, key: str) -> bool:
        return self._key_query("btnr", key)

    def _key_query(self, method: str, key: str) -> bool:
        if not isinstance(key, str):
            raise TypeError("key muss ein Tastenname sein.")
        names = {
            "left": "KEY_LEFT", "right": "KEY_RIGHT", "up": "KEY_UP",
            "down": "KEY_DOWN", "space": "KEY_SPACE", "enter": "KEY_RETURN",
            "escape": "KEY_ESCAPE",
        }
        normalized = key.lower()
        constant = names.get(normalized, f"KEY_{normalized.upper()}")
        if self._backend is None:
            return False
        if not hasattr(self._backend, constant):
            raise ValueError(f"Die Taste {key!r} ist unbekannt.")
        return bool(getattr(self._backend, method)(getattr(self._backend, constant)))

    def animate(self, delay: int | float = 0.1) -> None:
        api.animate(delay)

    def speed(self, value: int) -> None:
        api.speed(value)

    def zoom(self, value: int) -> None:
        """Vergrößere Weltpixel bei gleichbleibender Fenstergröße."""
        value = api._integer(value, "zoom")
        if not 1 <= value <= 10:
            raise ValueError("zoom muss zwischen 1 und 10 liegen.")
        self._zoom = value

    def play_tone(self, note: str | int, beats: int = 1) -> None:
        """Spiele einen Ton über das gemeinsame Audiosystem."""
        api.play_tone(note, beats)

    def play_pause(self, beats: int = 1) -> None:
        """Füge dem gemeinsamen Audiosystem eine Pause hinzu."""
        api.play_pause(beats)

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

    def run(
        self,
        update: Callable[[], None] | None = None,
        draw: Callable[[], None] | None = None,
        *,
        check: str | None = None,
    ) -> None:
        source = None
        if check is not None:
            caller = inspect.currentframe()
            caller = caller.f_back if caller is not None else None
            try:
                source = inspect.getsource(caller) if caller is not None else ""
            except (OSError, TypeError):
                source = ""
        api.run(update, draw, check=check, _source=source)
