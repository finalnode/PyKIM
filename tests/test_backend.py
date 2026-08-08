import sys

import pykim
from pykim import (
    animate,
    get_color,
    paint,
    play_tone,
    right,
    run,
    set_color,
    set_x,
    set_y,
)
from pykim.testing import set_pixel_for_test


class FakeSound:
    def __init__(self):
        self._notes, self._tones, self._volumes, self._effects = [], [], [], []
        self.speed = 0

    notes = property(lambda self: self._notes)
    tones = property(lambda self: self._tones)
    volumes = property(lambda self: self._volumes)
    effects = property(lambda self: self._effects)


class FakePyxel:
    def __init__(self):
        self.sounds = [FakeSound()]
        self.calls = []
        self.frame_count = 0

    def init(self, width, height, *, title):
        self.calls.append(("init", width, height, title))

    def run(self, update, draw):
        for _ in range(47):
            update()
        draw()

    def play_pos(self, channel):
        return None

    def play(self, channel, sound):
        self.calls.append(("play", channel, sound))

    def cls(self, color):
        self.calls.append(("cls", color))

    def pset(self, x, y, color):
        self.calls.append(("pset", x, y, color))

    def circ(self, *args):
        self.calls.append(("circ", *args))

    def line(self, *args):
        self.calls.append(("line", *args))

def test_run_connects_world_and_audio_to_pyxel(monkeypatch):
    fake = FakePyxel()
    monkeypatch.setitem(sys.modules, "pyxel", fake)
    set_x(10)
    set_y(20)
    set_color("purple")
    paint()
    play_tone("C4", beats=2)

    run()

    assert ("init", 160, 120, "PyKIM") in fake.calls
    assert ("pset", 10, 20, 2) in fake.calls
    assert ("pset", 10, 20, 1) in fake.calls
    assert not any(call[0] in ("circ", "line") for call in fake.calls)
    assert ("play", 0, 0) in fake.calls
    assert fake.sounds[0].notes == [24]
    assert fake.sounds[0].speed == 60


def test_kim_rotates_through_all_visible_colors():
    fake = FakePyxel()
    set_x(10)
    set_y(20)

    pykim._draw_kim(fake)
    assert fake.calls == [("pset", 10, 20, 1)]


def test_kim_skips_the_background_color():
    fake = FakePyxel()
    set_x(10)
    set_y(20)
    set_pixel_for_test(10, 20, "navy")

    pykim._draw_kim(fake)

    assert fake.calls == [("pset", 10, 20, 2)]


def test_color_sensor_lights_up_during_animation():
    fake = FakePyxel()
    set_x(10)
    set_y(20)
    set_pixel_for_test(11, 20, "green")
    animate(0.01)

    assert get_color("right") == "green"
    pykim._advance_animation()
    pykim._draw_sensor(fake)

    assert fake.calls == [("pset", 11, 20, 12)]
    assert get_color(11, 20) == "green"

    fake.calls.clear()
    fake.frame_count = 5
    pykim._draw_kim(fake)
    assert fake.calls == [("pset", 10, 20, 2)]

    fake.calls.clear()
    fake.frame_count = 70
    pykim._draw_kim(fake)
    assert fake.calls == [("pset", 10, 20, 15)]

    fake.calls.clear()
    fake.frame_count = 75
    pykim._draw_kim(fake)
    assert fake.calls == [("pset", 10, 20, 1)]


def test_animation_draws_the_path_step_by_step():
    fake = FakePyxel()
    set_x(10)
    set_y(20)
    animate(0.01)
    set_color("purple")
    paint()
    right(2)

    pykim._draw_world(fake)
    assert ("pset", 10, 20, 2) not in fake.calls
    assert ("pset", 11, 20, 2) not in fake.calls

    pykim._advance_animation()
    fake.calls.clear()
    pykim._draw_world(fake)
    assert ("pset", 10, 20, 2) in fake.calls
    assert ("pset", 11, 20, 2) not in fake.calls

    pykim._advance_animation()
    fake.calls.clear()
    pykim._draw_world(fake)
    assert ("pset", 11, 20, 2) in fake.calls
    assert ("pset", 12, 20, 2) not in fake.calls


def test_maximum_axes_shrink_to_a_pixel():
    fake = FakePyxel()

    pykim._draw_axes(fake, 20, 30, 1, 10)
    assert fake.calls == [
        ("line", 0, 30, 159, 30, 10),
        ("line", 20, 0, 20, 119, 10),
    ]

    fake.calls.clear()
    pykim._draw_axes(fake, 20, 30, 0, 10)
    assert fake.calls == [("pset", 20, 30, 10)]


def test_pause_finishes_without_using_a_pyxel_rest():
    fake = FakePyxel()
    pykim.play_pause()
    play_tone("C4")

    for _ in range(10):
        pykim._play_next_note(fake)

    assert ("play", 0, 0) in fake.calls
    assert fake.sounds[0].notes == [24]
