"""Paint a path, inspect its colors, and react to what Kim sees."""


from pykim import *


# Build a path from three colored sections.
for x in range(20, 60):
    set_x(x)
    set_y(60)
    set_color("green")
    paint()
    paint_stop()

for x in range(60, 100):
    set_x(x)
    set_color("yellow")
    paint()
    paint_stop()

for x in range(100, 140):
    set_x(x)
    set_color("red")
    paint()
    paint_stop()

# Walk over the path and play a different tone for each section.
paint_stop()
set_x(20)
animate()
last_color = ""

for _ in range(119):
    color = get_color()

    if color != last_color:
        if color == "green":
            play_tone("C4")
        elif color == "yellow":
            play_tone("E4")
        elif color == "red":
            play_tone("G4")

        last_color = color

    right()

run()
