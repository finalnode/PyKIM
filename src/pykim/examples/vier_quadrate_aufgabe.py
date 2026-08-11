"""Musterlösung: vier benachbarte Quadrate mit Funktion und Schleife."""


from pykim import *


def zeichne_quadrat():
    right(5)
    down(5)
    left(5)
    up(5)
    right(5)


speed(30)
set_position(20, 20)
paint("purple")

for _ in range(4):
    zeichne_quadrat()

run(check="vier-quadrate")
