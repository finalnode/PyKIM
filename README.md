# PyKIM

PyKIM 0.2.0 ist eine kleine Python-Lernumgebung auf Basis von Pyxel. Kim, eine
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

set_position(20, 20)
speed(30)
set_color("purple")
paint_start()

for _ in range(30):
    right()

run()
```

`animate()` zeigt Kims Bewegungen beim späteren `run()` Schritt für Schritt.
Die Standardverzögerung beträgt `0.1` Sekunden pro Pixel und kann angepasst
werden, zum Beispiel mit `animate(0.25)`. Auch `right(10)` zeigt dabei alle
zehn Zwischenpositionen. Wird die Zeile entfernt, erscheint Kim wie bisher
sofort an der Endposition.

Alternativ bietet `speed(...)` eine einfache Skala von 1 bis 100:

```python
speed(1)    # sehr langsam
speed(50)   # schnell
speed(100)  # Bewegungen sofort anzeigen
```

`speed(...)` wird wie `animate(...)` vor den Bewegungen aufgerufen. Der Wert
muss eine ganze Zahl zwischen 1 und 100 sein.

`run()` öffnet am Ende das Pyxel-Fenster. Der Ursprung `(0, 0)` liegt links
oben; `x` wächst nach rechts und `y` nach unten. Kim startet bei `(0, 0)`.
Bewegungen, die die Welt verlassen würden, lösen eine verständliche Exception
aus. Kim erscheint als einzelner Pixel, der durch alle sichtbaren Farben der
Pyxel-Palette rotiert. Trifft die Cursorfarbe auf dieselbe Farbe im
Hintergrund, überspringt Kim sie automatisch. Mit `get_color(direction)` oder
`get_color(x, y)` gelesene Pixel leuchten bei aktivem `animate()` kurz cyan
auf, ohne dass sich ihre gespeicherte Farbe ändert.

Beim Start kreuzen sich eine bildschirmfüllende x- und y-Achse an Kims
Startposition. Beide Achsen schrumpfen zu Kims Pixel zusammen. Nach der
Bewegungs- oder Musiksequenz bleibt Kim einfach als einzelner Pixel stehen.

## Schüler-API

Position lesen und absolut setzen:

```python
get_x()
get_y()
set_position(x, y)
set_x(x)
set_y(y)
```

`set_position(x, y)` ist der einfache Standardweg. `set_x(...)` und
`set_y(...)` bleiben verfügbar, wenn nur eine Koordinate geändert werden soll.

Relativ bewegen (Standardschrittweite `1`):

```python
up(steps=1)
down(steps=1)
left(steps=1)
right(steps=1)
```

Farbe auswählen, einen einzelnen Pixel färben, eine Spur beginnen oder
beenden und Pixel lesen:

```python
set_color("purple")  # oder set_color(2)
paint()              # färbt nur den aktuellen Pixel
paint_start()
right(20)            # malt jeden besuchten Pixel
paint_stop()
get_color()          # aktueller Pixel
get_color("right")   # unmittelbarer Nachbar
get_color(100, 50)   # beliebige Position
```

`paint_start()` färbt sofort den aktuellen Pixel und danach jeden Pixel, über
den Kim sich bewegt. `paint_stop()` beendet die Spur. Ohne vorherige
Farbauswahl wird Weiß verwendet:

```python
paint_start()
right(20)
paint_stop()

paint_start("orange")
down(10)
paint_stop()
```

Der bisherige Name `paint_path()` funktioniert weiterhin als Alias für
`paint_start()`. `paint()` bleibt bewusst eine atomare Ein-Pixel-Operation.

`get_color()` gibt immer einen lesbaren, kanonischen Farbnamen zurück. Die 16
Farben sind: `black`, `navy`, `purple`, `green`, `brown`, `dark_blue`,
`light_blue`, `white`, `red`, `orange`, `yellow`, `lime`, `cyan`, `gray`,
`pink` und `peach`.

### Objektweg und mehrere Pixel

Die freien Befehle steuern den mitgelieferten Pixel `kim`. Dieselbe Bewegung
kann deshalb auch objektorientiert geschrieben werden:

```python
from pykim import kim, world

kim.set_position(20, 20)
kim.paint_path("purple")
kim.right(10)

world.speed(30)
world.run()
```

Beide Schreibweisen verändern dieselbe Welt. Für mehrere Figuren erzeugt die
Welt zusätzliche Pixel:

```python
from pykim import kim, world

kim.set_position(20, 20)
kim.paint_path("purple")
kim.right(10)

mia = world.new_pixel("MIA", x=20, y=30)
mia.paint_path("orange")
mia.right(10)

leo = world.new_pixel("LEO", x=20, y=40)
leo.paint_path("cyan")
leo.right(10)
leo.hide()  # Spur behalten, Figur verstecken

world.run()
```

Ein vollständiges Beispiel steht in `examples/mehrere_pixel.py`.

Jeder Pixel kann unabhängig versteckt und wieder gezeigt werden:

```python
mia.hide()
mia.show()
```

Für KIM funktionieren zusätzlich die freien Kurzformen `hide()` und `show()`.
Das Verstecken entfernt weder die gemalte Spur noch die aktuelle Position.

Normalerweise werden Befehle in ihrer geschriebenen Reihenfolge animiert. In
einem `parallel()`-Block beginnen die Bewegungen verschiedener Pixel dagegen
im selben Animationsschritt:

```python
with world.parallel():
    kim.right(20)
    mia.left(20)
    leo.up(10)
```

Die Figuren dürfen unterschiedlich viele Schritte ausführen. Eine früher
fertige Figur wartet an ihrem Ziel, während die anderen weiterlaufen.

Das Beispiel `examples/mehrere_pixel.py` wird mit
`world.run(check="mehrere-pixel")` geprüft. Der Trainer vergleicht die Namen
und Endpositionen aller Figuren, jeden farbigen Weltpixel, LEOs Sichtbarkeit
und die Verwendung eines `world.parallel()`-Blocks.

Töne akzeptieren MIDI-Zahlen von 36 bis 95 (`C2` bis `B6`) oder übliche
Notennamen. Dieser Bereich entspricht den 60 von Pyxel unterstützten Tonhöhen:

```python
play_tone(60)
play_tone("C4")
play_tone("F#4", beats=2)
play_pause()
play_pause(beats=2)
```

> **Hinweis zur Oktavbenennung:** PyKIM verwendet die verbreitete
> MIDI-Konvention, bei der `C4` der MIDI-Note 60 entspricht. Pyxel benennt
> seine 60 Tonhöhen dagegen von `C0` bis `B4`. Deshalb entspricht zum Beispiel
> PyKIMs `C4` klanglich Pyxels `C2`; PyKIM rechnet die Bezeichnungen beim
> Abspielen automatisch um.

`beats` ist eine positive ganze Zahl und bestimmt die Länge eines Tons oder
einer Pause. Töne, die vor `run()` angefordert werden, werden gespeichert und
nach dem Öffnen des Fensters nacheinander abgespielt.

### Interaktiver Modus und Übergang zu Pyxel

Neben fertigen Befehlsfolgen unterstützt PyKIM eine Spielschleife. `update()`
enthält Eingaben und Zustandsänderungen, `draw()` baut das aktuelle Bild auf:

```python
from pykim import kim, world

def update():
    if world.btn("right") and kim.get_x() < world.width - 1:
        kim.right()

def draw():
    world.cls("black")
    world.text(5, 5, "Pfeiltaste rechts", "white")
    kim.draw()

world.run(update, draw)
```

Eingaben stehen als `world.btn(key)` für gehaltene, `world.btnp(key)` für neu
gedrückte und `world.btnr(key)` für losgelassene Tasten bereit. Vordefinierte
Namen sind `left`, `right`, `up`, `down`, `space`, `enter` und `escape`;
Buchstaben wie `a` funktionieren ebenfalls.

Die Pyxel-nahen Weltoperationen lauten:

```python
world.cls("black")
world.pset(10, 20, "purple")
world.rect(10, 20, 30, 15, "orange")
world.text(5, 5, "Punkte: 3", "white")

world.width
world.height
world.frame_count
```

Im späteren Pyxel-Programm werden daraus hauptsächlich andere Namen:

```text
world.btn("right")  -> pyxel.btn(pyxel.KEY_RIGHT)
world.cls("black")  -> pyxel.cls(0)
world.pset(...)      -> pyxel.pset(...)
world.run(...)       -> pyxel.run(...)
```

Wird nur `update` übergeben, leert PyKIM die Anzeige und zeichnet alle
sichtbaren Pixel automatisch. Mit einer eigenen `draw()`-Funktion lernen
Schüler bewusst die für Pyxel zentrale Trennung von Logik und Darstellung.

### Eigene Pixel-Klassen

`world.spawn()` erzeugt Instanzen eigener `Pixel`-Unterklassen. Ihre
`update()`-Methoden werden im interaktiven Modus automatisch einmal pro Frame
aufgerufen:

```python
from pykim import Pixel, world

class MusikPixel(Pixel):
    def __init__(self, pixel_world, name, x, y, *, note):
        super().__init__(pixel_world, name, x, y)
        self.note = note

    def update(self):
        if self.world.btnp("space"):
            self.play_tone(self.note)

    def draw(self):
        self.world.pset(self.get_x(), self.get_y(), "purple")

mia = world.spawn(MusikPixel, "MIA", 40, 60, note="C4")
leo = world.spawn(MusikPixel, "LEO", 80, 60, note="E4")
world.run(lambda: None)
```

Damit können Unterrichtsreihen von Objektbenutzung über eigene Attribute und
Methoden zu Vererbung, Überschreiben und polymorphem Verhalten führen.

## Tests und Aufgaben

Zusätzliche, nicht zur Anfänger-API gehörende Hilfen liegen in
`pykim.testing`:

```python
from pykim.testing import reset_world, set_pixel_for_test, get_world_state
```

Weitere vollständige Programme stehen im Ordner `examples`.
Alle automatisch prüfbaren Aufgabenstellungen stehen gesammelt in
[`AUFGABEN.md`](AUFGABEN.md).

### Lokale Aufgabenprüfung in Thonny

Mit `pykim.trainer` können Lernende eine Aufgabe direkt in ihrem Programm
prüfen und erhalten deutschsprachige Hinweise. Die Welt beginnt immer bei
`(0, 0)`. Verlangt eine Aufgabe wie hier den Startpunkt `(50, 50)`, müssen die
Lernenden ihn selbst setzen:

```python
from pykim import *

# Lösung hier einfügen
set_position(50, 50)

run(check="quadrat-5")
```

Die Prüfung bewertet die fertige Zeichnung und nicht die verwendete
Befehlsfolge. Das Quadrat darf daher in unterschiedlichen Richtungen und auch
mithilfe einer Schleife gezeichnet werden. Ein vollständiges Beispiel liegt in
`examples/quadrat_aufgabe.py`.

Eine zweite Aufgabe fordert eine Treppe aus fünf jeweils 5 Pixel breiten und
hohen Stufen. Dabei wird auch geprüft, ob die wiederholten Bewegungen mit einer
Schleife kurz formuliert wurden:

```python
set_position(50, 50)
paint_path("purple")
for _ in range(5):
    right(5)
    down(5)
run(check="treppe-5")
```

`run(check=...)` prüft zuerst die Zeichnung und erkennt dabei auch die
verwendete Schleife. Anschließend öffnet es wie gewohnt das Pyxel-Fenster. Das
vollständige Beispiel steht in `examples/treppe_aufgabe.py`.

#### Neue Trainer-Aufgaben ergänzen

Der Trainer ist nach Verantwortlichkeiten aufgeteilt:

```text
pykim/trainer/
├── models.py             # Ergebnisse und Aufgabenmodell
├── feedback.py           # deutsche Konsolenausgabe
├── optimization.py       # optionale Bewertung von Codequalität
├── builder.py            # einheitliche Autoren-API und Codeanalyse
├── runner.py             # Einstieg für run(check=...)
└── exercises/
    ├── __init__.py       # automatische Aufgaben-Registry
    ├── checkerboard.py
    ├── color_melody.py
    ├── dotted_line.py
    ├── four_squares.py
    ├── multiple_pixels.py
    ├── custom_pixel.py
    ├── interactive.py
    ├── rhythm.py
    ├── scale.py
    ├── square.py
    └── stairs.py
```

Neue Aufgaben werden mit `ExerciseBuilder` deklarativ beschrieben. Technische
Weltabfragen, Farbindizes und AST-Analysen gehören nicht in die Aufgabendatei.
Eine vollständige Anleitung mit kopierbaren Vorlagen steht in
[`TRAINER_AUTOREN.md`](TRAINER_AUTOREN.md). Jede Datei mit einem erzeugten
`EXERCISE` wird automatisch registriert. Der PyKIM-Kern und `run(check=...)`
müssen dafür nicht verändert werden.

Alle mitgelieferten Aufgaben geben zusätzlich zur fachlichen Prüfung eine
prozentuale Bewertung der Codelänge aus. Die jeweilige Schwelle entspricht der
mitgelieferten kompakten Musterlösung; Leerzeilen und reine Kommentarzeilen
werden nicht gezählt:

```text
Optimierung: 100 %
✓ Dein Code ist für diese Aufgabe optimal aufgebaut.
```

Bei einer längeren Lösung erscheinen stattdessen die tatsächliche und die
optimale Zeilenzahl als konkreter Tipp. Geforderte Kontrollstrukturen wie
Schleifen oder Funktionen werden unabhängig davon fachlich geprüft.
