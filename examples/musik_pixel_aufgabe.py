"""Musterlösung: Eigene Pixel-Unterklasse mit Farbe und Ton."""

from pykim import Pixel, world


class MusikPixel(Pixel):
    def __init__(self, pixel_world, name, x, y, *, color, note):
        super().__init__(pixel_world, name, x, y)
        self.color = color
        self.note = note

    def update(self):
        if self.world.btnp("space"):
            self.play_tone(self.note)

    def draw(self):
        self.world.pset(self.get_x(), self.get_y(), self.color)


mia = world.spawn(MusikPixel, "MIA", 50, 60, color="purple", note="C4")
leo = world.spawn(MusikPixel, "LEO", 80, 60, color="orange", note="E4")


def update():
    pass


def draw():
    world.cls("black")
    world.text(5, 5, "Leertaste: MusikPixel spielen", "white")
    mia.draw()
    leo.draw()


world.run(update, draw, check="musik-pixel-klasse")
