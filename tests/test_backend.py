import sys

import pykim
from pykim import paint, play_tone, run, set_color, set_x, set_y


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
    assert ("play", 0, 0) in fake.calls
    assert fake.sounds[0].notes == [24]
    assert fake.sounds[0].speed == 60


def test_pause_finishes_without_using_a_pyxel_rest():
    fake = FakePyxel()
    pykim.play_pause()
    play_tone("C4")

    for _ in range(10):
        pykim._play_next_note(fake)

    assert ("play", 0, 0) in fake.calls
    assert fake.sounds[0].notes == [24]
