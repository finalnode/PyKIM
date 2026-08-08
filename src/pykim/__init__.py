"""PyKIM: eine kleine, testbare Lernumgebung auf Basis von Pyxel."""

import re
from collections import deque

__version__ = "0.11.0"

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
# gewählt wurde; paint_start() verwendet dann DEFAULT_COLOR.
_selected_color: int | None = None
_painting_path = False
_pixels = [[0] * WIDTH for _ in range(HEIGHT)]

# Audioereignisse bestehen aus (MIDI-Note, Länge). Die Note -1 steht intern
# für eine Pause. Pyxel verarbeitet die Ereignisse später der Reihe nach.
_notes: deque[tuple[int, int]] = deque()
_pause_frames = 0

# animate() zeichnet die besuchten Positionen auf. Beim späteren run() werden
# sie mit der gewählten Verzögerung nacheinander wiedergegeben.
_animation_delay_frames: int | None = None
_animation_positions: list[tuple[int, int]] = []
_animation_paints: list[tuple[int, int, int] | None] = []
_animation_sensors: list[tuple[int, int] | None] = []
_animation_pixels: list[list[int]] = []
_animation_index = 0
_animation_ticks = 0


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
    _record_position(_x, _y)


def set_y(y: int) -> None:
    """Setze Kims y-Koordinate, ohne x zu verändern."""
    global _y
    _, _y = _position(_x, y)
    _record_position(_x, _y)


def _record_position(x: int, y: int, color: int | None = None) -> None:
    """Merke eine Position und optional einen zeitgleichen Farbauftrag."""
    if _animation_delay_frames is not None:
        _animation_positions.append((x, y))
        paint_event = None if color is None else (x, y, color)
        _animation_paints.append(paint_event)
        _animation_sensors.append(None)


def _record_sensor(x: int, y: int) -> None:
    """Merke einen gelesenen Pixel als kurzen Sensor-Moment."""
    if _animation_delay_frames is not None:
        _animation_positions.append((_x, _y))
        _animation_paints.append(None)
        _animation_sensors.append((x, y))


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

    if _animation_delay_frames is not None:
        color = _paint_color() if _painting_path else None
        for distance in range(1, steps + 1):
            _record_position(_x + dx * distance, _y + dy * distance, color)

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


def animate(delay: int | float = 0.1) -> None:
    """Zeige Bewegungen bei run() schrittweise mit delay Sekunden pro Pixel."""
    global _animation_delay_frames, _animation_positions
    global _animation_paints, _animation_sensors, _animation_pixels
    global _animation_index, _animation_ticks

    if isinstance(delay, bool) or not isinstance(delay, (int, float)):
        raise TypeError("delay muss eine Zahl sein.")
    if delay <= 0:
        raise ValueError("delay muss größer als 0 sein.")

    _animation_delay_frames = max(1, round(delay * 30))
    _animation_positions = [(_x, _y)]
    _animation_paints = [None]
    _animation_sensors = [None]
    _animation_pixels = [row[:] for row in _pixels]
    _animation_index = 0
    _animation_ticks = 0


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
    """Wähle die Farbe für paint_start()."""
    global _selected_color
    _selected_color = _color(color)


def _paint_color() -> int:
    """Verwende Weiß, solange noch keine Farbe gewählt wurde."""
    return DEFAULT_COLOR if _selected_color is None else _selected_color


def paint_start(color: str | int | None = None) -> None:
    """Male ab jetzt den aktuellen Pixel und jede folgende Bewegung."""
    global _painting_path, _selected_color

    if color is not None:
        _selected_color = _color(color)
    elif _selected_color is None:
        _selected_color = DEFAULT_COLOR

    _pixels[_y][_x] = _paint_color()
    _record_position(_x, _y, _paint_color())
    _painting_path = True


def paint_stop() -> None:
    """Beende das Malen bei folgenden Bewegungen."""
    global _painting_path
    _painting_path = False


def paint() -> None:
    """Aktiviere das Malen; bevorzugt wird der klare Name paint_start()."""
    paint_start()


def paint_path(color: str | int | None = None) -> None:
    """Kompatibler Alias für paint_start()."""
    paint_start(color)


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
    if args:
        _record_sensor(x, y)
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
    pixels = _animation_pixels if _animation_delay_frames is not None else _pixels
    for y, row in enumerate(pixels):
        for x, color in enumerate(row):
            if color != 0:
                pyxel.pset(x, y, color)


def _animation_position() -> tuple[int, int]:
    if _animation_delay_frames is not None and _animation_positions:
        return _animation_positions[_animation_index]
    return _x, _y


def _advance_animation() -> None:
    """Schalte nach der gewählten Zahl von Frames zur nächsten Position."""
    global _animation_index, _animation_ticks

    if _animation_delay_frames is None:
        return
    if _animation_index >= len(_animation_positions) - 1:
        return

    _animation_ticks += 1
    if _animation_ticks >= _animation_delay_frames:
        _animation_index += 1
        _animation_ticks = 0
        paint_event = _animation_paints[_animation_index]
        if paint_event is not None:
            x, y, color = paint_event
            _animation_pixels[y][x] = color


def _draw_kim(pyxel: object) -> None:
    """Zeichne Kim farbrotierend und mit Kontrast zum Untergrund."""
    x, y = _animation_position()
    color = (pyxel.frame_count // 5) % 15 + 1
    pixels = _animation_pixels if _animation_delay_frames is not None else _pixels
    if color == pixels[y][x]:
        color = color % 15 + 1
    pyxel.pset(x, y, color)


def _draw_sensor(pyxel: object) -> None:
    """Lasse den aktuell von get_color(...) gelesenen Pixel kurz aufleuchten."""
    if _animation_delay_frames is None or not _animation_sensors:
        return
    target = _animation_sensors[_animation_index]
    if target is not None:
        x, y = target
        color = 7 if _animation_pixels[y][x] == 12 else 12
        pyxel.pset(x, y, color)


def _draw_axes(pyxel: object, x: int, y: int, scale: float, color: int) -> None:
    """Ziehe bildschirmfüllende Achsen bis auf ihren Schnittpunkt zusammen."""
    if scale <= 0:
        pyxel.pset(x, y, color)
        return

    left = round(x * (1 - scale))
    right = round(x + (WIDTH - 1 - x) * scale)
    top = round(y * (1 - scale))
    bottom = round(y + (HEIGHT - 1 - y) * scale)
    pyxel.line(left, y, right, y, color)
    pyxel.line(x, top, x, bottom, color)


def _draw_start_sequence(
    pyxel: object, x: int, y: int, frame: int, duration: int = 45
) -> None:
    """Lasse maximale x- und y-Achsen zu Kims Startpixel schrumpfen."""
    pyxel.cls(0)
    color = (pyxel.frame_count // 5) % 15 + 1
    scale = max(0.0, 1 - frame / duration)
    _draw_axes(pyxel, x, y, scale, color)


def run() -> None:
    """Öffne das Pyxel-Fenster und starte Bild- und Audioausgabe."""
    try:
        import pyxel
    except ImportError:
        raise RuntimeError(
            "Pyxel wird benötigt, um das PyKIM-Fenster zu öffnen."
        ) from None

    pyxel.init(WIDTH, HEIGHT, title="PyKIM")

    intro_frame = 0

    def draw() -> None:
        if intro_frame <= 45:
            start_x, start_y = (
                _animation_positions[0]
                if _animation_positions
                else (_x, _y)
            )
            _draw_start_sequence(pyxel, start_x, start_y, intro_frame)
            return

        _draw_world(pyxel)
        _draw_sensor(pyxel)
        _draw_kim(pyxel)

    def update() -> None:
        nonlocal intro_frame

        if intro_frame <= 45:
            intro_frame += 1
            return

        _play_next_note(pyxel)
        _advance_animation()

    pyxel.run(update, draw)


# Hilfsfunktion für pykim.testing

def _reset() -> None:
    """Setze den gesamten Zustand für Tests und Aufgaben zurück."""
    global _x, _y, _selected_color, _painting_path, _pixels, _pause_frames
    global _animation_delay_frames, _animation_positions
    global _animation_paints, _animation_sensors, _animation_pixels
    global _animation_index, _animation_ticks
    _x = 0
    _y = 0
    _selected_color = None
    _painting_path = False
    _pixels = [[0] * WIDTH for _ in range(HEIGHT)]
    _notes.clear()
    _pause_frames = 0
    _animation_delay_frames = None
    _animation_positions = []
    _animation_paints = []
    _animation_sensors = []
    _animation_pixels = []
    _animation_index = 0
    _animation_ticks = 0


__all__ = [
    "animate",
    "down",
    "get_color",
    "get_x",
    "get_y",
    "left",
    "paint",
    "paint_path",
    "paint_start",
    "paint_stop",
    "play_pause",
    "play_tone",
    "right",
    "run",
    "set_color",
    "set_x",
    "set_y",
    "up",
]
