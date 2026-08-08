# PyKIM

PyKIM 0.1 ist eine kleine Python-Lernumgebung auf Basis von Pyxel. Kim, eine
kleine Drohne, bewegt sich pixelweise durch eine 160 × 120 Pixel große Welt,
liest und verändert Farben und kann einfache Töne spielen. Die gesamte Logik
funktioniert auch ohne ein geöffnetes Grafikfenster und ist daher gut testbar.

## Installation

Python 3.10 oder neuer wird benötigt. Im Projektverzeichnis:

```bash
python -m pip install -e .
```

Für die Entwicklung und Tests:

```bash
python -m pip install -e '.[test]'
pytest
```

## Erstes Programm

```python
from pykim import *

set_x(20)
set_y(20)
set_color("purple")

for _ in range(30):
    paint()
    right()

run()
```

`run()` öffnet am Ende das Pyxel-Fenster. Der Ursprung `(0, 0)` liegt links
oben; `x` wächst nach rechts und `y` nach unten. Kim startet bei `(0, 0)`.
Bewegungen, die die Welt verlassen würden, lösen eine verständliche Exception
aus. Kim erscheint als Quadcopter von oben; ihre logische Position ist der
Mittelpunkt des Sprites.

## Schüler-API

Position lesen und absolut setzen:

```python
get_x()
get_y()
set_x(x)
set_y(y)
```

Relativ bewegen (Standardschrittweite `1`):

```python
up(steps=1)
down(steps=1)
left(steps=1)
right(steps=1)
```

Farbe auswählen, den aktuellen Pixel färben und Pixel lesen:

```python
set_color("purple")  # oder set_color(2)
paint()
get_color()          # aktueller Pixel
get_color("right")   # unmittelbarer Nachbar
get_color(100, 50)   # beliebige Position
```

Mit `paint_path()` hinterlässt Kim bei jeder Bewegung eine durchgehende Spur.
Ohne vorherige Farbauswahl wird Weiß verwendet:

```python
paint_path()
right(20)

paint_path("orange")
down(10)
```

`get_color()` gibt immer einen lesbaren, kanonischen Farbnamen zurück. Die 16
Farben sind: `black`, `navy`, `purple`, `green`, `brown`, `dark_blue`,
`light_blue`, `white`, `red`, `orange`, `yellow`, `lime`, `cyan`, `gray`,
`pink` und `peach`.

Töne akzeptieren MIDI-Zahlen von 36 bis 95 (`C2` bis `B6`) oder übliche
Notennamen. Dieser Bereich entspricht den 60 von Pyxel unterstützten Tonhöhen:

```python
play_tone(60)
play_tone("C4")
play_tone("F#4", beats=2)
play_pause()
play_pause(beats=2)
```

`beats` ist eine positive ganze Zahl und bestimmt die Länge eines Tons oder
einer Pause. Töne, die vor `run()` angefordert werden, werden gespeichert und
nach dem Öffnen des Fensters nacheinander abgespielt.

## Tests und Aufgaben

Zusätzliche, nicht zur Anfänger-API gehörende Hilfen liegen in
`pykim.testing`:

```python
from pykim.testing import reset_world, set_pixel_for_test, get_world_state
```

Weitere vollständige Programme stehen im Ordner `examples`.
