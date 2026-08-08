import sys
print(sys.executable)

from pykim import *


print("Start:", get_x(), get_y())

set_x(10)
set_y(10)
print("Gesetzt:", get_x(), get_y())

up()
right()
down()
left()
print("Nach der Runde:", get_x(), get_y())

set_color("purple")
paint()
print("Farbe:", get_color())
