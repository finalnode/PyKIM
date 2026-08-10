"""Beispiel fuer eine lokal in Thonny pruefbare Aufgabe."""

import pykim as k

k.speed(30)
# Aufgabe: Zeichne ab (50, 50) ein Quadrat mit der Kantenlänge 5.
k.set_position(50, 50)
k.paint_path("purple")
k.right(5)
k.down(5)
k.left(5)
k.up(5)

k.run(check="quadrat-5")
