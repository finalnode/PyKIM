"""PyKIM: eine kleine, testbare Lernumgebung auf Basis von Pyxel."""

import re
from collections import deque

__version__ = "0.1.0"

WIDTH = 160
HEIGHT = 120
DEFAULT_COLOR = 7

# Die Reihenfolge entspricht exakt den Farbindizes der Pyxel-Standardpalette.
COLORS = (
    "black",
    "navy",
    "purple",
    "green",
    "brown",
    "dark_blue",
    "light_blue",
    "white",
    "red",
    "orange",
    "yellow",
    "lime",
    "cyan",
    "gray",
    "pink",
    "peach",
)

_DIRECTIONS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

_NOTE_PATTERN = re.compile(r"^([A-Ga-g])([#b]?)(-?\d+)$")
_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_ACCIDENTALS = {"": 0, "#": 1, "b": -1}

# Der fachliche Zustand lebt in PyKIM und nicht im Pyxel-Framebuffer. Dadurch
# lassen sich Bewegungen und Pixel ohne Fenster testen.
_x = 0
_y = 0
# Die mit set_color() gewählte Farbe. None bedeutet, dass noch keine Farbe
# gewählt wurde; paint() und paint_path() verwenden dann DEFAULT_COLOR.
_selected_color: int | None = None
_painting_path = False
_pixels = [[0] * WIDTH for _ in range(HEIGHT)]

# Audioereignisse bestehen aus (MIDI-Note, Länge). Die Note -1 steht intern
# für eine Pause. Pyxel verarbeitet die Ereignisse später der Reihe nach.
_notes: deque[tuple[int, int]] = deque()
_pause_frames = 0


# Position und Bewegung

def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        kind = type(value).__name__
        raise TypeError(f"{name} muss eine ganze Zahl sein, nicht {kind}.")
    return value


def _position(x: object, y: object) -> tuple[int, int]:
    """Prüfe eine Position und gib sie als Zahlenpaar zurück."""
    x = _integer(x, "x")
    y = _integer(y, "y")

    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        return x, y

    raise ValueError(
        f"Die Position ({x}, {y}) liegt außerhalb der PyKIM-Welt "
        f"(x: 0..{WIDTH - 1}, y: 0..{HEIGHT - 1})."
    )


def get_x() -> int:
    """Gib Kims aktuelle x-Koordinate zurück."""
    return _x


def get_y() -> int:
    """Gib Kims aktuelle y-Koordinate zurück."""
    return _y


def set_x(x: int) -> None:
    """Setze Kims x-Koordinate, ohne y zu verändern."""
    global _x
    _x, _ = _position(x, _y)


def set_y(y: int) -> None:
    """Setze Kims y-Koordinate, ohne x zu verändern."""
    global _y
    _, _y = _position(_x, y)


def _move(dx: int, dy: int, steps: int) -> None:
    """Bewege Kim und zeichne bei aktivierter Spur alle Zwischenpixel."""
    global _x, _y

    steps = _integer(steps, "steps")
    if steps < 0:
        raise ValueError("steps muss mindestens 0 sein.")

    # Erst das Ziel prüfen. Bei einem Fehler bleiben Position und Welt damit
    # vollständig unverändert.
    new_x, new_y = _position(_x + dx * steps, _y + dy * steps)

    if _painting_path and steps > 0:
        for distance in range(steps + 1):
            x = _x + dx * distance
            y = _y + dy * distance
            _pixels[y][x] = _paint_color()

    _x, _y = new_x, new_y


def up(steps: int = 1) -> None:
    """Bewege Kim nach oben."""
    _move(0, -1, steps)


def down(steps: int = 1) -> None:
    """Bewege Kim nach unten."""
    _move(0, 1, steps)


def left(steps: int = 1) -> None:
    """Bewege Kim nach links."""
    _move(-1, 0, steps)


def right(steps: int = 1) -> None:
    """Bewege Kim nach rechts."""
    _move(1, 0, steps)


# Farben und Pixelwelt

def _color(value: str | int) -> int:
    """Wandle einen Farbnamen oder Index in einen Pyxel-Farbindex um."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise TypeError("Die Farbe muss ein Farbname oder eine Zahl von 0 bis 15 sein.")

    if isinstance(value, int):
        if 0 <= value < len(COLORS):
            return value
        raise ValueError(f"Der Farbwert {value} liegt nicht zwischen 0 und 15.")

    if value in COLORS:
        return COLORS.index(value)

    available = ", ".join(COLORS)
    raise ValueError(f"Die Farbe {value!r} ist unbekannt. Verfügbare Farben: {available}")


def set_color(color: str | int) -> None:
    """Wähle die Farbe für paint() und paint_path()."""
    global _selected_color
    _selected_color = _color(color)


def _paint_color() -> int:
    """Verwende Weiß, solange noch keine Farbe gewählt wurde."""
    return DEFAULT_COLOR if _selected_color is None else _selected_color


def paint() -> None:
    """Färbe den Pixel an Kims aktueller Position."""
    _pixels[_y][_x] = _paint_color()


def paint_path(color: str | int | None = None) -> None:
    """Aktiviere Kims Spur und wähle optional ihre Farbe."""
    global _painting_path, _selected_color

    if color is not None:
        _selected_color = _color(color)
    elif _selected_color is None:
        _selected_color = DEFAULT_COLOR

    _painting_path = True


def get_color(*args: object) -> str:
    """Lies die Farbe hier, in einer Richtung oder an einer Position."""
    if len(args) == 0:
        x, y = _x, _y
    elif len(args) == 1:
        direction = args[0]
        if not isinstance(direction, str):
            raise TypeError("get_color(direction) erwartet einen Richtungsnamen.")
        if direction not in _DIRECTIONS:
            names = ", ".join(_DIRECTIONS)
            raise ValueError(
                f"Die Richtung {direction!r} ist unbekannt. "
                f"Verfügbare Richtungen: {names}"
            )
        dx, dy = _DIRECTIONS[direction]
        x, y = _x + dx, _y + dy
    elif len(args) == 2:
        x, y = args
    else:
        raise TypeError(
            "get_color() erlaubt kein Argument, eine Richtung oder x und y."
        )

    x, y = _position(x, y)
    return COLORS[_pixels[y][x]]


# Töne und Pausen

def _beats(value: object) -> int:
    value = _integer(value, "beats")
    if value < 1:
        raise ValueError("beats muss mindestens 1 sein.")
    return value


def _note_number(note: str | int) -> int:
    """Wandle beispielsweise 'C4' in die MIDI-Note 60 um."""
    if isinstance(note, bool) or not isinstance(note, (str, int)):
        raise TypeError("Die Note muss ein Notenname oder eine Zahl von 36 bis 95 sein.")

    if isinstance(note, str):
        match = _NOTE_PATTERN.fullmatch(note)
        if match is None:
            raise ValueError(
                f"Die Note {note!r} ist ungültig. "
                "Verwende einen Notennamen wie 'C4' oder 'F#4'."
            )

        name, accidental, octave = match.groups()
        # In der MIDI-Zählung beginnt jede Oktave bei C. C4 ergibt so 60.
        note = (
            (int(octave) + 1) * 12
            + _SEMITONES[name.upper()]
            + _ACCIDENTALS[accidental]
        )

    if not 36 <= note <= 95:
        raise ValueError(
            f"Die Note {note!r} liegt außerhalb von Pyxels Tonumfang "
            "36 bis 95 (C2 bis B6)."
        )
    return note


def play_tone(note: str | int, beats: int = 1) -> None:
    """Füge einen Ton mit der angegebenen Länge zur Warteschlange hinzu."""
    _notes.append((_note_number(note), _beats(beats)))


def play_pause(beats: int = 1) -> None:
    """Füge eine musikalische Pause zur Warteschlange hinzu."""
    _notes.append((-1, _beats(beats)))


# Pyxel-Ausgabe

def _play_next_note(pyxel: object) -> None:
    """Starte das nächste Audioereignis, sobald der Kanal frei ist."""
    global _pause_frames

    if _pause_frames > 0:
        _pause_frames -= 1
        return

    if not _notes or pyxel.play_pos(0) is not None:
        return

    note, beats = _notes.popleft()
    if note == -1:
        # Pyxel does not reliably report the end of a sound containing only a
        # rest, so pauses are counted in frames instead.
        _pause_frames = round(7.5 * beats)
        return

    # Pyxel nummeriert seine 60 Tonhöhen von 0 bis 59. PyKIM nimmt die
    # geläufigen MIDI-Werte 36 bis 95 entgegen und verschiebt sie um 36.
    sound = pyxel.sounds[0]
    sound.notes[:] = [note - 36]
    sound.tones[:] = [0]
    sound.volumes[:] = [7]
    sound.effects[:] = [0]
    sound.speed = 30 * beats
    pyxel.play(0, 0)


def _draw_world(pyxel: object) -> None:
    """Zeichne den logischen Pixelzustand in den Pyxel-Framebuffer."""
    pyxel.cls(0)
    for y, row in enumerate(_pixels):
        for x, color in enumerate(row):
            if color != 0:
                pyxel.pset(x, y, color)


def _draw_kim(pyxel: object) -> None:
    """Draw Kim as an orange and gray quadcopter seen from above."""
    orange = 9
    gray = 13

    # Ausleger
    pyxel.line(_x - 3, _y - 3, _x + 3, _y + 3, orange)
    pyxel.line(_x + 3, _y - 3, _x - 3, _y + 3, orange)

    # Animierte Rotorblätter
    blade_positions = ((2, 0), (1, 1), (0, 2), (1, -1))
    blade_x, blade_y = blade_positions[pyxel.frame_count % len(blade_positions)]
    rotors = (
        (_x - 4, _y - 4),
        (_x + 4, _y - 4),
        (_x - 4, _y + 4),
        (_x + 4, _y + 4),
    )

    for rotor_x, rotor_y in rotors:
        pyxel.circ(rotor_x, rotor_y, 2, gray)
        pyxel.line(
            rotor_x - blade_x,
            rotor_y - blade_y,
            rotor_x + blade_x,
            rotor_y + blade_y,
            orange,
        )
        pyxel.pset(rotor_x, rotor_y, orange)

    # Rumpf und orange Frontmarkierung
    pyxel.circ(_x, _y, 2, gray)
    pyxel.pset(_x, _y - 2, orange)


def run() -> None:
    """Öffne das Pyxel-Fenster und starte Bild- und Audioausgabe."""
    try:
        import pyxel
    except ImportError:
        raise RuntimeError(
            "Pyxel wird benötigt, um das PyKIM-Fenster zu öffnen."
        ) from None

    pyxel.init(WIDTH, HEIGHT, title="PyKIM")

    def draw() -> None:
        _draw_world(pyxel)
        _draw_kim(pyxel)

    pyxel.run(lambda: _play_next_note(pyxel), draw)


# Hilfsfunktion für pykim.testing

def _reset() -> None:
    """Setze den gesamten Zustand für Tests und Aufgaben zurück."""
    global _x, _y, _selected_color, _painting_path, _pixels, _pause_frames
    _x = 0
    _y = 0
    _selected_color = None
    _painting_path = False
    _pixels = [[0] * WIDTH for _ in range(HEIGHT)]
    _notes.clear()
    _pause_frames = 0


__all__ = [
    "down",
    "get_color",
    "get_x",
    "get_y",
    "left",
    "paint",
    "paint_path",
    "play_pause",
    "play_tone",
    "right",
    "run",
    "set_color",
    "set_x",
    "set_y",
    "up",
]
