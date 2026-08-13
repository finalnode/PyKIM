"""Die bewegliche und malende Pixel-Figur."""

from typing import TYPE_CHECKING

import pykim as api

if TYPE_CHECKING:
    from .world import World


class Pixel:
    """Eine bewegliche, malende Figur innerhalb der gemeinsamen Welt."""

    def __init__(
        self,
        pixel_world: "World",
        name: str,
        x: int = 0,
        y: int = 0,
        *,
        default: bool = False,
    ) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Ein Pixel benötigt einen Namen.")
        self.world = pixel_world
        self.name = name
        self._default = default
        self._x, self._y = api._position(x, y)
        self._selected_color: int | None = None
        self._painting_path = False
        self.visible = True

    def get_x(self) -> int:
        return api.get_x() if self._default else self._x

    @property
    def x(self) -> int:
        return self.get_x()

    @x.setter
    def x(self, value: int) -> None:
        self.set_x(value)

    def get_y(self) -> int:
        return api.get_y() if self._default else self._y

    @property
    def y(self) -> int:
        return self.get_y()

    @y.setter
    def y(self, value: int) -> None:
        self.set_y(value)

    @property
    def position(self) -> tuple[int, int]:
        """Kompatible Eigenschaft; neuer Code kann ``get_position()`` verwenden."""
        return self.get_position()

    def get_position(self) -> tuple[int, int]:
        return self.get_x(), self.get_y()

    @position.setter
    def position(self, value: tuple[int, int]) -> None:
        if not isinstance(value, tuple) or len(value) != 2:
            raise TypeError("position muss ein Tupel aus x und y sein.")
        self.set_position(*value)

    def set_position(self, x: int, y: int) -> None:
        if self._default:
            api.set_position(x, y)
        else:
            self._x, self._y = api._position(x, y)

    def set_x(self, x: int) -> None:
        self.set_position(x, self.get_y())

    def set_y(self, y: int) -> None:
        self.set_position(self.get_x(), y)

    def _paint_color(self) -> int:
        if self._default:
            return api._paint_color()
        return (
            api.DEFAULT_COLOR
            if self._selected_color is None
            else self._selected_color
        )

    def _move(self, dx: int, dy: int, steps: int) -> None:
        if self._default:
            api._move(dx, dy, steps)
            return
        steps = api._integer(steps, "steps")
        if steps < 0:
            raise ValueError("steps muss mindestens 0 sein.")
        old_x, old_y = self._x, self._y
        api._position(old_x + dx * steps, old_y + dy * steps)
        moved_steps = self.world._movement_distance(
            old_x, old_y, dx, dy, steps
        )
        new_x = old_x + dx * moved_steps
        new_y = old_y + dy * moved_steps
        if self._painting_path and moved_steps > 0:
            for distance in range(moved_steps + 1):
                x = old_x + dx * distance
                y = old_y + dy * distance
                self.world.cells[y][x] = self._paint_color()
        if api.runtime.animation_delay_frames is not None:
            color = self._paint_color() if self._painting_path else None
            for distance in range(1, moved_steps + 1):
                api._record_pixel_position(
                    self,
                    old_x + dx * distance,
                    old_y + dy * distance,
                    color,
                )
        self._x, self._y = new_x, new_y

    def up(self, steps: int = 1) -> None:
        self._move(0, -1, steps)

    def down(self, steps: int = 1) -> None:
        self._move(0, 1, steps)

    def left(self, steps: int = 1) -> None:
        self._move(-1, 0, steps)

    def right(self, steps: int = 1) -> None:
        self._move(1, 0, steps)

    def set_color(self, color: str | int) -> None:
        if self._default:
            api.set_color(color)
        else:
            self._selected_color = api._color(color)

    def paint(self, color: str | int | None = None) -> None:
        """Färbe die aktuelle Position und aktiviere die Farbspur."""
        if self._default:
            api.paint(color)
            return
        if color is not None:
            self._selected_color = api._color(color)
        elif self._selected_color is None:
            self._selected_color = api.DEFAULT_COLOR
        self.world.cells[self._y][self._x] = self._paint_color()
        api._record_pixel_position(self, self._x, self._y, self._paint_color())
        self._painting_path = True

    def paint_start(self, color: str | int | None = None) -> None:
        """Kompatibler Alias für paint()."""
        self.paint(color)

    def paint_path(self, color: str | int | None = None) -> None:
        """Kompatibler Alias für paint()."""
        self.paint(color)

    def paint_stop(self) -> None:
        if self._default:
            api.paint_stop()
        else:
            self._painting_path = False

    def hide(self) -> None:
        """Verstecke die Figur; Malen und Bewegen bleiben möglich."""
        self.visible = False
        api._record_pixel_visibility(self, False)

    def show(self) -> None:
        """Zeige eine zuvor versteckte Figur wieder an."""
        self.visible = True
        api._record_pixel_visibility(self, True)

    def get_color(self, *args: object) -> str:
        if self._default:
            return api.get_color(*args)
        if not args:
            x, y = self._x, self._y
        elif len(args) == 1 and isinstance(args[0], str):
            direction = args[0]
            if direction not in api._DIRECTIONS:
                names = ", ".join(api._DIRECTIONS)
                raise ValueError(
                    f"Die Richtung {direction!r} ist unbekannt. "
                    f"Verfügbare Richtungen: {names}"
                )
            dx, dy = api._DIRECTIONS[direction]
            x, y = self._x + dx, self._y + dy
        elif len(args) == 2:
            x, y = args
        else:
            raise TypeError(
                "get_color() erlaubt kein Argument, eine Richtung oder x und y."
            )
        x, y = api._position(x, y)
        return api.COLORS[self.world.cells[y][x]]

    def get_obstacles(self) -> tuple[str, ...]:
        """Nenne die Richtungen angrenzender Hindernisse und Weltränder."""
        return self.world.get_obstacles(self.get_x(), self.get_y())

    def collect(self) -> str:
        """Sammle die Farbe am aktuellen Feld ein und lege Hintergrund frei."""
        x, y = self.get_position()
        color = self.world.cells[y][x]
        self.world.cells[y][x] = self.world._background_color
        if api.runtime.animation_delay_frames is not None:
            if self.world._capture_parallel(
                self, paint=(x, y, self.world._background_color)
            ):
                return api.COLORS[color]
            api._record_pixel_position(
                self, x, y, self.world._background_color
            )
        return api.COLORS[color]

    def play_tone(self, note: str | int, beats: int = 1) -> None:
        api.play_tone(note, beats)

    def play_pause(self, beats: int = 1) -> None:
        api.play_pause(beats)

    def update(self) -> None:
        """Optionaler Frame-Hook für eigene Pixel-Unterklassen."""

    def draw(self) -> None:
        """Zeichne diese Figur im interaktiven Modus."""
        backend = self.world._backend
        if backend is None or not self.visible:
            return
        index = self.world.pixels.index(self)
        api._draw_actor(backend, self.get_x(), self.get_y(), index * 3)
