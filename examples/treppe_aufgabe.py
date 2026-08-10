"""Mit einer Schleife eine Treppe zeichnen und lokal prüfen."""

from pykim import *


# Aufgabe: Zeichne ab (50, 50) eine Treppe aus fünf 5 x 5 Pixel großen Stufen.
set_position(50, 50)
paint_path("purple")
for _ in range(5):
    right(5)
    down(5)

run(check="treppe-5")
