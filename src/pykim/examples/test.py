"""Technischer Gesamttest wichtiger PyKIM-Funktionen."""

import sys
from pykim import *


# Zeigt, welchen Python-Interpreter die IDE zum Starten verwendet.
print("Python:", sys.executable)

# Kim beginnt standardmäßig an der Position (0, 0).
print("Start:", get_x(), get_y())

# Kim an eine sichere Startposition innerhalb der Pixelwelt setzen.
set_x(10)
set_y(10)
print("Gesetzt:", get_x(), get_y())

# Jede Bewegung später mit 0,2 Sekunden pro Pixelschritt wiedergeben.
animate()

# Ab jetzt hinterlässt Kim bei jeder Bewegung eine violette Spur.
set_color("purple")
paint_start()

# Ein Quadrat mit einer Seitenlänge von fünf Pixeln abfahren.
up(5)
right(5)
down(5)
left(5)

# Folgende Bewegungen würden keine Spur mehr hinterlassen.
paint_stop()
print("Nach der Runde:", get_x(), get_y())

# Die Farbe an Kims aktueller Position auslesen.
print("Farbe:", get_color())

# Fenster öffnen und die vorbereitete Animation abspielen.
run()
