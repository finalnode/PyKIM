"""Helpers for tests and exercise setup."""

import pykim

WIDTH, HEIGHT = pykim.WIDTH, pykim.HEIGHT


def reset_world() -> None:
    pykim._reset()


def set_pixel_for_test(x: int, y: int, color: str | int) -> None:
    x, y = pykim._position(x, y)
    pykim.world.cells[y][x] = pykim._color(color)


def get_world_state() -> tuple[tuple[int, ...], ...]:
    return tuple(map(tuple, pykim.world.cells))


def get_painted_pixels() -> set[tuple[int, int]]:
    """Gib die Koordinaten aller nicht schwarzen Pixel zurück."""
    return {
        (x, y)
        for y, row in enumerate(pykim.world.cells)
        for x, color in enumerate(row)
        if color != 0
    }


def get_pending_tones() -> tuple[int, ...]:
    return tuple(note for note, _ in pykim._notes)


def get_pending_audio_events() -> tuple[tuple[int, int], ...]:
    """Gib Tonhöhe und Länge aller noch abzuspielenden Ereignisse zurück."""
    return tuple(pykim._notes)


__all__ = [
    "HEIGHT", "WIDTH", "get_painted_pixels", "get_pending_audio_events",
    "get_pending_tones",
    "get_world_state", "reset_world", "set_pixel_for_test",
]
