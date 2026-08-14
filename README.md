# PyKIM

**Aktuelle Version: 0.6.0**

PyKIM ist ein kleines Pythonmodul für einen visuellen, pixelbasierten Einstieg
in die Programmierung. Eine Figur namens KIM bewegt sich auf einer
[Pyxel](https://github.com/kitao/pyxel)-Welt, malt Pixel, erkennt Farben und
Hindernisse, sammelt Gegenstände und spielt Töne.

Die allgemeine Desktop-Lernumgebung, Kursverwaltung und Autorenwerkstatt werden
im eigenständigen Projekt [in:si](https://github.com/finalnode/insi)
weiterentwickelt. PyKIM bleibt eine unabhängige Bibliothek und kann ebenso in
Thonny, VS Code, PyCharm oder eigenen Pythonprojekten verwendet werden.

Seit Version 0.6.0 werden PyKIM und in:si unabhängig veröffentlicht. PyKIM
enthält ausschließlich Pixelwelt, Laufzeit und Trainerkern; Desktop-App,
Kursverwaltung und Autorenwerkzeuge gehören zu in:si.

## Installation

```bash
python -m pip install "git+https://github.com/finalnode/PyKIM.git"
```

Für die Entwicklung:

```bash
git clone https://github.com/finalnode/PyKIM.git
cd PyKIM
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest
```

Unter Windows wird die Umgebung mit `.venv\Scripts\activate` aktiviert.

## Erstes Programm

```python
from pykim import *

set_position(20, 20)
paint("purple")

for _ in range(5):
    right(5)
    down(5)

run()
```

## Imperative API

### Bewegung und Position

| Funktion | Wirkung |
|---|---|
| `right(steps=1)` | nach rechts bewegen |
| `left(steps=1)` | nach links bewegen |
| `up(steps=1)` | nach oben bewegen |
| `down(steps=1)` | nach unten bewegen |
| `set_position(x, y)` | Position setzen |
| `get_position()` | Position als `(x, y)` lesen |
| `set_x(x)`, `set_y(y)` | einzelne Koordinate setzen |
| `get_x()`, `get_y()` | einzelne Koordinate lesen |

### Farbe und Zeichnen

| Funktion | Wirkung |
|---|---|
| `set_color(color)` | aktuelle Farbe wählen |
| `paint(color=None)` | aktuelles Feld malen |
| `paint_start(color=None)` | Malspur einschalten |
| `paint_stop()` | Malspur ausschalten |
| `paint_path(color=None)` | Malspur einschalten und Startfeld malen |
| `get_color(...)` | Farbe am aktuellen, benachbarten oder angegebenen Feld lesen |
| `count_color(color)` | Felder einer Farbe zählen |

PyKIM verwendet die 16 Farben der Pyxel-Standardpalette, beispielsweise
`"black"`, `"purple"`, `"orange"`, `"green"`, `"cyan"`, `"yellow"` und
`"white"`.

### Welten, Hindernisse und Sammelobjekte

```python
world.background("dark_blue")
world.obstacle_color("red")

if obstacle("right"):
    down()

collect("yellow")
print(items_left("yellow"))
```

Hindernisse werden über eine definierte Farbe markiert. KIM kann benachbarte
Felder prüfen, ohne die Weltlogik an eine bestimmte Labyrinthdarstellung zu
binden. Sammelobjekte bleiben normale Farbfelder und können dadurch in
Aufgaben, Spielen und automatischen Tests gleich verwendet werden.

### Audio, Animation und Start

| Funktion | Wirkung |
|---|---|
| `play_tone(note, beats=1)` | Note wie `"C4"` abspielen |
| `play_pause(beats=1)` | Pause einfügen |
| `speed(value)` | Animationsgeschwindigkeit setzen |
| `animate(enabled=True)` | schrittweise Animation schalten |
| `run(check=None)` | Welt starten; optional einen extern bereitgestellten Trainer auswerten |

## Objektorientierte API

```python
from pykim import Pixel, World

world = World()
mia = world.new_pixel("MIA", 20, 20)
mia.color = "orange"
mia.paint_path()
mia.right(10)

print(mia.position)
world.run()
```

Mehrere Pixel können sequenziell oder gemeinsam bewegt werden:

```python
with world.parallel():
    world.kim.right(10)
    mia.down(10)
```

Eigene Figuren entstehen durch Unterklassen von `Pixel`; interaktive Projekte
können `update()` und `draw()` mit `world.run(update, draw)` verwenden.

## Runtime statt global verteilter Zustände

Position, Weltmatrix, Audioereignisse und Animation liegen in einer gebundenen
`Runtime`-Instanz. Die einfachen Modulbefehle verwenden aus
Kompatibilitätsgründen eine Standardinstanz:

```python
import pykim

other = pykim.Runtime(pykim.WIDTH, pykim.HEIGHT, pykim.DEFAULT_COLOR)
other_world = pykim.World(other)
```

Damit können Anwendungen und Tests voneinander unabhängige Welten erzeugen,
ohne die einsteigerfreundliche imperative API aufzugeben.

## Trainer als externer Inhaltsvertrag

Der Trainerkern kann deklarative YAML-Prüfungen laden. PyKIM selbst enthält
bewusst keinen fest eingebauten Kurs. Eine Lernanwendung oder ein Kurs setzt
den bereits geprüften Inhaltsordner über `PYKIM_TRAINER_CONTENT_DIR`; darunter
liegt üblicherweise `Trainer/`.

Diese Trennung sorgt dafür, dass:

- PyKIM nicht von in:si oder einer Kursverwaltung abhängt,
- verschiedene Kurse eigene Trainerstände verwenden können,
- Trainer und Kursinhalte gemeinsam versioniert werden,
- die Bibliothek auch völlig ohne Lernplattform funktioniert.

PyKIM führt beim Laden der YAML-Dateien keinen beliebigen Pythoncode aus.
Schülerprogramme selbst sind jedoch regulärer Pythoncode; eine aufrufende
Anwendung muss Prozessisolation, Berechtigungen und gegebenenfalls eine
Betriebssystem-Sandbox bereitstellen.

## Beispiele

Die Module unter `pykim.examples` zeigen unter anderem:

- Linien, Malspuren und Farbpaletten,
- mehrere Pixel und parallele Bewegung,
- Farbsensoren, Hindernisse und Sammelfelder,
- Melodien und rhythmische Motive,
- interaktive Steuerung und Pyxel-nahe Projekte.

Beispiel:

```bash
python -m pykim.examples.hindernisse
```

## Geplante Weiterentwicklung

Die Pixelwelt soll Labyrinthe und typische Suchalgorithmen anschaulich machen:
Breiten- und Tiefensuche, kürzeste Wege, Dijkstra und A*. Einzelne Suchschritte
sollen animierbar und durch externe Trainer prüfbar werden.

### Sprachmaps – geplant, noch nicht implementiert

Vorgesehen ist eine validierte Sprachmap für API-Aliase. Kurse oder
Sprachpakete sollen dann beispielsweise `right` als `rechts`, `paint` als
`male` oder `get_position` als `position_lesen` anbieten können, ohne
Python-Schlüsselwörter zu verändern.

Intern bleibt immer der kanonische PyKIM-Befehl erhalten, damit Projekte und
Trainer sprachübergreifend kompatibel bleiben. Vor der Veröffentlichung dieser
Funktion fehlen noch der Sprachpaket-Loader, Kollisionsprüfungen, eine
eindeutige Rückübersetzung und Tests für gemischte Sprachmaps. Diese Aliase
sind deshalb **nicht Bestandteil von PyKIM 0.6.0**.

## Tests

```bash
python -m pip install -e '.[test]'
python -m pytest
```

Die Kernprüfungen decken imperative und objektorientierte API, unabhängige
Runtimes, Weltlogik, Pyxel-Backend, Farben, Hindernisse, Sammelobjekte,
Animation und Audio ab.

## Lizenz

PyKIM steht unter der [MIT-Lizenz](LICENSE).
