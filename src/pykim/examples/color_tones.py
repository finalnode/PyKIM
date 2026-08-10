"""Farben mit Tönen verbinden."""

from pykim import *
from pykim.testing import set_pixel_for_test

set_x(20)
set_y(20)
set_pixel_for_test(20, 20, "red")

if get_color() == "red":
    play_tone("C4")

run()
