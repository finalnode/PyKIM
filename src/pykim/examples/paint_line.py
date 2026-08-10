"""Eine einfache Linie malen."""

from pykim import *

set_x(20)
set_y(20)
animate()
set_color("purple")
paint_start()

for _ in range(30):
    right()

paint_stop()

run()
