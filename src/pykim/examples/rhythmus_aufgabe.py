"""Musterlösung: Ein rhythmisches Motiv zweimal spielen."""


from pykim import *


def spiele_motiv():
    play_tone("C4")
    play_tone("E4")
    play_tone("G4", beats=2)
    play_pause()


for _ in range(2):
    spiele_motiv()

run(check="rhythmus-motiv")
