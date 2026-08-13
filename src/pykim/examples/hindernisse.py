"""Zeige farbbasierte Hindernisse in einer Welt mit eigenem Hintergrund."""

from pykim import *


world.set_background("light_blue")
world.rect(30, 10, 2, 40, "red")
world.set_obstacle("red")

set_position(20, 20)
paint("purple")
right(20)

run()
