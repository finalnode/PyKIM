"""Build a checkerboard with nested loops and a condition."""


from pykim import *


for y in range(20, 100):
    set_y(y)

    for x in range(40, 120):
        set_x(x)

        if (x // 8 + y // 8) % 2 == 0:
            set_color("purple")
        else:
            set_color("peach")

        paint()
        paint_stop()

run()
