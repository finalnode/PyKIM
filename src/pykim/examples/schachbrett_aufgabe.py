"""Musterlösung: Schachbrett mit Funktion, Bedingung und zwei Schleifen."""


from pykim import *


def zeichne_feld(x, y, color):
    set_position(x, y)
    set_color(color)
    paint()
    paint_stop()


speed(100)
for y in range(8):
    for x in range(8):
        if (x + y) % 2 == 0:
            color = "purple"
        else:
            color = "orange"
        zeichne_feld(20 + x, 20 + y, color)

run(check="schachbrett-8")
