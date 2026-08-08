from pykim import *
from pykim.testing import set_pixel_for_test

set_x(20)
set_y(20)
for x in range(20, 61):
    set_pixel_for_test(x, 20, "green")

animate()
for _ in range(40):
    if get_color("right") == "green":
        right()

run()
