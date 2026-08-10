"""Musterlösung: acht einzelne Punkte mit einer Schleife zeichnen."""

from pykim import *


speed(30)
set_position(20, 20)
set_color("purple")

for _ in range(8):
    paint()
    right(2)

run(check="punktlinie-8")
