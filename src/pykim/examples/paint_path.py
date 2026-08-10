"""Let Kim draw a colorful path while moving."""


from pykim import *


set_x(40)
set_y(30)
animate()
paint_start("orange")

for _ in range(2):
    right(60)
    down(20)
    left(60)
    down(20)

paint_stop()

run()
