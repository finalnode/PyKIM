"""PyKIM: eine kleine, testbare Lernumgebung auf Basis von Pyxel."""

import re

from .runtime import Runtime

__version__ = "0.6.0"

WIDTH = 160
HEIGHT = 120
DEFAULT_COLOR = 7
runtime = Runtime(WIDTH, HEIGHT, DEFAULT_COLOR)

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

# Der fachliche Zustand lebt in der Runtime und nicht im Pyxel-Framebuffer.
# Dadurch lassen sich Bewegungen und Pixel ohne Fenster testen. Die öffentliche
# Standardinstanz hält die imperative Anfänger-API rückwärtskompatibel.


# Position und Bewegung

def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        kind = type(value).__name__
        raise TypeError(f"{name} muss eine ganze Zahl sein, nicht {kind}.")
    return value


def _positive_size(value: object, name: str) -> int:
    value = _integer(value, name)
    if value < 1:
        raise ValueError(f"{name} muss mindestens 1 sein.")
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
    return runtime.x


def get_y() -> int:
    """Gib Kims aktuelle y-Koordinate zurück."""
    return runtime.y


def get_position() -> tuple[int, int]:
    """Gib Kims aktuelle Position als Tupel ``(x, y)`` zurück."""
    return runtime.x, runtime.y


def get_obstacles() -> tuple[str, ...]:
    """Nenne die Richtungen angrenzender Hindernisse und Weltränder."""
    return world.get_obstacles(runtime.x, runtime.y)


def collect() -> str:
    """Sammle die Farbe unter KIM ein und gib ihren Namen zurück."""
    return kim.collect()


def count_color(color: str | int) -> int:
    """Zähle Felder einer Farbe in der Welt."""
    return world.count_color(color)


def items_left(color: str | int) -> bool:
    """Prüfe, ob mindestens ein Feld der Farbe übrig ist."""
    return count_color(color) > 0


def prepare(exercise_name: str) -> None:
    """Lade das in sicheren Trainerdaten definierte Aufgabenspielfeld."""
    if not isinstance(exercise_name, str) or not exercise_name:
        raise TypeError("prepare() benötigt eine Aufgabenkennung.")
    from pykim.trainer.exercises import get_exercise

    setup = get_exercise(exercise_name).world_setup
    if setup is None:
        return
    _reset()
    world.set_background(setup.background)
    for x, y, color in setup.cells:
        world.pset(x, y, color)
    if setup.obstacles:
        world.set_obstacle(*setup.obstacles)
    set_position(*setup.start)


def set_x(x: int) -> None:
    """Setze Kims x-Koordinate, ohne y zu verändern."""
    runtime.x, _ = _position(x, runtime.y)
    _record_position(runtime.x, runtime.y)


def set_y(y: int) -> None:
    """Setze Kims y-Koordinate, ohne x zu verändern."""
    _, runtime.y = _position(runtime.x, y)
    _record_position(runtime.x, runtime.y)


def set_position(x: int, y: int) -> None:
    """Setze Kims x- und y-Koordinate gemeinsam."""
    runtime.x, runtime.y = _position(x, y)
    _record_position(runtime.x, runtime.y)


def _record_position(x: int, y: int, color: int | None = None) -> None:
    """Merke eine Position und optional einen zeitgleichen Farbauftrag."""
    if runtime.animation_delay_frames is not None:
        paint_event = None if color is None else (x, y, color)
        if world._capture_parallel(kim, position=(x, y), paint=paint_event):
            return
        runtime.animation_positions.append((x, y))
        runtime.animation_paints.append([] if paint_event is None else [paint_event])
        runtime.animation_sensors.append(None)
        positions = runtime.animation_actor_positions[-1].copy()
        positions[kim] = (x, y)
        runtime.animation_actor_positions.append(positions)
        runtime.animation_actor_visibility.append(runtime.animation_actor_visibility[-1].copy())


def _record_pixel_position(
    pixel: object, x: int, y: int, color: int | None = None
) -> None:
    """Merke eine Position eines zusätzlichen Pixels in der Timeline."""
    if runtime.animation_delay_frames is None:
        return
    paint_event = None if color is None else (x, y, color)
    if world._capture_parallel(pixel, position=(x, y), paint=paint_event):
        return
    runtime.animation_positions.append((x, y))
    runtime.animation_paints.append([] if paint_event is None else [paint_event])
    runtime.animation_sensors.append(None)
    positions = runtime.animation_actor_positions[-1].copy()
    positions[pixel] = (x, y)
    runtime.animation_actor_positions.append(positions)
    runtime.animation_actor_visibility.append(runtime.animation_actor_visibility[-1].copy())


def _register_animation_pixel(pixel: object, x: int, y: int) -> None:
    """Mache ein neu erzeugtes Pixel in allen Animationsframes sichtbar."""
    for positions in runtime.animation_actor_positions:
        positions[pixel] = (x, y)
    for visibility in runtime.animation_actor_visibility:
        visibility[pixel] = True


def _record_pixel_visibility(pixel: object, visible: bool) -> None:
    """Merke hide() oder show() als eigenes Animationsereignis."""
    if runtime.animation_delay_frames is None:
        return
    if world._capture_parallel(pixel, visible=visible):
        return
    runtime.animation_positions.append((pixel.get_x(), pixel.get_y()))
    runtime.animation_paints.append([])
    runtime.animation_sensors.append(None)
    runtime.animation_actor_positions.append(runtime.animation_actor_positions[-1].copy())
    visibility = runtime.animation_actor_visibility[-1].copy()
    visibility[pixel] = visible
    runtime.animation_actor_visibility.append(visibility)


def _record_sensor(x: int, y: int) -> None:
    """Merke einen gelesenen Pixel als kurzen Sensor-Moment."""
    if runtime.animation_delay_frames is not None:
        if world._capture_parallel(kim, sensor=(x, y)):
            return
        runtime.animation_positions.append((runtime.x, runtime.y))
        runtime.animation_paints.append([])
        runtime.animation_sensors.append((x, y))
        runtime.animation_actor_positions.append(runtime.animation_actor_positions[-1].copy())
        runtime.animation_actor_visibility.append(runtime.animation_actor_visibility[-1].copy())


def _move(dx: int, dy: int, steps: int) -> None:
    """Bewege Kim und zeichne bei aktivierter Spur alle Zwischenpixel."""
    steps = _integer(steps, "steps")
    if steps < 0:
        raise ValueError("steps muss mindestens 0 sein.")

    # Erst das Ziel prüfen. Bei einem Fehler bleiben Position und Welt damit
    # vollständig unverändert.
    _position(runtime.x + dx * steps, runtime.y + dy * steps)
    moved_steps = world._movement_distance(runtime.x, runtime.y, dx, dy, steps)
    new_x, new_y = runtime.x + dx * moved_steps, runtime.y + dy * moved_steps

    if runtime.painting_path and moved_steps > 0:
        for distance in range(moved_steps + 1):
            x = runtime.x + dx * distance
            y = runtime.y + dy * distance
            runtime.cells[y][x] = _paint_color()

    if runtime.animation_delay_frames is not None:
        color = _paint_color() if runtime.painting_path else None
        for distance in range(1, moved_steps + 1):
            _record_position(runtime.x + dx * distance, runtime.y + dy * distance, color)

    runtime.x, runtime.y = new_x, new_y


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
    if isinstance(delay, bool) or not isinstance(delay, (int, float)):
        raise TypeError("delay muss eine Zahl sein.")
    if delay <= 0:
        raise ValueError("delay muss größer als 0 sein.")

    _configure_animation(max(1, round(delay * 30)))


def _configure_animation(delay_frames: int | None) -> None:
    """Aktiviere eine Frame-Verzögerung oder schalte die Animation aus."""
    runtime.animation_delay_frames = delay_frames
    runtime.animation_positions = [] if delay_frames is None else [(runtime.x, runtime.y)]
    runtime.animation_actor_positions = (
        []
        if delay_frames is None
        else [{pixel: (pixel.get_x(), pixel.get_y()) for pixel in world.pixels}]
    )
    runtime.animation_actor_visibility = (
        []
        if delay_frames is None
        else [{pixel: pixel.visible for pixel in world.pixels}]
    )
    runtime.animation_paints = [] if delay_frames is None else [[]]
    runtime.animation_sensors = [] if delay_frames is None else [None]
    runtime.animation_pixels = [] if delay_frames is None else [row[:] for row in runtime.cells]
    runtime.animation_index = 0
    runtime.animation_ticks = 0


def speed(value: int) -> None:
    """Setze die Geschwindigkeit von 1 (langsam) bis 100 (sofort)."""
    value = _integer(value, "speed")
    if not 1 <= value <= 100:
        raise ValueError("speed muss zwischen 1 und 100 liegen.")

    delay_frames = None if value == 100 else max(1, round(100 / value))
    _configure_animation(delay_frames)


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
    """Wähle die Farbe für den nächsten Aufruf von paint()."""
    runtime.selected_color = _color(color)


def _paint_color() -> int:
    """Verwende Weiß, solange noch keine Farbe gewählt wurde."""
    return DEFAULT_COLOR if runtime.selected_color is None else runtime.selected_color


def paint(color: str | int | None = None) -> None:
    """Färbe den aktuellen Pixel und male bei folgenden Bewegungen weiter."""
    if color is not None:
        runtime.selected_color = _color(color)
    elif runtime.selected_color is None:
        runtime.selected_color = DEFAULT_COLOR

    runtime.cells[runtime.y][runtime.x] = _paint_color()
    _record_position(runtime.x, runtime.y, _paint_color())
    runtime.painting_path = True


def paint_stop() -> None:
    """Beende das Malen bei folgenden Bewegungen."""
    runtime.painting_path = False


def paint_start(color: str | int | None = None) -> None:
    """Kompatibler Alias für paint()."""
    paint(color)


def paint_path(color: str | int | None = None) -> None:
    """Kompatibler Alias für paint()."""
    paint(color)


def get_color(*args: object) -> str:
    """Lies die Farbe hier, in einer Richtung oder an einer Position."""
    if len(args) == 0:
        x, y = runtime.x, runtime.y
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
        x, y = runtime.x + dx, runtime.y + dy
    elif len(args) == 2:
        x, y = args
    else:
        raise TypeError(
            "get_color() erlaubt kein Argument, eine Richtung oder x und y."
        )

    x, y = _position(x, y)
    if args:
        _record_sensor(x, y)
    return COLORS[runtime.cells[y][x]]


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
    runtime.notes.append((_note_number(note), _beats(beats)))


def play_pause(beats: int = 1) -> None:
    """Füge eine musikalische Pause zur Warteschlange hinzu."""
    runtime.notes.append((-1, _beats(beats)))


# Pyxel-Ausgabe

def _play_next_note(pyxel: object) -> None:
    """Starte das nächste Audioereignis, sobald der Kanal frei ist."""
    if runtime.pause_frames > 0:
        runtime.pause_frames -= 1
        return

    if not runtime.notes or pyxel.play_pos(0) is not None:
        return

    note, beats = runtime.notes.popleft()
    if note == -1:
        # Pyxel does not reliably report the end of a sound containing only a
        # rest, so pauses are counted in frames instead.
        runtime.pause_frames = round(7.5 * beats)
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
    pyxel.cls(world._background_color)
    pixels = runtime.animation_pixels if runtime.animation_delay_frames is not None else runtime.cells
    for y, row in enumerate(pixels):
        for x, color in enumerate(row):
            if color != world._background_color:
                _draw_cell(pyxel, x, y, color)


def _camera_origin() -> tuple[int, int]:
    """Liefere den an den Welträndern begrenzten Kameraausschnitt um KIM."""
    zoom = world._zoom
    if zoom == 1:
        return 0, 0
    visible_width = (WIDTH + zoom - 1) // zoom
    visible_height = (HEIGHT + zoom - 1) // zoom
    center_x, center_y = _animation_position(kim)
    left = min(max(0, center_x - visible_width // 2), WIDTH - visible_width)
    top = min(max(0, center_y - visible_height // 2), HEIGHT - visible_height)
    return left, top


def _screen_position(x: int, y: int) -> tuple[int, int]:
    left, top = _camera_origin()
    return (x - left) * world._zoom, (y - top) * world._zoom


def _draw_cell(pyxel: object, x: int, y: int, color: int) -> None:
    """Zeichne einen logischen Weltpixel in der aktuellen Zoomstufe."""
    screen_x, screen_y = _screen_position(x, y)
    zoom = world._zoom
    if screen_x >= WIDTH or screen_y >= HEIGHT or screen_x + zoom <= 0 or screen_y + zoom <= 0:
        return
    if zoom == 1:
        pyxel.pset(screen_x, screen_y, color)
    else:
        pyxel.rect(screen_x, screen_y, zoom, zoom, color)


def _animation_position(pixel: object | None = None) -> tuple[int, int]:
    pixel = kim if pixel is None else pixel
    if runtime.animation_delay_frames is not None and runtime.animation_actor_positions:
        return runtime.animation_actor_positions[runtime.animation_index][pixel]
    return pixel.get_x(), pixel.get_y()


def _animation_visible(pixel: object) -> bool:
    if runtime.animation_delay_frames is not None and runtime.animation_actor_visibility:
        return runtime.animation_actor_visibility[runtime.animation_index][pixel]
    return pixel.visible


def _advance_animation() -> None:
    """Schalte nach der gewählten Zahl von Frames zur nächsten Position."""
    if runtime.animation_delay_frames is None:
        return
    if runtime.animation_index >= len(runtime.animation_positions) - 1:
        return

    runtime.animation_ticks += 1
    if runtime.animation_ticks >= runtime.animation_delay_frames:
        runtime.animation_index += 1
        runtime.animation_ticks = 0
        for paint_event in runtime.animation_paints[runtime.animation_index]:
            x, y, color = paint_event
            runtime.animation_pixels[y][x] = color


def _draw_actor(pyxel: object, x: int, y: int, offset: int = 0) -> None:
    """Zeichne eine Figur farbrotierend und mit Kontrast zum Untergrund."""
    color = (pyxel.frame_count // 5) % 15 + 1
    color = (color - 1 + offset) % 15 + 1
    pixels = runtime.animation_pixels if runtime.animation_delay_frames is not None else runtime.cells
    if color == pixels[y][x]:
        color = color % 15 + 1
    _draw_cell(pyxel, x, y, color)


def _draw_kim(pyxel: object) -> None:
    """Zeichne den Standard-Pixel KIM."""
    if _animation_visible(kim):
        _draw_actor(pyxel, *_animation_position(kim))


def _draw_pixels(pyxel: object) -> None:
    """Zeichne KIM und alle zusätzlich erzeugten Pixel."""
    _draw_kim(pyxel)
    for index, pixel in enumerate(world.extra_pixels, start=1):
        if _animation_visible(pixel):
            _draw_actor(pyxel, *_animation_position(pixel), index * 3)


def _draw_sensor(pyxel: object) -> None:
    """Lasse den aktuell von get_color(...) gelesenen Pixel kurz aufleuchten."""
    if runtime.animation_delay_frames is None or not runtime.animation_sensors:
        return
    target = runtime.animation_sensors[runtime.animation_index]
    if target is not None:
        x, y = target
        color = 7 if runtime.animation_pixels[y][x] == 12 else 12
        _draw_cell(pyxel, x, y, color)


def _draw_axes(pyxel: object, x: int, y: int, scale: float, color: int) -> None:
    """Ziehe bildschirmfüllende Achsen bis auf ihren Schnittpunkt zusammen."""
    x, y = _screen_position(x, y)
    if scale <= 0:
        if world._zoom == 1:
            pyxel.pset(x, y, color)
        else:
            pyxel.rect(x, y, world._zoom, world._zoom, color)
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
    pyxel.cls(world._background_color)
    color = (pyxel.frame_count // 5) % 15 + 1
    scale = max(0.0, 1 - frame / duration)
    _draw_axes(pyxel, x, y, scale, color)


def _draw_start_sequences(pyxel: object, frame: int, duration: int = 45) -> None:
    """Zeige die schrumpfenden Startachsen aller sichtbaren Pixel zugleich."""
    pyxel.cls(world._background_color)
    scale = max(0.0, 1 - frame / duration)
    for index, pixel in enumerate(world.pixels):
        visible = (
            runtime.animation_actor_visibility[0].get(pixel, pixel.visible)
            if runtime.animation_actor_visibility
            else pixel.visible
        )
        if not visible:
            continue
        x, y = (
            runtime.animation_actor_positions[0].get(
                pixel, (pixel.get_x(), pixel.get_y())
            )
            if runtime.animation_actor_positions
            else (pixel.get_x(), pixel.get_y())
        )
        color = ((pyxel.frame_count // 5) + index * 3) % 15 + 1
        _draw_axes(pyxel, x, y, scale, color)


def run(
    update: object = None,
    draw: object = None,
    *,
    check: str | None = None,
    _source: str | None = None,
) -> None:
    """Prüfe optional eine Aufgabe und öffne anschließend das Pyxel-Fenster."""
    if check is not None:
        import inspect

        from pykim.trainer.runner import check_exercise

        caller = inspect.currentframe()
        caller = caller.f_back if caller is not None else None
        if _source is None:
            try:
                source = inspect.getsource(caller) if caller is not None else ""
            except (OSError, TypeError):
                source = ""
        else:
            source = _source
        namespace = {}
        if caller is not None:
            namespace.update(caller.f_globals)
            namespace.update(caller.f_locals)
        check_exercise(check, source, namespace)

    # Dokumentations- und CI-Prüfungen führen vollständige Schülerprogramme
    # absichtlich ohne Fenster aus. Die gesamte Weltlogik ist zu diesem
    # Zeitpunkt bereits gelaufen und kann trotzdem geprüft werden.
    import os
    if os.environ.get("PYKIM_HEADLESS") == "1":
        return

    try:
        import pyxel
    except ImportError:
        raise RuntimeError(
            "Pyxel wird benötigt, um das PyKIM-Fenster zu öffnen."
        ) from None

    if update is not None and not callable(update):
        raise TypeError("update muss eine Funktion sein.")
    if draw is not None and not callable(draw):
        raise TypeError("draw muss eine Funktion sein.")

    pyxel.init(WIDTH, HEIGHT, title="PyKIM")

    if update is not None or draw is not None:
        world._backend = pyxel

        def interactive_update() -> None:
            _play_next_note(pyxel)
            for pixel in world.pixels:
                pixel.update()
            if update is not None:
                update()

        def interactive_draw() -> None:
            if draw is not None:
                draw()
            else:
                world.cls(world.background_color)
                for pixel in world.pixels:
                    pixel.draw()

        try:
            pyxel.run(interactive_update, interactive_draw)
        finally:
            world._backend = None
        return

    intro_frame = 0

    def draw() -> None:
        if intro_frame <= 45:
            _draw_start_sequences(pyxel, intro_frame)
            return

        _draw_world(pyxel)
        _draw_sensor(pyxel)
        _draw_pixels(pyxel)

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
    runtime.reset_state()
    if "world" in globals():
        world.extra_pixels.clear()
        world._backend = None
        world._zoom = 1
        world._background_color = 0
        world._obstacle_colors.clear()
        kim.visible = True


def hide() -> None:
    """Verstecke KIM, ohne seine Spur oder Position zu verändern."""
    kim.hide()


def show() -> None:
    """Zeige KIM wieder an."""
    kim.show()


from .pixel import Pixel
from .world import World

world = World(runtime)
kim = Pixel(world, "KIM", default=True)
runtime.bind(world, kim)


__all__ = [
    "animate",
    "collect",
    "count_color",
    "down",
    "get_color",
    "get_obstacles",
    "get_position",
    "get_x",
    "get_y",
    "hide",
    "items_left",
    "left",
    "paint",
    "paint_stop",
    "Pixel",
    "play_pause",
    "play_tone",
    "prepare",
    "right",
    "Runtime",
    "runtime",
    "run",
    "set_color",
    "set_position",
    "set_x",
    "set_y",
    "show",
    "speed",
    "up",
    "World",
    "kim",
    "world",
]
