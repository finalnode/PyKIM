"""Helpers for tests and exercise setup."""

import pykim

WIDTH, HEIGHT = pykim.WIDTH, pykim.HEIGHT


def reset_world() -> None:
    pykim._reset()


def set_pixel_for_test(x: int, y: int, color: str | int) -> None:
    x, y = pykim._position(x, y)
    pykim._pixels[y][x] = pykim._color(color)


def get_world_state() -> tuple[tuple[int, ...], ...]:
    return tuple(map(tuple, pykim._pixels))


def get_pending_tones() -> tuple[int, ...]:
    return tuple(note for note, _ in pykim._notes)


__all__ = [
    "HEIGHT", "WIDTH", "get_pending_tones", "get_world_state", "reset_world",
    "set_pixel_for_test",
]
