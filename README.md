# PyKIM

PyKIM 0.3.0 ist eine deutschsprachige Python-Lernumgebung auf Basis von
[Pyxel](https://github.com/kitao/pyxel). Eine kleine Pixel-Figur namens KIM
bewegt sich durch eine 160 × 120 Pixel große Welt, liest und verändert Farben,
zeichnet Spuren und spielt Töne. Dieselben Grundlagen lassen sich zuerst mit
einfachen Befehlen, später objektorientiert und schließlich mit der Pyxel-API
verwenden.

Zum Projekt gehören zwei eng verbundene Teile:

- **PyKIM-Bibliothek:** testbare Zeichen-, Bewegungs-, Audio- und Weltlogik.
- **PyKIM Suite:** lokale Desktop-Lernumgebung mit Skript, Aufgaben, Tests,
  Lernstand, IDE-Anbindung, Projekten und persönlichen Erweiterungen.

Die fachliche Weltlogik liegt nicht nur im Grafikfenster. Aufgaben können
deshalb deterministisch geprüft werden, ohne Bildschirminhalte vergleichen zu
müssen.

> Entwicklungsstand: Alpha. Der aktuelle Releaseweg konzentriert sich auf
> macOS. Die Python-Bibliothek selbst ist plattformunabhängig; vollständige
> Desktop-Bundles für Windows und Linux sind noch nicht fertiggestellt.

## Inhalt

- [Funktionsumfang](#funktionsumfang)
- [Schnellstart](#schnellstart)
- [Grundmodell](#grundmodell)
- [Imperative API](#imperative-api)
- [Farben und Zeichnen](#farben-und-zeichnen)
- [Animation](#animation)
- [Töne und Musik](#töne-und-musik)
- [Objektorientierte API](#objektorientierte-api)
- [Mehrere Pixel und Parallelität](#mehrere-pixel-und-parallelität)
- [Interaktive Programme](#interaktive-programme)
- [Aufgaben und Trainer](#aufgaben-und-trainer)
- [PyKIM Suite](#pykim-suite)
- [Kursordner und Setupdatei](#kursordner-und-setupdatei)
- [Externes Kurs-Repository](#externes-kurs-repository)
- [Eigene Erweiterungen](#eigene-erweiterungen)
- [Eigene Projekte und Pyxel-Ressourcen](#eigene-projekte-und-pyxel-ressourcen)
- [IDE und Python-Laufzeit](#ide-und-python-laufzeit)
- [Speicherorte und Datenschutz](#speicherorte-und-datenschutz)
- [Installation und Entwicklung](#installation-und-entwicklung)
- [macOS-App und DMG](#macos-app-und-dmg)
- [Grenzen und zurückgestellte Funktionen](#grenzen-und-zurückgestellte-funktionen)
- [Lizenzierung](#lizenzierung)

## Funktionsumfang

### Programmieren mit PyKIM

- Bewegungen nach oben, unten, links und rechts
- absolute Positionierung und lesbare Koordinaten
- 16 Farben der Pyxel-Standardpalette
- einzelne Farbpixel und durchgehende Malspuren
- Farbsensor am aktuellen Feld, an Nachbarfeldern oder beliebigen Koordinaten
- schrittweise Animation mit einer Geschwindigkeit von 1 bis 100
- Töne, Pausen, Tonlängen, Rhythmen und Melodien
- imperative Kurzbefehle für Einsteiger
- objektorientierte Steuerung über `Pixel` und `World`
- mehrere benannte Pixel in derselben Welt
- parallele Bewegungsblöcke
- eigene Pixel-Unterklassen mit `update()` und `draw()`
- interaktive Spielschleifen und Tastaturabfragen
- Pyxel-nahe Zeichenoperationen als vorbereiteter API-Übergang

### Lernen mit der Suite

- lokaler Kursordner, der auch auf USB- oder WebDAV-Laufwerken liegen kann
- Kursauswahl durch eine kleine `.pykim-setup`-Datei
- Skripte, Aufgaben und Trainer aus einem externen GitHub-Repository
- eingebautes Skript mit Inhaltsnavigation
- ausführbare und kopierbare Codebeispiele
- Aufgabenbearbeitung in einem Codeeditor
- Speichern, Starten, Stoppen, Kopieren und Öffnen in einer externen IDE
- deutschsprachige automatische Testfälle mit ausklappbaren Details
- Analyse von Schleifen, Funktionen, Bedingungen, Klassen und Parallelität
- Optimierungsbewertung anhand relevanter Codezeilen
- lokaler Lernstand und persönliches Dokubuch
- Beispielgalerie und Pyxel-Beispiele
- eigene Python-, PyKIM- und Pyxel-Projekte
- Start des Pyxel-Ressourceneditors für Sprites, Tilemaps, Sounds und Musik
- persönliches Modul `erweiterungen.py` für eigene Funktionen und Klassen
- Erkennung von Thonny, VS Code, PyCharm und benutzerdefinierten IDEs
- Erkennung und Auswahl geeigneter Python-Interpreter
- verwaltete lokale Python-Laufzeit mit Offline-Wheelhouse
- getrennte Updateprüfung für App und Lerninhalte

## Schnellstart

Ein minimales Programm:

```python
from pykim import *

speed(30)
paint("orange")
right(10)
down(5)
paint_stop()

run()
```

KIM startet bei `(0, 0)`. Der Ursprung liegt links oben. `x` wächst nach
rechts, `y` nach unten.

Eine typische Aufgabe mit automatischer Prüfung endet so:

```python
run(check="quadrat-5")
```

Der Trainer wertet vor dem Öffnen des Fensters die logische Welt und den
Quellcode aus und gibt verständliche Rückmeldungen auf der Konsole und in der
Suite aus.

## Grundmodell

Die Welt besitzt die feste Größe:

```python
WIDTH = 160
HEIGHT = 120
```

Gültige Koordinaten sind daher:

- `x`: `0` bis `159`
- `y`: `0` bis `119`

Bewegungen außerhalb der Welt werden nicht abgeschnitten, sondern mit einer
verständlichen `ValueError`-Exception abgewiesen. Schrittweiten und Beats
müssen ganze Zahlen sein; Boolesche Werte werden dabei nicht als Zahlen
akzeptiert.

PyKIM stellt direkt zwei Objekte bereit:

```python
from pykim import kim, world
```

- `kim` ist der mitgelieferte Standardpixel.
- `world` ist die gemeinsame Welt aller Pixel.
- Freie Befehle wie `right()` steuern dasselbe Objekt wie `kim.right()`.

## Imperative API

Der Einsteigerweg verwendet:

```python
from pykim import *
```

### Position lesen und setzen

| Funktion | Wirkung |
|---|---|
| `get_x()` | aktuelle x-Koordinate lesen |
| `get_y()` | aktuelle y-Koordinate lesen |
| `set_position(x, y)` | beide Koordinaten setzen |
| `set_x(x)` | nur x setzen |
| `set_y(y)` | nur y setzen |

```python
set_position(20, 30)
print(get_x())  # 20
print(get_y())  # 30
```

### Relativ bewegen

| Funktion | Standard | Wirkung |
|---|---:|---|
| `up(steps=1)` | 1 | nach oben |
| `down(steps=1)` | 1 | nach unten |
| `left(steps=1)` | 1 | nach links |
| `right(steps=1)` | 1 | nach rechts |

```python
set_position(20, 20)
right(8)
down(4)
print(get_x(), get_y())  # 28 24
```

Eine Schrittweite von `0` ist erlaubt. Negative Schrittweiten sind nicht
zulässig; für die Gegenrichtung wird der entsprechende Bewegungsbefehl
verwendet.

### Sichtbarkeit

```python
hide()
show()
```

`hide()` versteckt KIM, löscht aber weder Position noch Malspur. Ein
versteckter Pixel kann sich weiterhin bewegen und malen.

## Farben und Zeichnen

PyKIM verwendet die 16 Farben der Pyxel-Standardpalette:

| Index | Name | Index | Name |
|---:|---|---:|---|
| 0 | `black` | 8 | `red` |
| 1 | `navy` | 9 | `orange` |
| 2 | `purple` | 10 | `yellow` |
| 3 | `green` | 11 | `lime` |
| 4 | `brown` | 12 | `cyan` |
| 5 | `dark_blue` | 13 | `gray` |
| 6 | `light_blue` | 14 | `pink` |
| 7 | `white` | 15 | `peach` |

Farben dürfen als Name oder Index angegeben werden:

```python
set_color("purple")
set_color(2)
```

### Malspur

```python
paint("purple")  # aktuelles Feld malen und Spur einschalten
right(10)        # alle besuchten Felder malen
paint_stop()     # Spur ausschalten
```

`paint()` malt sofort die aktuelle Position. Ohne Argument verwendet es die
zuletzt mit `set_color()` gewählte Farbe, andernfalls Weiß. Für genau einen
Punkt wird die Spur direkt wieder beendet:

```python
paint("orange")
paint_stop()
```

`paint_start()` und `paint_path()` existieren als Kompatibilitätsaliase für
`paint()`, werden aber nicht mehr als Standard-API gelehrt und sind nicht in
`from pykim import *` enthalten.

### Farben lesen

```python
get_color()          # aktuelle Position
get_color("right")   # unmittelbarer rechter Nachbar
get_color(100, 50)   # beliebige Position
```

Erlaubte Richtungsnamen sind `up`, `down`, `left` und `right`. Das Ergebnis
ist immer ein kanonischer Farbname aus der Tabelle. Bei aktiver Animation wird
das gelesene Feld kurz als Sensor markiert, ohne seine gespeicherte Farbe zu
verändern.

## Animation

Ohne Animation erscheint die Welt direkt im Endzustand. Mit `animate()` werden
alle Zwischenschritte aufgezeichnet:

```python
animate()       # 0,1 Sekunden pro Schritt
animate(0.25)   # 0,25 Sekunden pro Schritt
```

Die schülerfreundliche Alternative ist:

```python
speed(1)    # sehr langsam
speed(50)   # schnell
speed(100)  # Endzustand sofort anzeigen
```

`speed()` akzeptiert nur ganze Zahlen von 1 bis 100. Animation und
Geschwindigkeit werden vor den Bewegungen konfiguriert.

Beim Start zeigt PyKIM für jeden sichtbaren Pixel eine kurze Achsenanimation.
Danach werden Bewegungen, Malereignisse, Sensorzugriffe und Sichtbarkeit in der
aufgezeichneten Reihenfolge wiedergegeben.

## Töne und Musik

```python
play_tone("C4")
play_tone("F#4", beats=2)
play_tone(60)
play_pause()
play_pause(beats=2)
```

### Tonhöhen

- MIDI-Zahlen von `36` bis `95`
- Notennamen von `C2` bis `B6`
- Vorzeichen `#` und `b`, beispielsweise `F#4` oder `Bb3`

PyKIM verwendet die verbreitete MIDI-Benennung, bei der `C4` der MIDI-Note 60
entspricht. Pyxel benennt seinen internen Bereich anders; PyKIM übersetzt die
Notennamen beim Abspielen automatisch.

`beats` ist eine positive ganze Zahl. Töne und Pausen werden in einer
gemeinsamen Warteschlange gespeichert und nach dem Start des Fensters in
Reihenfolge abgespielt.

```python
notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]

for note in notes:
    play_tone(note)
```

## Objektorientierte API

Die freie und die objektorientierte Schreibweise greifen auf denselben
Standardpixel zu:

```python
from pykim import kim, world

kim.position = (20, 20)
kim.paint("purple")
kim.right(10)
kim.paint_stop()

world.speed(30)
world.run()
```

### `Pixel`

Konstruktor:

```python
Pixel(pixel_world, name, x=0, y=0)
```

Normalerweise werden Pixel mit `world.new_pixel()` oder `world.spawn()`
erzeugt, nicht durch einen direkten Konstruktoraufruf.

| Eigenschaft/Methode | Bedeutung |
|---|---|
| `name` | eindeutiger Anzeigename |
| `world` | zugehörige Welt |
| `x`, `y` | les- und schreibbare Koordinaten |
| `position` | Tupel `(x, y)`, les- und schreibbar |
| `visible` | aktueller Sichtbarkeitszustand |
| `set_position(x, y)` | Position setzen |
| `set_x(x)`, `set_y(y)` | einzelne Koordinate setzen |
| `up/down/left/right(steps=1)` | bewegen |
| `set_color(color)` | Malfarbe auswählen |
| `paint(color=None)` | Feld malen und Spur aktivieren |
| `paint_stop()` | Spur beenden |
| `get_color(...)` | Farbe lesen |
| `hide()`, `show()` | Sichtbarkeit steuern |
| `play_tone(...)`, `play_pause(...)` | Audioereignis einreihen |
| `update()` | Hook pro Frame im interaktiven Modus |
| `draw()` | Figur im interaktiven Modus zeichnen |

### `World`

| Eigenschaft/Methode | Bedeutung |
|---|---|
| `width`, `height` | Weltgröße |
| `cells` | logische Farbmatrix |
| `pixels` | Tupel aus KIM und allen weiteren Pixeln |
| `frame_count` | aktueller Pyxel-Frame, außerhalb des Fensters `0` |
| `new_pixel(name, x=0, y=0)` | normalen Pixel erzeugen |
| `spawn(PixelClass, name, ...)` | eigene Pixel-Unterklasse erzeugen |
| `animate(delay=0.1)` | Animation einschalten |
| `speed(value)` | Geschwindigkeit 1 bis 100 |
| `play_tone(...)`, `play_pause(...)` | gemeinsames Audiosystem |
| `parallel()` | parallelen Befehlsblock starten |
| `cls(color="black")` | Anzeige bzw. Welt leeren |
| `clear(color="black")` | Alias für `cls()` |
| `pset(x, y, color)` | einen Weltpixel setzen |
| `rect(x, y, width, height, color)` | gefülltes Rechteck zeichnen |
| `text(x, y, value, color="white")` | Text in `draw()` zeichnen |
| `btn(key)` | Taste wird gehalten |
| `btnp(key)` | Taste wurde neu gedrückt |
| `btnr(key)` | Taste wurde losgelassen |
| `run(...)` | Fenster, Spielschleife oder Trainer starten |

Pixelnamen müssen eindeutig sein. `KIM` ist für den Standardpixel
reserviert.

## Mehrere Pixel und Parallelität

```python
from pykim import kim, world

world.speed(25)

kim.position = (20, 20)
kim.paint("purple")

mia = world.new_pixel("MIA", x=60, y=20)
mia.paint("orange")

leo = world.new_pixel("LEO", x=40, y=60)
leo.paint("cyan")

with world.parallel():
    kim.right(15)
    mia.left(15)
    leo.up(20)

kim.paint_stop()
mia.paint_stop()
leo.paint_stop()
leo.hide()

world.run()
```

Innerhalb von `world.parallel()` werden die Ereignisse verschiedener Pixel
zeitgleich wiedergegeben. Unterschiedlich lange Bewegungen sind erlaubt; ein
früher fertiger Pixel wartet an seiner Zielposition. Parallele Blöcke dürfen
nicht ineinander verschachtelt werden.

### Eigene Pixelklassen

```python
from pykim import Pixel, world


class MusikPixel(Pixel):
    def __init__(self, pixel_world, name, x=0, y=0, note="C4"):
        super().__init__(pixel_world, name, x, y)
        self.note = note

    def update(self):
        if self.world.btnp("space"):
            self.play_tone(self.note)


mia = world.spawn(MusikPixel, "MIA", 40, 30, note="E4")
world.run()
```

`world.spawn()` reicht zusätzliche benannte Argumente an den Konstruktor der
Unterklasse weiter und registriert die Figur für Welt und Animation.

## Interaktive Programme

Wird `run()` ohne Callbacks aufgerufen, zeigt PyKIM eine vorberechnete
Befehlsfolge. Mit `update` und `draw` arbeitet PyKIM als echte Spielschleife:

```python
from pykim import kim, world


def update():
    if world.btn("right") and kim.x < world.width - 1:
        kim.right()
    if world.btn("left") and kim.x > 0:
        kim.left()


def draw():
    world.cls("black")
    world.text(5, 5, "Pfeiltasten bewegen KIM", "white")
    kim.draw()


world.run(update, draw)
```

Vordefinierte Tastennamen:

```text
left right up down space enter escape
```

Buchstaben wie `a`, `w`, `s` und `d` werden ebenfalls auf die entsprechenden
Pyxel-Tastenkonstanten abgebildet. Außerhalb einer aktiven Spielschleife geben
Tastenabfragen `False` zurück.

Der API-Übergang zu Pyxel ist bewusst sichtbar:

```text
world.btn("right")  -> pyxel.btn(pyxel.KEY_RIGHT)
world.cls("black")  -> pyxel.cls(0)
world.pset(...)      -> pyxel.pset(...)
world.rect(...)      -> pyxel.rect(...)
world.text(...)      -> pyxel.text(...)
```

## `run()` und Headless-Betrieb

Signaturen:

```text
run(update=None, draw=None, *, check=None)
world.run(update=None, draw=None, *, check=None)
```

- Ohne Callbacks: aufgezeichnete Welt und Animation anzeigen.
- Mit `update`/`draw`: interaktive Pyxel-Schleife starten.
- Mit `check="kennung"`: vor dem Fenster den Trainer ausführen.
- Mit `PYKIM_HEADLESS=1`: Logik und Tests ausführen, kein Fenster öffnen.

`update` und `draw` müssen Funktionen oder `None` sein.

## Aufgaben und Trainer

Trainerdefinitionen sind YAML-Dateien. Damit müssen Autoren für reguläre
Aufgaben keine Python-Prüfdatei schreiben.

```yaml
format: 1
id: treppe-5
title: Treppe mit 5 Stufen
tests:
  - type: position
    position: [75, 75]
    hint: Prüfe die letzte Bewegung.
  - type: loop
    hint: Verwende eine for-Schleife.
optimization:
  optimal_lines: 8
```

Eine Datei darf eine einzelne Aufgabe oder eine Liste unter `exercises`
enthalten. Jede Aufgabe besitzt:

- eindeutige `id`
- angezeigten `title`
- mindestens einen Eintrag unter `tests`
- optional `optimization.optimal_lines`

### Unterstützte Prüftypen

| Typ | Prüft |
|---|---|
| `pixels` | erwartete Farbpositionen, Pfade, Treppen oder Schachbrett |
| `no-extra-pixels` | keine zusätzlichen gemalten Felder |
| `pixel-count` | exakte Anzahl gemalter Pixel |
| `square` | Start, Ende, Seitenlänge und geschlossener Rand |
| `position` | Endposition eines Pixels |
| `positions` | Endpositionen mehrerer Pixel |
| `pixel-names` | exakte Figurenmenge |
| `visibility` | sichtbar oder versteckt |
| `audio` | Noten, Pausen, Reihenfolge und Beats |
| `loop` | mindestens eine `for`- oder `while`-Schleife |
| `nested-loop` | verschachtelte Schleifen |
| `condition` | Bedingung und optional erforderliche Aufrufe |
| `function` | eigene Funktion, optional mit festem Namen |
| `calls` | geforderte Funktions- oder Methodenaufrufe |
| `parallel` | `with world.parallel():` |
| `class` | Klasse und optionale Basisklasse |
| `methods` | geforderte Methoden einer Klasse |
| `super-init` | Aufruf von `super().__init__()` |

Jeder Test kann eigene Texte für `success`, `failure` und `hint` besitzen.
Unbekannte YAML-Felder und unsichere Prüftypen werden abgewiesen.

### Optimierungsbewertung

`optimal_lines` zählt nichtleere Zeilen ohne reine Kommentare:

```text
Bewertung = min(100, optimal_lines / verwendete_Zeilen × 100)
```

Die Optimierungszahl ist ein Lernhinweis und entscheidet nicht automatisch
über die fachliche Korrektheit.

### Trainer-Hash

Jede geladene YAML-Definition erhält einen reproduzierbaren SHA-256-Hash. Vor
einer Bewertung vergleicht die Suite die lokalen Trainerdateien mit
`.pykim/trainer-hashes.json` des konfigurierten Kurs-Repositorys. Bei einer
erreichbaren Quelle werden abweichende Trainer neu synchronisiert. Offline
wird mit dem zuletzt erfolgreich synchronisierten Stand gearbeitet.

## PyKIM Suite

Start als Desktopanwendung:

```bash
pykim-guide
```

Alternativ im Browserfenster:

```bash
pykim-guide --browser
```

Die Suite bindet nur an `127.0.0.1`. Andere Geräte im Netzwerk können die
lokalen Aktionen nicht aufrufen.

### Bereiche der Suite

| Bereich | Funktion |
|---|---|
| **Setup** | Kursordner, Name, Python-Laufzeit und `.pykim-setup` |
| **Werkzeuge** | Ordner, IDE, Interpreter, Pyxel und Updates |
| **Übersicht** | Lernstand und Status der Aufgaben |
| **Aufgaben** | Aufgabenstellung, Editor, Tests, Optimierung und Dokubuch |
| **Beispiele** | mitgelieferte Programme starten, kopieren oder übernehmen |
| **Meine Projekte** | Python-, PyKIM- und Pyxel-Projekte verwalten |
| **Erweiterungen** | eigene Funktionen und Klassen wiederverwenden |
| **Cheatsheet** | kompakte Befehlsreferenz |
| **Skript** | Kapitelansicht mit seitlichem Inhaltsverzeichnis |
| **Pyxel** | Pyxel-Referenz, Beispiele und Übergang von PyKIM |
| **Python-Spielwiese** | normales Python mit Pyodide im Browser |

Der experimentelle Bereich **Abgabe** ist im aktuellen Schülerworkflow
ausgeblendet.

Codeblöcke im Skript können durch Autorenanweisungen gesteuert werden:

````markdown
@button:run
@button:copy
```python
print("Hallo")
```
````

`@button:run` ist nur für vollständige, freigegebene Programme vorgesehen.

## Kursordner und Setupdatei

Der Kursordner enthält Schülerdateien und bleibt von Inhaltsupdates getrennt:

```text
PyKIM-Kurs/
├── .pykim-course.json
├── .pykim/
│   ├── course.pykim-setup
│   ├── progress.json
│   └── backups/
├── Aufgaben/
│   ├── imperativ/
│   └── oop/
├── Projekte/
└── erweiterungen.py
```

Vorhandene Lösungen werden beim erneuten Setup nicht überschrieben.
Zurückgesetzte Aufgaben und Lernstände werden vorher unter `.pykim/backups`
gesichert.

### Format der Setupdatei

```json
{
  "format": "pykim-course-setup-v1",
  "name": "pykim-standardkurs.pykim-setup",
  "teacher": "Lehrkraft",
  "school": "OSZ KIM",
  "course": "PyKIM Standardkurs",
  "repository": "https://github.com/finalnode/PyKIM_Kurs.git",
  "branch": "main",
  "scripts_path": "Skripte",
  "assignments_path": "Aufgaben",
  "trainers_path": "Trainer"
}
```

Die Datei enthält bewusst keine Schlüssel, Zertifikate oder
Verschlüsselungsdaten. Sie ist in Version 0.3 eine Konfigurationsdatei und
nicht kryptografisch authentifiziert.

Erzeugen:

```bash
pykim-teacher setup \
  --teacher "Frau Beispiel" \
  --school "OSZ KIM" \
  --course "Python 11A" \
  --repository "https://github.com/finalnode/PyKIM_Kurs.git" \
  --branch main \
  --output ./setupdatei
```

Ohne importierte Setupdatei zeigt die Suite nur den rudimentären lokalen
Funktionsumfang. Skript, Aufgaben und Lernstand werden erst nach erfolgreicher
Synchronisation eingeblendet. Der Kursname erscheint danach im Header.

## Externes Kurs-Repository

Empfohlene Struktur:

```text
PyKIM_Kurs/
├── content.yml
├── .pykim/
│   └── trainer-hashes.json
├── Skripte/
│   ├── imperativ/
│   └── oop/
├── Aufgaben/
│   ├── imperativ/
│   └── oop/
└── Trainer/
    └── *.yml
```

`content.yml` listet explizit alle freigegebenen Kapitel, Aufgaben und
Trainerdateien. Die Suite lädt nicht beliebige Repository-Dateien. Sie ermittelt
zuerst den Commit des konfigurierten Branches und speichert den vollständigen
Stand danach versionsweise und atomar unter `~/.pykim/content/versions`.

Für Vorabstände kann eine Setupdatei beispielsweise auf den Branch `beta`
verweisen. Ein Wechsel des Branches erfolgt durch eine andere Setupdatei.

## Eigene Erweiterungen

Die Suite legt im Kursordner genau ein persönliches Modul an:

```text
erweiterungen.py
```

Schüler können dort selbst entwickelte Funktionen und Klassen speichern:

```python
def square(length):
    for _ in range(4):
        right(length)
        down(length)
```

Alle Erweiterungen importieren:

```python
from erweiterungen import *
```

Gezielt importieren:

```python
from erweiterungen import square
```

Die Suite prüft vor dem Hinzufügen:

- gültige Python-Syntax
- mindestens eine öffentliche Funktion oder Klasse
- keine doppelten Namen
- keine Beispielaufrufe oder sonstige Ausführung auf Modulebene

Vorhandene Definitionen können einzeln bearbeitet werden. Andere Funktionen
bleiben dabei unverändert. Der Kursordner wird beim Ausführen automatisch dem
Python-Suchpfad hinzugefügt, sodass der Import auch aus Aufgaben-Unterordnern
funktioniert.

Eine alte, kurzzeitig verwendete Paketstruktur wird bei Bedarf nach
`erweiterungen_altes_paket` verschoben und nicht gelöscht.

## Eigene Projekte und Pyxel-Ressourcen

Die Suite kennt drei Projektvorlagen:

- `empty`: normales Python-Projekt
- `pykim`: PyKIM-Projekt
- `pyxel`: Pyxel-Spiel mit Ressourcen

Beispiel:

```text
Projekte/mein_spiel/
├── main.py
├── projekt.json
└── ressourcen.pyxres
```

`projekt.json` speichert Projektname, Typ, Einstiegspunkt und Ressourcenpfad.
Pfade werden auf den jeweiligen Projektordner begrenzt.

`.pyxres` enthält Pyxel-Sprites, Tilemaps, Sounds und Musik. Die Suite startet
den offiziellen Editor sinngemäß mit:

```bash
python -m pyxel edit ressourcen.pyxres
```

Ein Pyxel-Projekt wird erst gestartet, nachdem seine konfigurierte
Ressourcendatei existiert. Das Arbeitsverzeichnis ist immer der Projektordner;
dadurch funktioniert `pyxel.load("ressourcen.pyxres")` portabel.

Mitgelieferte Beispiele bleiben unverändert. Zum Bearbeiten erstellt die Suite
eine persönliche Kopie unter `Projekte/beispiele`.

## IDE und Python-Laufzeit

Die Suite erkennt unterstützte Installationen und typische Systempfade für:

- Thonny
- Visual Studio Code
- PyCharm
- eigene IDE-Pfade

Die Auswahl wird sofort lokal gespeichert. Aufgaben und Beispiele zeigen den
Namen der ausgewählten IDE im Öffnen-Button.

### VS Code

Beim Öffnen ergänzt die Suite im Kursordner:

```text
.vscode/settings.json
.vscode/extensions.json
```

Der ausgewählte Python-Interpreter wird gesetzt und die offizielle
Python-Erweiterung empfohlen. Vorhandene Einstellungen bleiben erhalten.

### Thonny

PyKIM verwendet ein eigenes Profil unter `~/.pykim/thonny`, damit persönliche
Thonny-Einstellungen nicht überschrieben werden. Kursordner und ausgewählter
Interpreter werden gemeinsam gestartet.

### Interpreter

Die Suite sucht unter anderem nach:

- dem Interpreter der laufenden App
- System-Python-Installationen
- virtuellen Umgebungen
- pyenv-Installationen
- Conda-Umgebungen
- Windows-Python-Launcher-Einträgen
- Thonnys mitgeliefertem Python
- manuell ausgewählten Programmpfaden

Ein Kandidat wird auf Python-Version, PyKIM und Pyxel untersucht. PyKIM
benötigt Python 3.10 oder neuer.

Verwaltete Umgebungen liegen unter `~/.pykim/runtimes` und werden nicht in den
portablen Kursordner geschrieben. Dadurch werden plattformspezifische Pakete
nicht versehentlich über ein Netzlaufwerk synchronisiert.

## Updates

Die Suite prüft App und Lerninhalte getrennt im Hintergrund. Ein fehlendes Netz
blockiert den Start nicht.

### App-Update

- liest das neueste GitHub-Release
- vergleicht die semantische Versionsnummer
- wählt ein zur macOS-Architektur passendes DMG
- öffnet die Downloadseite
- ersetzt eine installierte App niemals ungefragt selbst

### Kursinhalte

- werden durch Setupdatei, Repository und Branch bestimmt
- werden commitgenau synchronisiert
- werden in einem Staging-Verzeichnis validiert
- werden erst danach atomar aktiviert
- verändern keine Schülerlösungen, Projekte oder Lernstände
- prüfen insbesondere Trainer gegen die Repository-Hashliste

Der ältere ZIP-basierte Inhaltsupdatekanal ist technisch noch vorhanden. Der
aktuelle Kursworkflow verwendet jedoch die direkte GitHub-Synchronisation.

## Speicherorte und Datenschutz

### Im Kursordner

- Schülername in `.pykim-course.json`
- Aufgabenlösungen
- Projekte
- `erweiterungen.py`
- Lernstand und Dokubuch in `.pykim/progress.json`
- Sicherungen unter `.pykim/backups`
- installierte Kurs-Setupdatei

### Lokal auf dem Rechner

- Suite-Konfiguration: `~/.pykim/config.json`
- synchronisierte Inhaltsversionen: `~/.pykim/content/versions`
- verwaltete Python-Laufzeiten: `~/.pykim/runtimes`
- eigenes Thonny-Profil: `~/.pykim/thonny`

Der Kursordner darf auf einem lokalen Laufwerk, USB-Datenträger oder
eingebundenen WebDAV-Laufwerk liegen. CalDAV ist ein Kalenderprotokoll und kein
Dateisystem. Gleichzeitiges Bearbeiten desselben synchronisierten Ordners auf
mehreren Geräten kann Konflikte erzeugen; vorgesehen ist nacheinander erfolgendes
Arbeiten in Schule und Zuhause.

Die Runtime-Diagnose enthält Plattform, Interpreter, Paketstatus und
Wheelhouse-Pfad, aber keinen Quellcode und keinen Lernstand.

## Python-Spielwiese

Die Spielwiese lädt Pyodide und führt normales Python im Browserkontext aus.
Beim ersten Laden ist eine Internetverbindung erforderlich. Das lokale
PyKIM-/Pyxel-Paket steht dort nicht automatisch zur Verfügung. Ein vollständiges
browserfähiges PyKIM benötigt ein eigenes Canvas-Backend oder die offizielle
Pyxel-WASM-Laufzeit.

## Installation und Entwicklung

Voraussetzung: Python 3.10 oder neuer.

### Bibliothek installieren

```bash
python -m pip install -e .
```

### Suite installieren

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[guide]'
pykim-guide
```

Unter Windows wird die Umgebung so aktiviert:

```powershell
.venv\Scripts\activate
```

### Tests

```bash
python -m pip install -e '.[test]'
pytest
```

Der reguläre Lauf prüft API, Weltlogik, Animation, Audio, Trainer,
Kursdateien, Erweiterungen, Projekte, Laufzeiten und Suite-Helfer.

NiceGUI-E2E-Test separat:

```bash
python -m pip install -e '.[e2e]'
pytest -m e2e
```

Manuelle Plattformtests stehen in `QUALITAETSSICHERUNG.md`.

### Test-Helfer

`pykim.testing` stellt bereit:

| Funktion | Zweck |
|---|---|
| `reset_world()` | gesamten Zustand zurücksetzen |
| `set_pixel_for_test(x, y, color)` | Testpixel setzen |
| `get_world_state()` | unveränderliche Weltmatrix lesen |
| `get_painted_pixels()` | alle nicht schwarzen Koordinaten lesen |
| `get_pending_tones()` | ausstehende MIDI-Noten lesen |
| `get_pending_audio_events()` | Noten und Beats lesen |

## Offline-Wheelhouse

```bash
python tools/build_wheelhouse.py
```

Das Ergebnis liegt unter `dist/wheelhouse`. Erkennt die Suite diesen Ordner,
installiert oder repariert sie PyKIM und Pyxel ohne Zugriff auf PyPI. Wheels
sind betriebssystem- und architekturabhängig und müssen auf passenden Runnern
gebaut werden.

## macOS-App und DMG

Eigenständige App inklusive Python, PyKIM, Pyxel, NiceGUI und Wheelhouse:

```bash
python tools/build_macos_app.py
open 'dist/macos/PyKIM Suite.app'
```

Schneller Wiederholungs-Build:

```bash
python tools/build_macos_app.py --skip-wheelhouse
```

DMG mit Verknüpfung zum Programme-Ordner:

```bash
python tools/build_macos_dmg.py
```

App und DMG gemeinsam neu bauen:

```bash
python tools/build_macos_dmg.py --rebuild-app
```

Der Dateiname enthält Version und Architektur, beispielsweise:

```text
PyKIM-Suite-0.3.0-macos-x86_64.dmg
```

Der Build muss auf derselben macOS-Architektur wie das Ziel erzeugt werden.
Intel (`x86_64`) und Apple Silicon (`arm64`) benötigen getrennte Builds. Ohne
Apple-Developer-Zertifikat wird die App nur ad hoc signiert und nicht
notarisiert.

## Grenzen und zurückgestellte Funktionen

- Die Setupdatei ist noch nicht signiert oder kryptografisch authentifiziert.
- Der verschlüsselte Moodle-Dateiexport ist experimentell und ausgeblendet.
- Der alte Zertifikats-/Schlüsselcode ist technische Vorarbeit, nicht Teil des
  stabilen 0.3-Workflows.
- Die automatische Übernahme einer bestandenen Aufgabenfunktion nach
  `erweiterungen.py` ist noch nicht implementiert; Erweiterungen werden derzeit
  manuell hinzugefügt.
- Die Browser-Spielwiese kann normales Python, aber noch kein lokales PyKIM.
- Windows- und Linux-Desktop-Bundles fehlen noch.
- macOS-Signierung und Notarisierung sind noch offen.
- Das Projekt befindet sich im Alpha-Stadium und ist noch kein abgesicherter
  flächendeckender Schul-Rollout.

## Lizenzierung

Der aktuelle Repository-Code steht unter der MIT License; siehe `LICENSE`.

Für die geplante Trennung des Kurs-Repositorys ist vorgesehen:

- Software und wiederverwendbarer Beispielcode: MIT
- Skript, Aufgabenstellungen und eigene didaktische Medien: CC BY-NC-SA 4.0
- Schülerlösungen: verbleiben bei den jeweiligen Schülerinnen und Schülern
- externe Medien: jeweilige Originallizenz

Die Inhaltslizenz ist erst verbindlich, wenn sie im Kurs-Repository mit einer
eigenen Lizenzdatei veröffentlicht wurde.

> **Concept by human. Crafted by human + AI.**  
> Konzept und pädagogische Verantwortung: Projektverantwortliche von PyKIM  
> KI-Unterstützung: OpenAI Codex
