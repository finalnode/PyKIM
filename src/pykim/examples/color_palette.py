"""Paint one stripe in each of Pyxel's 16 colors."""


from pykim import *


for color in range(16):
    set_color(color)
    set_y(20 + color * 4)

    for x in range(20, 140):
        set_x(x)
        paint()
        paint_stop()

run()
