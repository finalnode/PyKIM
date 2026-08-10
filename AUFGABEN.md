# PyKIM-Aufgaben

Diese Datei enthält alle Aufgabenstellungen, die der lokale PyKIM-Trainer
prüfen kann. Eine Lösung wird am Ende mit der angegebenen Aufgabenkennung
gestartet:

```python
run(check="aufgabenkennung")
```

Bei Verwendung der Objekt-API lautet der Aufruf entsprechend
`world.run(check="aufgabenkennung")`.

## 1. Quadrat mit Kantenlänge 5

**Aufgabenkennung:** `quadrat-5`  
**Schwierigkeit:** einfach  
**Codeschwelle:** 10 relevante Zeilen = 100 %

Zeichne mit KIM ein violettes Quadrat mit der Kantenlänge 5.

- KIM beginnt bei `(50, 50)`.
- `(50, 50)` muss eine Ecke des Quadrats sein.
- Alle vier Seiten müssen vollständig gezeichnet werden.
- Innerhalb und außerhalb des Randes dürfen keine zusätzlichen Pixel liegen.
- KIM kehrt am Ende nach `(50, 50)` zurück.

## 2. Treppe mit fünf Stufen

**Aufgabenkennung:** `treppe-5`  
**Schwierigkeit:** einfach  
**Codeschwelle:** 8 relevante Zeilen = 100 %

Zeichne ab `(50, 50)` eine violette Treppe mit fünf Stufen.

- Jede Stufe ist 5 Pixel breit und 5 Pixel hoch.
- Die Treppe verläuft nach rechts und unten.
- KIM steht am Ende bei `(75, 75)`.
- Verwende eine Schleife, damit sich die Bewegungsbefehle nicht wiederholen.

## 3. Drei Pixel gemeinsam bewegen

**Aufgabenkennung:** `mehrere-pixel`  
**Schwierigkeit:** mittel  
**Codeschwelle:** 22 relevante Zeilen = 100 %

Erzeuge neben KIM die Pixel `MIA` und `LEO` und zeichne das in
`src/pykim/examples/mehrere_pixel.py` beschriebene Muster.

- KIM beginnt bei `(20, 20)` und zeichnet `purple`.
- MIA beginnt bei `(60, 20)` und zeichnet `orange`.
- LEO beginnt bei `(40, 60)` und zeichnet `cyan`.
- Nutze sowohl parallele als auch sequenzielle Bewegungsphasen.
- KIM endet bei `(50, 30)`, MIA bei `(30, 40)` und LEO bei `(50, 25)`.
- Verstecke LEO erst nach seiner letzten Bewegung; seine Spur bleibt sichtbar.
- Verwende mindestens einen `with world.parallel():`-Block.

## 4. Punktlinie mit acht Punkten

**Aufgabenkennung:** `punktlinie-8`  
**Schwierigkeit:** einfach  
**Übernommen aus:** Turtle, Kapitel 2, Aufgabe 2.5  
**Codeschwelle:** 9 relevante Zeilen = 100 %

Zeichne eine regelmäßige violette Punktlinie.

- KIM beginnt bei `(20, 20)`.
- Male insgesamt acht einzelne violette Pixel.
- Zwischen zwei Punkten liegt jeweils genau ein schwarzer Pixel.
- Bewege KIM nach jedem gemalten Punkt 2 Pixel nach rechts.
- KIM endet bei `(36, 20)`.
- Verwende für die acht Wiederholungen eine Schleife.

## 5. Vier Quadrate in einer Reihe

**Aufgabenkennung:** `vier-quadrate`  
**Schwierigkeit:** mittel  
**Übernommen aus:** Turtle, Kapitel 2, Aufgabe 2.4  
**Codeschwelle:** 14 relevante Zeilen = 100 %

Zeichne ab `(20, 20)` vier benachbarte violette Quadrate.

- Jedes Quadrat besitzt die Kantenlänge 5.
- Benachbarte Quadrate teilen sich jeweils eine senkrechte Seite.
- Die gesamte Figur reicht von `x = 20` bis `x = 40` und von `y = 20` bis
  `y = 25`.
- KIM endet bei `(40, 20)`.
- Definiere eine eigene Funktion für ein einzelnes Quadrat.
- Wiederhole diese Funktion mit einer Schleife viermal.

## 6. Zweifarbiges 8-mal-8-Schachbrett

**Aufgabenkennung:** `schachbrett-8`  
**Schwierigkeit:** mittel  
**Übernommen aus:** Turtle, Kapitel 3, Aufgabe 3.4  
**Codeschwelle:** 15 relevante Zeilen = 100 %

Zeichne ein Schachbrett aus 64 einzelnen Pixeln.

- Die linke obere Ecke liegt bei `(20, 20)`.
- Das Brett ist 8 Pixel breit und 8 Pixel hoch.
- Das linke obere Feld ist `purple`.
- Die Felder wechseln zwischen `purple` und `orange`.
- Definiere eine Funktion zum Zeichnen eines einzelnen Feldes.
- Durchlaufe Zeilen und Spalten mit zwei verschachtelten Schleifen.
- Wähle die Farbe mit einer `if`-Bedingung. Die Summe aus relativer x- und
  y-Koordinate eignet sich zusammen mit dem Modulo-Operator `%`.
- Versuche, mit höchstens 20 nichtleeren Codezeilen ohne Kommentare
  auszukommen.

## 7. C-Dur-Tonleiter

**Aufgabenkennung:** `tonleiter-c-dur`  
**Schwierigkeit:** einfach  
**Codeschwelle:** 6 relevante Zeilen = 100 %

Spiele eine vollständige C-Dur-Tonleiter aufwärts.

- Spiele nacheinander `C4`, `D4`, `E4`, `F4`, `G4`, `A4`, `B4` und `C5`.
- Jeder Ton dauert einen Beat.
- Speichere die Noten in einer Liste.
- Spiele die Liste mit einer Schleife ab.

## 8. Rhythmisches Tonmotiv

**Aufgabenkennung:** `rhythmus-motiv`  
**Schwierigkeit:** mittel  
**Codeschwelle:** 10 relevante Zeilen = 100 %

Komponiere ein kurzes Motiv und spiele es zweimal.

- Das Motiv besteht aus `C4` für einen Beat, `E4` für einen Beat und `G4`
  für zwei Beats.
- Danach folgt eine Pause von einem Beat.
- Definiere für das Motiv eine eigene Funktion.
- Wiederhole die Funktion zweimal mit einer Schleife.

## 9. Melodie aus Farben

**Aufgabenkennung:** `farben-melodie`  
**Schwierigkeit:** mittel  
**Codeschwelle:** 20 relevante Zeilen = 100 %

Male vier Farbfelder und übersetze ihre Farben anschließend in Töne.

- Die Felder liegen von `(20, 20)` bis `(23, 20)`.
- Ihre Reihenfolge lautet `red`, `green`, `cyan`, `yellow`.
- Gehe anschließend mit einer Schleife über die vier Felder.
- Lies jedes Feld mit `get_color()`.
- Spiele mit einer `if`-/`elif`-Bedingung für `red` den Ton `C4`, für
  `green` den Ton `E4`, für `cyan` den Ton `G4` und für `yellow` den Ton
  `C5` mit zwei Beats.

## 10. Interaktive Steuerung

**Aufgabenkennung:** `interaktive-steuerung`  
**Schwierigkeit:** mittel  
**Lernziel:** Übergang zur Pyxel-Spielschleife  
**Codeschwelle:** 17 relevante Zeilen = 100 %

Steuere KIM mit den vier Pfeiltasten.

- Definiere eine Funktion `update()` für Tasten und Bewegung.
- Frage die Tasten mit `world.btn("left")`, `"right"`, `"up"` und `"down"`
  ab.
- Verhindere, dass KIM die Welt verlässt.
- Definiere eine Funktion `draw()` für die Darstellung.
- Leere dort das Bild mit `world.cls()` und zeichne KIM mit `kim.draw()`.
- Starte das Programm mit `world.run(update, draw, check="interaktive-steuerung")`.

## 11. Eigene MusikPixel-Klasse

**Aufgabenkennung:** `musik-pixel-klasse`  
**Schwierigkeit:** fortgeschritten  
**Lernziel:** Vererbung, Konstruktoren und Polymorphie  
**Codeschwelle:** 22 relevante Zeilen = 100 %

Entwickle eine eigene Klasse für musikalische Pixel.

- Definiere `class MusikPixel(Pixel):`.
- Ergänze in `__init__()` die Attribute `color` und `note`.
- Rufe den Konstruktor der Basisklasse mit `super().__init__(...)` auf.
- Überschreibe `update()`. Bei einem Druck auf die Leertaste soll der Pixel
  seine eigene Note spielen.
- Überschreibe `draw()` und zeichne den Pixel mit seiner eigenen Farbe.
- Erzeuge mindestens zwei MusikPixel mit verschiedenen Attributen über
  `world.spawn(MusikPixel, ...)`.
- Zeichne die Instanzen in `draw()` und starte die interaktive Welt.

## Nicht übernommene Archivbereiche

Aufgaben zu beliebigen Winkeln, Kreisen, GUI-Elementen, Maus- und
Tastaturereignissen, Zufallsbildern, Texteingaben und Rekursion wurden nicht in
den Trainer aufgenommen. Dafür fehlen PyKIM derzeit entweder die passenden
Zeichenoperationen oder ein eindeutig reproduzierbarer Weltzustand für eine
faire automatische Prüfung.

## Musterlösungen

Ausführbare Musterlösungen werden im Paketordner `src/pykim/examples` mitgeliefert:

- `quadrat_aufgabe.py`
- `treppe_aufgabe.py`
- `mehrere_pixel.py`
- `punktlinie_aufgabe.py`
- `vier_quadrate_aufgabe.py`
- `schachbrett_aufgabe.py`
- `tonleiter_aufgabe.py`
- `rhythmus_aufgabe.py`
- `farben_melodie_aufgabe.py`
- `interaktive_steuerung_aufgabe.py`
- `musik_pixel_aufgabe.py`

Jede Musterlösung ruft den Trainer mit ihrer Aufgabenkennung auf und sollte
alle fachlichen Prüfungen und eine Codebewertung von 100 % erreichen. Für die
Codeschwelle zählen nichtleere Zeilen außer reinen Kommentarzeilen. Kürzere
korrekte Lösungen bleiben ebenfalls bei 100 %; längere Lösungen werden im
Verhältnis zur angegebenen Schwelle bewertet.
