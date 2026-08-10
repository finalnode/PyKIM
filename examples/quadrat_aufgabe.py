"""Beispiel fuer eine lokal in Thonny pruefbare Aufgabe."""

import pykim as k

k.speed(30)
# Aufgabe: Zeichne ab (50, 50) ein Quadrat mit der Kantenlänge 5.
k.set_position(50, 50)
k.paint_path("purple")
k.right(4)
k.down(3)
k.left(4)
k.up(3)

k.run(check="quadrat-5")
