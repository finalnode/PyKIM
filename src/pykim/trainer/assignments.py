"""Schülergerechte Aufgabenstellungen als installierbare strukturierte Daten."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Assignment:
    summary: str
    requirements: tuple[str, ...]
    difficulty: str = "mittel"


ASSIGNMENTS = {
    "quadrat-5": Assignment(
        "Zeichne mit KIM ein violettes Quadrat mit der Kantenlänge 5.",
        ("Beginne bei (50, 50).", "Zeichne alle vier Seiten vollständig.", "Kehre am Ende nach (50, 50) zurück.", "Zeichne keine zusätzlichen Pixel."),
        "einfach",
    ),
    "treppe-5": Assignment(
        "Zeichne ab (50, 50) eine violette Treppe mit fünf Stufen.",
        ("Jede Stufe ist 5 Pixel breit und 5 Pixel hoch.", "Die Treppe verläuft nach rechts und unten.", "KIM endet bei (75, 75).", "Verwende eine Schleife."),
        "einfach",
    ),
    "mehrere-pixel": Assignment(
        "Erzeuge neben KIM die Pixel MIA und LEO und bewege alle drei gemeinsam.",
        ("KIM zeichnet purple, MIA orange und LEO cyan.", "Nutze parallele und sequenzielle Bewegungsphasen.", "KIM endet bei (50, 30), MIA bei (30, 40), LEO bei (50, 25).", "Verstecke LEO erst nach seiner letzten Bewegung.", "Verwende world.parallel()."),
    ),
    "punktlinie-8": Assignment(
        "Zeichne ab (20, 20) eine regelmäßige violette Punktlinie aus acht Punkten.",
        ("Zwischen zwei Punkten bleibt genau ein schwarzer Pixel.", "Gehe nach jedem Punkt 2 Pixel nach rechts.", "KIM endet bei (36, 20).", "Verwende eine Schleife."),
        "einfach",
    ),
    "vier-quadrate": Assignment(
        "Zeichne ab (20, 20) vier benachbarte violette Quadrate.",
        ("Jedes Quadrat hat die Kantenlänge 5.", "Benachbarte Quadrate teilen eine Seite.", "KIM endet bei (40, 20).", "Nutze eine eigene Funktion und eine Schleife."),
    ),
    "schachbrett-8": Assignment(
        "Zeichne ab (20, 20) ein 8-mal-8-Schachbrett aus einzelnen Pixeln.",
        ("Das linke obere Feld ist purple.", "Die Farben wechseln zwischen purple und orange.", "Nutze zwei verschachtelte Schleifen.", "Wähle die Farbe mit if und dem Modulo-Operator %.", "Kapsle ein Feld in einer Funktion."),
    ),
    "tonleiter-c-dur": Assignment(
        "Spiele eine vollständige C-Dur-Tonleiter aufwärts.",
        ("Spiele C4, D4, E4, F4, G4, A4, B4 und C5.", "Jeder Ton dauert einen Beat.", "Speichere die Noten in einer Liste und verwende eine Schleife."),
        "einfach",
    ),
    "rhythmus-motiv": Assignment(
        "Komponiere ein kurzes Tonmotiv und spiele es zweimal.",
        ("Spiele C4 (1 Beat), E4 (1), G4 (2) und eine Pause (1).", "Definiere für das Motiv eine Funktion.", "Wiederhole die Funktion mit einer Schleife zweimal."),
    ),
    "farben-melodie": Assignment(
        "Male vier Farbfelder und übersetze ihre Farben anschließend in Töne.",
        ("Male ab (20, 20) red, green, cyan und yellow.", "Lies die Felder mit get_color().", "Ordne C4, E4, G4 und C5 zu; C5 dauert zwei Beats.", "Verwende eine Schleife und if/elif."),
    ),
    "interaktive-steuerung": Assignment(
        "Steuere KIM mit den vier Pfeiltasten.",
        ("Definiere update() für Tasten und Bewegung.", "Verhindere das Verlassen der Welt.", "Definiere draw(), leere mit world.cls() und zeichne KIM.", "Starte mit world.run(update, draw, check=...)."),
    ),
    "musik-pixel-klasse": Assignment(
        "Entwickle eine eigene Klasse für musikalische Pixel.",
        ("Definiere class MusikPixel(Pixel).", "Ergänze color und note und rufe super().__init__() auf.", "Überschreibe update() und draw().", "Erzeuge mindestens zwei Instanzen mit world.spawn()."),
        "fortgeschritten",
    ),
}


def get_assignment(name: str) -> Assignment:
    try:
        return ASSIGNMENTS[name]
    except KeyError:
        raise ValueError(f"Für {name!r} fehlt die Aufgabenstellung.") from None
