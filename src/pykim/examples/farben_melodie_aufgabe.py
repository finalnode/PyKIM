"""Musterlösung: Farben lesen und als Melodie wiedergeben."""


from pykim import *

farben = ["red", "green", "cyan", "yellow"]
for x, farbe in enumerate(farben, start=20):
    set_position(x, 20)
    set_color(farbe)
    paint()
    paint_stop()

set_position(20, 20)
for _ in range(4):
    farbe = get_color()
    if farbe == "red":
        play_tone("C4")
    elif farbe == "green":
        play_tone("E4")
    elif farbe == "cyan":
        play_tone("G4")
    else:
        play_tone("C5", beats=2)
    right()

run(check="farben-melodie")
