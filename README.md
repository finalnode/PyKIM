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

Der normale Testlauf prüft die API, Weltlogik, Trainer, Kursdateien und
Suite-Helfer. Der echte NiceGUI-Navigationslauf ist bewusst separat, weil er
zusätzliche Desktop-/Browser-Abhängigkeiten benötigt:

```bash
python -m pip install -e '.[e2e]'
pytest -m e2e
```

Die ergänzende manuelle Prüfmatrix für Windows, Thonny und synchronisierte
Netzlaufwerke steht in `QUALITAETSSICHERUNG.md`.

### Eigenständige macOS-App

Der erste gebündelte Release-Weg konzentriert sich auf macOS. Der Build enthält
Python, PyKIM, Pyxel, NiceGUI, die Trainer-Aufgaben, Skripte, Beispiele und ein
Offline-Wheelhouse. Auf dem Schülergerät ist deshalb keine eigene
Python-Installation nötig.

```bash
python tools/build_macos_app.py
open 'dist/macos/PyKIM Suite.app'
```

Für schnelle Wiederholungs-Builds kann das bereits erzeugte Wheelhouse erhalten
bleiben:

```bash
python tools/build_macos_app.py --skip-wheelhouse
```

Aus dem fertigen App-Bundle entsteht ein Intel-DMG mit einer Verknüpfung zum
Programme-Ordner:

```bash
python tools/build_macos_dmg.py
```

Mit `--rebuild-app` werden App, Wheelhouse, Icon und DMG in einem Durchlauf neu
erzeugt. Das Ergebnis trägt Version und Architektur im Dateinamen.

Der Build muss auf macOS und für dieselbe Prozessorarchitektur wie das Zielgerät
erzeugt werden. Der derzeit lokal erzeugte Build ist `x86_64`. Für Apple Silicon
wird später auf einem Apple-Silicon-Mac ein eigener `arm64`-Build erstellt.
Ohne Apple-Developer-Zertifikat ist die App nur ad-hoc signiert und noch nicht
notarisiert; das ist für lokale Entwicklung geeignet, aber noch kein fertiger
Schul-Rollout.

## Lokales Begleitheft und Kursordner

Der optionale NiceGUI-Prototyp bündelt Setup, Aufgabenübersicht, einzelne
Trainer-Testfälle, Cheatsheet, Dokubuch sowie PyKIM- und Pyxel-Dokumentation:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e '.[guide]'
pykim-guide
```

Standardmäßig öffnet sich das Lernstudio als eigenes Desktopfenster. Falls der
native Fenstermodus auf einem Rechner nicht funktioniert oder das Begleitheft
bewusst in einem Browser laufen soll, steht derselbe Funktionsumfang so bereit:

```bash
pykim-guide --browser
```

Eine isolierte Umgebung verhindert Konflikte mit älteren FastAPI-, Pydantic-
oder NiceGUI-Versionen anderer Projekte. PyKIM benötigt Python 3.10 oder
neuer; der Setup-Systemcheck weist auf eine zu alte Python-Version hin.

Das Begleitheft läuft technisch weiterhin ausschließlich lokal. Im Setup kann ein beliebiger
Kursordner gewählt werden, auch auf einem als Laufwerk eingebundenen
WebDAV-Speicher. Technisch ist WebDAV für Dateien zuständig; CalDAV ist das
darauf aufbauende Kalenderprotokoll und eignet sich nicht selbst als
Dateisystem.

Die Suite bindet ausschließlich an `127.0.0.1`. Andere Geräte im Schul- oder
Heimnetz können ihre lokalen Start-, Installations- und Updateaktionen daher
nicht aufrufen.

### Verschlüsselte Moodle-Dateiabgaben (experimentell, vorerst zurückgestellt)

Diese technische Grundlage ist vorhanden, gehört aber noch nicht zum
stabilisierten Schüler-Workflow. Zuerst werden Skript, Aufgaben und lokales
Arbeiten gefestigt. Moodle wird ohne Plugin ausschließlich als Datei-Transport
verwendet. Die Lehrkraft erzeugt einmalig ein öffentliches Kurszertifikat und
einen passwortgeschützten privaten Schlüssel:

```bash
pykim-teacher keygen \
  --teacher "Frau Beispiel" \
  --school "OSZ KIM" \
  --course "Informatik 11A" \
  --output ./kurs-schluessel
```

Die `.pykim-cert`-Datei wird im Lernraum bereitgestellt. Der private
`.pykim-private-key` verbleibt ausschließlich bei der Lehrkraft und sollte
zusätzlich gesichert werden. Schüler importieren das Zertifikat auf der
Abgabeseite des Lernstudios. Der verschlüsselte Export erscheint im Unterordner
`abgaben` des Kursordners und kann als normale Datei in Moodle hochgeladen
werden.

Ein heruntergeladener Moodle-Abgabeordner wird lokal ausgewertet:

```bash
pykim-teacher report ./moodle-download \
  --key ./kurs-schluessel/informatik-11a.pykim-private-key \
  --output ./bericht
```

Das Werkzeug fragt das Schlüsselpasswort verdeckt ab und erzeugt einen HTML-
Bericht sowie eine CSV-Leistungsübersicht. Es berechnet alle Codefingerprints
erneut. Original-, formatierter und AST-Strukturhash dienen nur als
Ähnlichkeitshinweise und niemals als automatischer Plagiatsnachweis.

Das Setup legt eine gegliederte Aufgabenstruktur an und überschreibt niemals
vorhandene Lösungen. Trainerläufe und Dokubuch-Einträge werden portabel unter
`.pykim/progress.json` im Kursordner gespeichert. Wer zwischen Schule und
Zuhause wechselt, bindet denselben Ordner ein und wählt ihn einmal im Setup.
Alternativ kann der Pfad gesetzt werden:

```bash
export PYKIM_COURSE_DIR="/Pfad/zum/eingebundenen/PyKIM-Kurs"
```

Bei gleichzeitigem Bearbeiten auf mehreren Geräten können
Synchronisationskonflikte entstehen. Der Prototyp ist für das nacheinander
Weiterarbeiten auf Schule- und Heimgerät ausgelegt.

### Suite-Werkzeuge

Der Tab **Setup** erkennt Python, PyKIM, Pyxel, Thonny und Visual Studio Code
und verweist bei fehlenden IDEs auf die offiziellen Installationsseiten. Im
Tab **Werkzeuge** kann der Kursordner mit der erkannten IDE geöffnet werden.

Schülerprogramme werden nicht mehr implizit mit irgendeinem globalen Python
gestartet. Die Suite prüft gefundene Interpreter auf Python-Version, PyKIM und
Pyxel und speichert eine gemeinsame Schüler-Laufzeit. Dieselbe Laufzeit gilt
für die Ausführen-Schaltflächen und die externe IDE. Verwaltete Umgebungen
liegen lokal unter `~/.pykim/runtimes`; sie werden deshalb nicht versehentlich
über WebDAV zwischen verschiedenen Betriebssystemen synchronisiert.

Beim Öffnen eines Kursordners in VS Code ergänzt die Suite dessen lokale
`.vscode/settings.json` um den ausgewählten Interpreter und empfiehlt die
offizielle Python-Erweiterung. Andere vorhandene Workspace-Einstellungen
bleiben erhalten. Thonny wird mit dem Kursordner gestartet; die automatische,
plattformübergreifende Übergabe des Interpreters verwendet ein eigenes
PyKIM-Thonny-Profil unter `~/.pykim/thonny`. Persönliche Thonny-Einstellungen
werden dadurch nicht überschrieben.

### App- und Inhaltsupdates

Beim Öffnen prüft die Suite beide Updatekanäle im Hintergrund. Ein fehlendes
Netz blockiert den Start nicht.

- **App:** Die Suite liest das neueste GitHub-Release und bietet das zur
  Prozessorarchitektur passende DMG an. Eine installierte App ersetzt sich
  niemals selbst und lädt keine Entwicklungsversion aus `main`.
- **Lerninhalte:** Skripte und Aufgaben können als eigenes ZIP aktualisiert
  werden. Paket- und Dateiprüfsummen werden vor der atomaren Aktivierung
  kontrolliert. Schülercode, Projekte und `.pykim/progress.json` liegen
  außerhalb des Inhaltsverzeichnisses und bleiben unverändert.

Aktive Downloads liegen unter `~/.pykim/content/versions`. Ist ein Paket
unvollständig oder beschädigt, verwendet die Suite weiterhin die mit der App
ausgelieferten Inhalte. Ein Releasepaket wird so erzeugt:

```bash
python tools/build_content_package.py --version 2026.08.1
```

Dabei entstehen `dist/content/pykim-content-<version>.zip` sowie das zugehörige
`content-manifest.json`. Das ZIP wird als GitHub-Release-Asset unter dem im
Manifest angegebenen Tag veröffentlicht; das Manifest selbst liegt im
Repository und dient der Startprüfung.

### Offline-Laufzeit

Die Offline-Pakete für das aktuelle Betriebssystem und die aktuelle
Prozessorarchitektur werden mit folgendem Befehl gebaut:

```bash
python tools/build_wheelhouse.py
```

Das Ergebnis liegt unter `dist/wheelhouse`. Erkennt die Suite diesen Ordner,
installiert und repariert sie PyKIM und Pyxel mit `--no-index`; ein Zugriff auf
PyPI findet dann nicht statt. Windows-, macOS- und Linux-Wheels müssen später
jeweils auf der passenden Plattform durch die Build-Matrix erzeugt werden.

Im Setup kann eine verwaltete Kursumgebung repariert und eine datensparsame
Runtime-Diagnose kopiert werden. Die Diagnose enthält Plattform, Interpreter,
Paketstatus und Wheelhouse-Pfad, aber weder Quellcode noch Lernstand.

Die Suite kann außerdem die Versionsnummer des GitHub-main-Branches prüfen.
Eine Installation der Entwicklungsversion erfolgt nur nach einer expliziten
Bestätigung und verändert keine Dateien im Kursordner.

Im Bereich **Meine Projekte** erzeugt die Suite vollständige Projektordner. Ein
Pyxel-Projekt sieht beispielsweise so aus:

```text
Projekte/mein_spiel/
├── main.py
├── projekt.json
└── ressourcen.pyxres
```

Eine `.pyxres`-Datei enthält Sprites, Tilemaps, Sounds und Musik. Der Editor
wird direkt an der Projektkarte geöffnet. Beim ersten Speichern legt Pyxel die
Datei an. Projektstart und Editor verwenden dieselbe in der Suite ausgewählte
Python-Laufzeit. `main.py` wird mit dem Projektordner als Arbeitsverzeichnis
gestartet, weshalb `pyxel.load("ressourcen.pyxres")` portabel funktioniert.

Der frühere Ordner `eigene_projekte/` wird aus Kompatibilitätsgründen nicht
gelöscht oder verschoben. Neue Projekte und bearbeitbare Beispielkopien liegen
unter `Projekte/`.

Der Tab **Python im Browser** enthält eine erste Pyodide-Spielwiese. Sie lädt
Python als WebAssembly im Browser und führt normalen Python-Code ohne lokale
Datei aus. Dafür ist beim ersten Laden eine Internetverbindung erforderlich.
Pyxel selbst wird dort nicht mit `micropip` installiert; ein späteres
browserfähiges PyKIM benötigt ein eigenes Canvas-Backend beziehungsweise die
offizielle Pyxel-WASM-Laufzeit.

## Erstes Programm

```python
from pykim import *

set_position(20, 20)
speed(30)
set_color("purple")
paint()

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

Eine Farbspur beginnen oder beenden und Pixel lesen:

```python
paint("purple")      # färbt hier und schaltet die Spur ein
right(20)            # malt jeden besuchten Pixel
paint_stop()
paint("orange")      # nur diese Position färben:
paint_stop()         # Spur sofort wieder ausschalten
get_color()          # aktueller Pixel
get_color("right")   # unmittelbarer Nachbar
get_color(100, 50)   # beliebige Position
```

`paint()` färbt sofort den aktuellen Pixel und danach jeden Pixel, über
den Kim sich bewegt. `paint_stop()` beendet die Spur. Ohne vorherige
Farbauswahl wird Weiß verwendet:

```python
paint()
right(20)
paint_stop()

paint("orange")
down(10)
paint_stop()
```

Die bisherigen Namen `paint_start()` und `paint_path()` funktionieren als
Kompatibilitätsaliase für `paint()`, werden aber nicht mehr aktiv gelehrt.

`get_color()` gibt immer einen lesbaren, kanonischen Farbnamen zurück. Die 16
Farben sind: `black`, `navy`, `purple`, `green`, `brown`, `dark_blue`,
`light_blue`, `white`, `red`, `orange`, `yellow`, `lime`, `cyan`, `gray`,
`pink` und `peach`.

### Objektweg und mehrere Pixel

Die freien Befehle steuern den mitgelieferten Pixel `kim`. Dieselbe Bewegung
kann deshalb auch objektorientiert geschrieben werden:

```python
from pykim import kim, world

kim.position = (20, 20)
kim.paint("purple")
kim.right(10)
kim.paint_stop()

world.speed(30)
world.run()
```

Beide Schreibweisen verändern dieselbe Welt. Für mehrere Figuren erzeugt die
Welt zusätzliche Pixel:

```python
from pykim import kim, world

kim.position = (20, 20)
kim.paint("purple")
kim.right(10)
kim.paint_stop()

mia = world.new_pixel("MIA", x=20, y=30)
mia.paint("orange")
mia.right(10)
mia.paint_stop()

leo = world.new_pixel("LEO", x=20, y=40)
leo.paint("cyan")
leo.right(10)
leo.paint_stop()
leo.hide()  # Spur behalten, Figur verstecken

world.run()
```

Ein vollständiges Beispiel steht in `src/pykim/examples/mehrere_pixel.py`.

Jeder Pixel kann unabhängig versteckt und wieder gezeigt werden:

```python
mia.hide()
mia.show()
```

Für KIM funktionieren zusätzlich die freien Kurzformen `hide()` und `show()`.
Das Verstecken entfernt weder die gemalte Spur noch die aktuelle Position.

Im Objektweg werden Positionen über Eigenschaften gelesen und gesetzt:

```python
print(kim.x, kim.y)
print(kim.position)
kim.position = (40, 30)
```

Töne können sowohl von einer Figur als auch direkt von der Welt ausgelöst
werden. Beide Wege verwenden dieselbe Tonwarteschlange:

```python
kim.play_tone("C4")
world.play_tone("E4", beats=2)
world.play_pause()
```

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

Das Beispiel `src/pykim/examples/mehrere_pixel.py` wird mit
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
    if world.btn("right") and kim.x < world.width - 1:
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
        self.world.pset(self.x, self.y, "purple")

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

Weitere vollständige Programme stehen im Paketordner `src/pykim/examples`
und in der Beispielsektion des Lernstudios.
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
`src/pykim/examples/quadrat_aufgabe.py`.

Eine zweite Aufgabe fordert eine Treppe aus fünf jeweils 5 Pixel breiten und
hohen Stufen. Dabei wird auch geprüft, ob die wiederholten Bewegungen mit einer
Schleife kurz formuliert wurden:

```python
set_position(50, 50)
paint("purple")
for _ in range(5):
    right(5)
    down(5)
run(check="treppe-5")
```

`run(check=...)` prüft zuerst die Zeichnung und erkennt dabei auch die
verwendete Schleife. Anschließend öffnet es wie gewohnt das Pyxel-Fenster. Das
vollständige Beispiel steht in `src/pykim/examples/treppe_aufgabe.py`.

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
