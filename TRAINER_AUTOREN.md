# Aufgaben für den PyKIM-Trainer schreiben

Trainerdateien beschreiben nur, **was** eine richtige Lösung ausmacht. Der
`ExerciseBuilder` übernimmt Weltzugriff, Farbumwandlung, Audiovergleich,
Quellcodeanalyse und den Aufbau der deutschen Rückmeldung.

## Autorenwerkzeuge in der Suite

Unter **Werkzeuge → Trainer-Autorenwerkzeuge** zeigt die Suite für jede
registrierte Aufgabe:

- die verwendeten Prüfbausteine,
- Erfolgs-, Fehler- und Tipptexte aus Sicht der Lernenden,
- redaktionelle Warnungen,
- einen stabilen Definitions-Hash.

Darunter erzeugt ein kleiner Bausteineditor aus Kennung, Titel, Prüfungen und
optionaler Codeschwelle eine vollständige Trainerdatei und das zugehörige
Aufgaben-Markdown. Vorhandene Aufgaben können als Ausgangspunkt geladen werden.
Beide Texte bleiben bewusst normaler, editierbarer Quelltext: Positionen,
Farben und besondere Fachwerte lassen sich direkt und nachvollziehbar anpassen.

Die Suite validiert Python-Syntax, Kennung, `EXERCISE`, Markdown-Titel,
Schwierigkeitsgrad und Anforderungen fortlaufend. Beim Speichern entstehen
immer beide Dateien unter `.pykim/author_drafts/` im Kursordner. Vorhandene
Entwürfe werden nur nach bewusst gesetztem Haken überschrieben. Installierte
Paketdateien bleiben dadurch unverändert.

Der Definitions-Hash ändert sich, sobald sich Titel, Reihenfolge, Art oder
Feedback der Prüfungen ändern. Er identifiziert damit eine konkrete
Testdefinition, ersetzt aber keine Versionsverwaltung.

## Kleinste Aufgabe

```python
from pykim.trainer import ExerciseBuilder

EXERCISE = (
    ExerciseBuilder("roter-punkt", "Ein roter Punkt")
    .expect_pixels({(20, 20): "red"})
    .expect_position((20, 20))
    .build()
)
```

Farben werden immer mit Namen angegeben. Interne Pyxel-Indizes wie `8` oder
`12` gehören nicht in Trainerdateien.

## Eigene Rückmeldungen

Jede Regel besitzt brauchbare Standardtexte. Für eine konkrete Aufgabe können
`success`, `failure` und `hint` überschrieben werden:

```python
.require_loop(
    success="Du verwendest eine Schleife für alle acht Punkte.",
    failure="Die Wiederholungen sind noch einzeln notiert.",
    hint="Setze paint() und right(2) in eine for-Schleife.",
)
```

## Welt und Figuren prüfen

```python
.expect_pixels({
    (20, 20): "purple",
    (21, 20): "orange",
})
.expect_position((30, 20))                 # standardmäßig KIM
.expect_positions({"KIM": (30, 20), "MIA": (40, 20)})
.expect_pixel_names(("KIM", "MIA"))
.expect_visibility("MIA", False)
```

`expect_pixels()` prüft standardmäßig das exakte Bild einschließlich Farben
und zusätzlicher Pixel. Eine reine Koordinatenmenge ignoriert die Farben:

```python
.expect_pixels({(20, 20), (21, 20)}, exact=False)
.expect_no_extra_pixels({(20, 20), (21, 20)})
.expect_pixel_count(2, success="Genau zwei Pixel sind angemalt.")
```

Für ein geschlossenes Quadrat gibt es eine fertige Geometrieprüfung:

```python
.expect_square(start=(50, 50), side=5)
```

## Töne und Pausen prüfen

Audioereignisse bestehen aus `(Note, beats)`. `None` steht lesbar für eine
Pause:

```python
.expect_audio([
    ("C4", 1),
    ("E4", 1),
    ("G4", 2),
    (None, 1),
])
```

MIDI-Zahlen sind möglich, Notennamen sind in Aufgaben aber meist verständlicher.

## Kontrollstrukturen prüfen

```python
.require_loop()
.require_nested_loop()
.require_condition()
.require_condition(calls=("get_color",))
.require_function()
.require_function("update")
.require_calls("cls", "run")
.require_parallel()
```

## Eigene Klassen prüfen

```python
.require_class("MusikPixel", base="Pixel")
.require_super_init("MusikPixel")
.require_methods("MusikPixel", "update", "draw")
.require_calls("spawn")
```

## Optimierung ergänzen

### Codeschwelle in Prozent

Wenn eine Aufgabe optimal in beispielsweise zehn relevanten Codezeilen lösbar
ist, wird die Schwelle direkt angegeben:

```python
.optimize_lines(optimal=10)
```

Gezählt werden alle nichtleeren Zeilen außer reinen Kommentarzeilen. Leerzeilen
und Kommentare verschlechtern die Bewertung also nicht. Die Punktzahl lautet:

```text
min(100, optimal / tatsächlich × 100)
```

Eine Lösung mit 10 Zeilen erhält `100 %`, eine mit 15 Zeilen `67 %` und eine
mit 20 Zeilen `50 %`. Kürzere korrekte Lösungen bleiben bei `100 %`. Die
fachlichen Prüfungen entscheiden weiterhin unabhängig davon, ob die Aufgabe
korrekt gelöst wurde.

Beispiel:

```python
EXERCISE = (
    ExerciseBuilder("tonleiter", "Tonleiter")
    .expect_audio(NOTES)
    .require_loop()
    .optimize_lines(optimal=5)
    .build()
)
```

### Eigene Optimierungsfunktion

Eine vorhandene Optimierungsfunktion kann separat angehängt werden:

```python
from pykim.trainer.optimization import evaluate_checkerboard

EXERCISE = (
    ExerciseBuilder("schachbrett-8", "Schachbrett")
    .expect_pixels(EXPECTED)
    .require_nested_loop()
    .optimize_with(evaluate_checkerboard)
    .build()
)
```

## Ungewöhnliche Sonderprüfung

Wenn keine fertige Regel passt, bleibt ein ausdrücklich beschrifteter Ausweg:

```python
.add_check(
    lambda source: meine_pruefung(),
    success="Das besondere Ziel ist erreicht.",
    failure="Das besondere Ziel fehlt noch.",
    hint="Prüfe ...",
)
```

Für dynamische Meldungen existiert zusätzlich `add_result()`. Neue allgemein
nützliche Prüfungen sollten jedoch bevorzugt einmal im Builder ergänzt werden,
statt technische Logik in mehreren Aufgaben zu duplizieren.

## Aufgabe verfügbar machen

Die Datei muss lediglich in `src/pykim/trainer/exercises/` liegen und eine
Variable namens `EXERCISE` exportieren. Die Registry entdeckt sie beim Start
automatisch; eine Importliste muss nicht gepflegt werden. Die Registry prüft
Kennung, Titel, Prüfbausteine und Definitions-Hash beim Laden.

Die Aufgabenstellung liegt als gleichnamige Markdown-Datei unter
`src/pykim/guide/Aufgaben/imperativ/` oder `Aufgaben/oop/`. Diese Datei ist die
einzige Quelle für den Aufgabentext und den Schwierigkeitsgrad; eine gemeinsame
`AUFGABEN.md` muss nicht zusätzlich gepflegt werden.
