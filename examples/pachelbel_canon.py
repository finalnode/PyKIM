"""A monophonic adaptation of Pachelbel's Canon in D."""

from pykim import *


# Arpeggios make the famous harmony audible even with only one sound channel.
progression = [
    "D3", "A3", "F#4", "A3",    # D major
    "C#3", "A3", "E4", "A3",    # A major / C sharp
    "B2", "F#3", "D4", "F#3",    # B minor
    "F#2", "C#3", "A3", "C#3",   # F sharp minor
    "G2", "D3", "B3", "D3",      # G major
    "D3", "A3", "F#4", "A3",     # D major
    "G2", "D3", "B3", "D3",      # G major
    "A2", "E3", "C#4", "E3",     # A major
]

for _ in range(2):
    for note in progression:
        play_tone(note)  # beats=1 is the default

# The first violin theme follows over the same implied harmony.
theme = [
    "F#4", "E4", "D4", "C#4", "B3", "A3", "B3", "C#4",
    "D4", "C#4", "B3", "A3", "G3", "F#3", "G3", "E3",
]

for note in theme:
    play_tone(note, beats=2)

play_tone("D3", beats=4)
run()
