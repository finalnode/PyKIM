"""Musterlösung: C-Dur-Tonleiter."""


from pykim import *

noten = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]

for note in noten:
    play_tone(note)

run(check="tonleiter-c-dur")
