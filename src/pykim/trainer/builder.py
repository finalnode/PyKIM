"""Lesbare, deklarative Autoren-API für PyKIM-Aufgaben."""

import ast
import hashlib
import json
from collections.abc import Callable, Iterable, Mapping
from contextvars import ContextVar
from typing import TypeAlias

import pykim
from pykim.testing import get_pending_audio_events

from .models import (
    CheckReport,
    CheckResult,
    Exercise,
    OptimizationResult,
    RuleDefinition,
)

Position: TypeAlias = tuple[int, int]
Color: TypeAlias = str | int
ResultFactory: TypeAlias = Callable[[str], CheckResult]
Optimization: TypeAlias = Callable[[str], OptimizationResult]
_ACTIVE_NAMESPACE: ContextVar[Mapping[str, object]] = ContextVar(
    "pykim_trainer_namespace", default={}
)


def _tree(source: str) -> ast.AST | None:
    if not source:
        return None
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _painted_cells() -> dict[Position, int]:
    return {
        (x, y): color
        for y, row in enumerate(pykim.world.cells)
        for x, color in enumerate(row)
        if color != pykim.world._background_color
    }


def _pixel_by_name(name: str):
    return next((pixel for pixel in pykim.world.pixels if pixel.name == name), None)


class ExerciseBuilder:
    """Baue eine Aufgabe aus verständlichen fachlichen Erwartungen zusammen."""

    def __init__(self, name: str, title: str) -> None:
        if not name or not title:
            raise ValueError("Eine Aufgabe benötigt name und title.")
        self.name = name
        self.title = title
        self._results: list[ResultFactory] = []
        self._rules: list[RuleDefinition] = []
        self._optimization: Optimization | None = None

    def add_check(
        self,
        predicate: Callable[[str], bool],
        *,
        success: str,
        failure: str,
        hint: str = "",
        rule: str = "custom",
    ) -> "ExerciseBuilder":
        """Ergänze bei Sonderfällen eine eigene, klar beschriftete Prüfung."""
        self._results.append(
            lambda source: CheckResult(
                bool(predicate(source)), success, failure, hint
            )
        )
        self._rules.append(RuleDefinition(rule, success, failure, hint))
        return self

    def add_result(
        self,
        factory: ResultFactory,
        *,
        rule: str = "dynamic",
        success: str = "Dynamische Prüfung bestanden.",
        failure: str = "Dynamische Prüfung fehlgeschlagen.",
        hint: str = "",
    ) -> "ExerciseBuilder":
        """Ergänze eine Prüfung mit dynamischen Rückmeldungen."""
        self._results.append(factory)
        self._rules.append(RuleDefinition(rule, success, failure, hint))
        return self

    def _tag_last(self, kind: str) -> "ExerciseBuilder":
        current = self._rules[-1]
        self._rules[-1] = RuleDefinition(
            kind, current.success, current.failure, current.hint
        )
        return self

    def expect_pixels(
        self,
        expected: Mapping[Position, Color] | Iterable[Position],
        *,
        exact: bool = True,
        success: str = "Alle erwarteten Farbpixel stimmen.",
        failure: str = "Positionen, Farben oder zusätzliche Pixel stimmen nicht.",
        hint: str = "Vergleiche deine Zeichnung mit der Aufgabenstellung.",
    ) -> "ExerciseBuilder":
        if isinstance(expected, Mapping):
            normalized = {position: pykim._color(value) for position, value in expected.items()}
            predicate = (
                lambda _source: _painted_cells() == normalized
                if exact
                else normalized.items() <= _painted_cells().items()
            )
        else:
            positions = set(expected)
            predicate = (
                lambda _source: set(_painted_cells()) == positions
                if exact
                else positions <= set(_painted_cells())
            )
        return self.add_check(
            predicate, success=success, failure=failure, hint=hint, rule="pixels"
        )

    def expect_square(
        self,
        start: Position,
        side: int,
    ) -> "ExerciseBuilder":
        """Prüfe ein geschlossenes, beliebig ausgerichtetes Quadrat."""
        def geometry() -> tuple[set[Position], set[Position], int, int, bool]:
            pixels = set(_painted_cells())
            if not pixels:
                return pixels, set(), 0, 0, False
            xs = [x for x, _y in pixels]
            ys = [y for _x, y in pixels]
            left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
            outline = {
                (x, y)
                for x in range(left, right + 1)
                for y in range(top, bottom + 1)
                if x in (left, right) or y in (top, bottom)
            }
            corners = {(left, top), (right, top), (left, bottom), (right, bottom)}
            return pixels, outline, right - left, bottom - top, start in corners

        self.add_check(
            lambda _source: (
                (actor := _pixel_by_name("KIM")) is not None
                and (actor.get_x(), actor.get_y()) == start
                and geometry()[4]
            ),
            success=f"KIM hat bei {start} gezeichnet und ist dorthin zurückgekehrt.",
            failure=f"Start oder Ende des Quadrats liegt nicht bei {start}.",
            hint=f"Setze KIM zuerst mit set_position{start} an den Startpunkt.",
        )._tag_last("square-start")

        def size_result(index: int, label: str) -> ResultFactory:
            def result(_source: str) -> CheckResult:
                actual = geometry()[index]
                return CheckResult(
                    actual == side,
                    f"Das Quadrat ist {side} Pixel {label}.",
                    f"Die Zeichnung ist momentan {actual} Pixel {label}.",
                    f"Eine entsprechende Seite soll genau {side} Schritte lang sein.",
                )
            return result

        self.add_result(
            size_result(2, "breit"),
            rule="square-width",
            success=f"Das Quadrat ist {side} Pixel breit.",
            failure="Die Breite des Quadrats stimmt noch nicht.",
            hint=f"Die waagerechten Seiten sollen genau {side} Schritte lang sein.",
        )
        self.add_result(
            size_result(3, "hoch"),
            rule="square-height",
            success=f"Das Quadrat ist {side} Pixel hoch.",
            failure="Die Höhe des Quadrats stimmt noch nicht.",
            hint=f"Die senkrechten Seiten sollen genau {side} Schritte lang sein.",
        )
        self.add_check(
            lambda _source: bool(geometry()[0]) and geometry()[1] <= geometry()[0],
            success="Alle vier Seiten sind vollständig.",
            failure="Mindestens eine Seite ist noch nicht vollständig.",
            hint="Beginne die Farbspur vor der ersten Bewegung und zeichne vier Seiten.",
        )._tag_last("square-outline")
        self.add_check(
            lambda _source: bool(geometry()[0]) and geometry()[0] <= geometry()[1],
            success="Es wurden keine zusätzlichen Pixel angemalt.",
            failure="Es wurden Pixel innerhalb oder außerhalb des Quadratrands angemalt.",
            hint="Beende die Farbspur, bevor du nach dem Quadrat weitergehst.",
        )._tag_last("square-no-extras")
        return self

    def expect_no_extra_pixels(
        self,
        allowed: Iterable[Position],
        *,
        success: str = "Es wurden keine zusätzlichen Pixel angemalt.",
        failure: str = "Es wurden zusätzliche Pixel angemalt.",
        hint: str = "Male nur die in der Aufgabe geforderten Pixel an.",
    ) -> "ExerciseBuilder":
        allowed = set(allowed)
        return self.add_check(
            lambda _source: bool(_painted_cells()) and set(_painted_cells()) <= allowed,
            success=success, failure=failure, hint=hint, rule="no-extra-pixels",
        )

    def expect_pixel_count(
        self,
        count: int,
        *,
        success: str = "Die Anzahl der gemalten Pixel stimmt.",
        failure: str | None = None,
        hint: str = "",
    ) -> "ExerciseBuilder":
        def result(_source: str) -> CheckResult:
            actual = len(_painted_cells())
            message = failure or f"Erwartet sind {count} Pixel; angemalt wurden {actual}."
            return CheckResult(actual == count, success, message, hint)
        return self.add_result(
            result,
            rule="pixel-count",
            success=success,
            failure=failure or f"Die Anzahl soll genau {count} sein.",
            hint=hint,
        )

    def expect_color_count(
        self,
        color: Color,
        count: int,
        *,
        success: str = "Die Anzahl der verbleibenden Farbfelder stimmt.",
        failure: str | None = None,
        hint: str = "Prüfe, welche Felder gesammelt oder verändert werden sollen.",
    ) -> "ExerciseBuilder":
        color_index = pykim._color(color)

        def result(_source: str) -> CheckResult:
            actual = sum(row.count(color_index) for row in pykim.world.cells)
            message = failure or (
                f"Erwartet sind {count} Felder der Farbe {pykim.COLORS[color_index]}; "
                f"vorhanden sind {actual}."
            )
            return CheckResult(actual == count, success, message, hint)

        return self.add_result(
            result,
            rule="color-count",
            success=success,
            failure=failure or f"Die Anzahl soll genau {count} sein.",
            hint=hint,
        )

    def expect_position(
        self,
        position: Position,
        *,
        pixel: str = "KIM",
        success: str | None = None,
        failure: str | None = None,
        hint: str = "Prüfe die letzte Bewegung der Figur.",
    ) -> "ExerciseBuilder":
        def predicate(_source: str) -> bool:
            actor = _pixel_by_name(pixel)
            return actor is not None and (actor.get_x(), actor.get_y()) == position
        return self.add_check(
            predicate,
            success=success or f"{pixel} steht an der richtigen Endposition.",
            failure=failure or f"{pixel} steht noch nicht bei {position}.",
            hint=hint, rule="position",
        )

    def expect_positions(
        self,
        expected: Mapping[str, Position],
        *,
        success: str = "Alle Figuren stehen an ihren richtigen Endpositionen.",
        failure: str = "Mindestens eine Figur steht an der falschen Endposition.",
        hint: str = "Prüfe die Bewegungen der Figuren einzeln.",
    ) -> "ExerciseBuilder":
        def predicate(_source: str) -> bool:
            return all(
                (actor := _pixel_by_name(name)) is not None
                and (actor.get_x(), actor.get_y()) == position
                for name, position in expected.items()
            )
        return self.add_check(
            predicate, success=success, failure=failure, hint=hint,
            rule="positions",
        )

    def expect_pixel_names(
        self,
        names: Iterable[str],
        *,
        success: str = "Die Welt enthält genau die geforderten Figuren.",
        failure: str = "Die Figuren in der Welt stimmen noch nicht.",
        hint: str = "Erzeuge die fehlenden Figuren mit world.new_pixel(...).",
    ) -> "ExerciseBuilder":
        expected = set(names)
        return self.add_check(
            lambda _source: {pixel.name for pixel in pykim.world.pixels} == expected,
            success=success, failure=failure, hint=hint, rule="pixel-names",
        )

    def expect_visibility(
        self,
        pixel: str,
        visible: bool,
        *,
        success: str | None = None,
        failure: str | None = None,
        hint: str = "Verwende show() oder hide() an der richtigen Stelle.",
    ) -> "ExerciseBuilder":
        def predicate(_source: str) -> bool:
            actor = _pixel_by_name(pixel)
            return actor is not None and actor.visible is visible
        state = "sichtbar" if visible else "versteckt"
        return self.add_check(
            predicate,
            success=success or f"{pixel} ist wie gefordert {state}.",
            failure=failure or f"{pixel} ist noch nicht {state}.",
            hint=hint, rule="visibility",
        )

    def expect_audio(
        self,
        events: Iterable[tuple[str | int | None, int]],
        *,
        success: str = "Töne, Reihenfolge und Längen stimmen.",
        failure: str = "Töne, Reihenfolge oder Längen stimmen noch nicht.",
        hint: str = "Prüfe die Noten und ihre beats-Werte.",
    ) -> "ExerciseBuilder":
        expected = tuple(
            (-1 if note is None else pykim._note_number(note), pykim._beats(beats))
            for note, beats in events
        )
        return self.add_check(
            lambda _source: get_pending_audio_events() == expected,
            success=success, failure=failure, hint=hint, rule="audio",
        )

    def _require_source(
        self,
        predicate: Callable[[ast.AST, str], bool],
        *,
        success: str,
        failure: str,
        hint: str,
        rule: str = "source",
    ) -> "ExerciseBuilder":
        def check_source(source: str) -> bool:
            tree = _tree(source)
            return tree is not None and predicate(tree, source)
        return self.add_check(
            check_source, success=success, failure=failure, hint=hint, rule=rule
        )

    def require_loop(self, *, kind: str | None = None, success: str = "Du verwendest eine Schleife.", failure: str = "Es wurde noch keine Schleife erkannt.", hint: str = "Nutze for und range(), um Wiederholungen zu formulieren.") -> "ExerciseBuilder":
        node_type = {None: (ast.For, ast.While), "for": (ast.For,), "while": (ast.While,)}.get(kind)
        if node_type is None:
            raise ValueError("Schleifenart muss 'for', 'while' oder leer sein.")
        return self._require_source(
            lambda tree, _source: any(isinstance(node, node_type) for node in ast.walk(tree)),
            success=success, failure=failure, hint=hint, rule="loop",
        )

    def require_nested_loop(self, *, success: str = "Du verwendest verschachtelte Schleifen.", failure: str = "Es wurden noch keine verschachtelten Schleifen erkannt.", hint: str = "Setze eine Schleife für die Spalten in eine Schleife für die Zeilen.") -> "ExerciseBuilder":
        loops = (ast.For, ast.While)
        return self._require_source(
            lambda tree, _source: any(
                isinstance(node, loops)
                and any(isinstance(child, loops) for child in ast.walk(node) if child is not node)
                for node in ast.walk(tree)
            ), success=success, failure=failure, hint=hint, rule="nested-loop",
        )

    def require_condition(self, *, calls: Iterable[str] = (), success: str = "Du verwendest eine Bedingung.", failure: str = "Es wurde noch keine if-Bedingung erkannt.", hint: str = "Verwende if und bei Bedarf elif oder else.") -> "ExerciseBuilder":
        required_calls = set(calls)
        return self._require_source(
            lambda tree, _source: (
                any(isinstance(node, ast.If) for node in ast.walk(tree))
                and required_calls <= {
                    name for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and (name := _call_name(node)) is not None
                }
            ),
            success=success, failure=failure, hint=hint, rule="condition",
        )

    def require_function(self, name: str | None = None, *, parameters: Iterable[str] | None = None, returns: bool | None = None, success: str = "Du verwendest eine eigene Funktion.", failure: str = "Es wurde noch keine passende Funktion erkannt.", hint: str = "Definiere die wiederholte Teilaufgabe mit def.") -> "ExerciseBuilder":
        expected_parameters = None if parameters is None else tuple(parameters)
        def predicate(tree: ast.AST, _source: str) -> bool:
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if name is not None and node.name != name:
                    continue
                actual = tuple(argument.arg for argument in node.args.args)
                if expected_parameters is not None and actual != expected_parameters:
                    continue
                has_return = any(
                    isinstance(child, ast.Return) and child.value is not None
                    for child in ast.walk(node)
                )
                if returns is not None and has_return is not returns:
                    continue
                return True
            return False
        return self._require_source(
            predicate, success=success, failure=failure, hint=hint, rule="function",
        )

    def expect_function_cases(
        self,
        name: str,
        cases: Iterable[Mapping[str, object]],
        *,
        success: str = "Die Funktion liefert für alle Testfälle das richtige Ergebnis.",
        failure: str = "Mindestens ein Funktionstest liefert noch ein falsches Ergebnis.",
        hint: str = "Prüfe Rückgabewert und Sonderfälle deiner Funktion.",
    ) -> "ExerciseBuilder":
        normalized = tuple(
            (
                tuple(case.get("args", ())),
                dict(case.get("kwargs", {})),
                case.get("expected"),
            )
            for case in cases
        )

        def predicate(_source: str) -> bool:
            function = _ACTIVE_NAMESPACE.get().get(name)
            if not callable(function):
                return False
            try:
                return all(function(*args, **kwargs) == expected for args, kwargs, expected in normalized)
            except Exception:
                return False

        return self.add_check(
            predicate,
            success=success,
            failure=failure,
            hint=hint,
            rule="function-cases",
        )

    def require_calls(self, *names: str, success: str | None = None, failure: str | None = None, hint: str = "Prüfe, ob alle geforderten Funktionen aufgerufen werden.") -> "ExerciseBuilder":
        expected = set(names)
        return self._require_source(
            lambda tree, _source: expected <= {
                name for node in ast.walk(tree)
                if isinstance(node, ast.Call) and (name := _call_name(node)) is not None
            },
            success=success or f"Du verwendest {', '.join(names)}.",
            failure=failure or f"Mindestens ein Aufruf fehlt: {', '.join(names)}.",
            hint=hint, rule="calls",
        )

    def require_parallel(self, *, success: str = "Du verwendest world.parallel().", failure: str = "Es wurde noch kein world.parallel()-Block erkannt.", hint: str = "Nutze with world.parallel(): für gleichzeitige Bewegungen.") -> "ExerciseBuilder":
        def predicate(tree: ast.AST, _source: str) -> bool:
            return any(
                isinstance(node, (ast.With, ast.AsyncWith))
                and any(
                    isinstance(item.context_expr, ast.Call)
                    and _call_name(item.context_expr) == "parallel"
                    for item in node.items
                )
                for node in ast.walk(tree)
            )
        return self._require_source(
            predicate, success=success, failure=failure, hint=hint,
            rule="parallel",
        )

    def require_class(self, name: str, *, base: str | None = None, success: str | None = None, failure: str | None = None, hint: str = "Prüfe Klassenname und Basisklasse.") -> "ExerciseBuilder":
        def predicate(tree: ast.AST, _source: str) -> bool:
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef) or node.name != name:
                    continue
                bases = {_callable_name(item) for item in node.bases}
                return base is None or base in bases
            return False
        return self._require_source(
            predicate,
            success=success or f"Die Klasse {name} ist richtig definiert.",
            failure=failure or f"Die Klasse {name} fehlt oder erbt nicht korrekt.",
            hint=hint, rule="class",
        )

    def require_methods(self, class_name: str, *methods: str, success: str | None = None, failure: str | None = None, hint: str = "Definiere die Methoden innerhalb der Klasse.") -> "ExerciseBuilder":
        expected = set(methods)
        def predicate(tree: ast.AST, _source: str) -> bool:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    actual = {item.name for item in node.body if isinstance(item, ast.FunctionDef)}
                    return expected <= actual
            return False
        return self._require_source(
            predicate,
            success=success or f"{class_name} besitzt alle geforderten Methoden.",
            failure=failure or f"In {class_name} fehlen Methoden: {', '.join(methods)}.",
            hint=hint, rule="methods",
        )

    def require_super_init(self, class_name: str, *, success: str = "Der Konstruktor der Basisklasse wird aufgerufen.", failure: str = "Ein Aufruf von super().__init__() fehlt noch.", hint: str = "Rufe in __init__ zuerst super().__init__(...) auf.") -> "ExerciseBuilder":
        def predicate(tree: ast.AST, _source: str) -> bool:
            target = next((node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == class_name), None)
            if target is None:
                return False
            return any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "__init__"
                and isinstance(node.func.value, ast.Call)
                and _call_name(node.func.value) == "super"
                for node in ast.walk(target)
            )
        return self._require_source(
            predicate, success=success, failure=failure, hint=hint,
            rule="super-init",
        )

    def optimize_with(self, evaluator: Optimization) -> "ExerciseBuilder":
        self._optimization = evaluator
        return self

    def optimize_lines(self, optimal: int) -> "ExerciseBuilder":
        """Bewerte die nichtleeren, relevanten Codezeilen in Prozent."""
        if isinstance(optimal, bool) or not isinstance(optimal, int):
            raise TypeError("optimal muss eine ganze Zahl sein.")
        if optimal < 1:
            raise ValueError("optimal muss mindestens 1 sein.")

        def evaluate(source: str) -> OptimizationResult:
            lines = [
                line
                for line in source.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            actual = len(lines)
            if actual == 0:
                return OptimizationResult(
                    0,
                    ("Es wurde kein auswertbarer Code gefunden.",),
                    maximum=100,
                )
            score = min(100, round(optimal / actual * 100))
            tips = () if score == 100 else (
                f"Die Aufgabe lässt sich optimal in {optimal} relevanten "
                f"Codezeilen lösen; dein Programm verwendet {actual}.",
            )
            return OptimizationResult(score, tips, maximum=100)

        self._optimization = evaluate
        return self

    def build(self) -> Exercise:
        factories = tuple(self._results)
        rules = tuple(self._rules)
        evaluator = self._optimization
        title = self.title

        def checker(source: str, namespace: Mapping[str, object] | None = None) -> CheckReport:
            token = _ACTIVE_NAMESPACE.set(namespace or {})
            try:
                optimization = None if evaluator is None else evaluator(source)
                return CheckReport(
                    title,
                    tuple(factory(source) for factory in factories),
                    optimization,
                )
            finally:
                _ACTIVE_NAMESPACE.reset(token)

        definition = {
            "name": self.name,
            "title": self.title,
            "rules": [rule.__dict__ for rule in rules],
            "optimization": evaluator is not None,
        }
        definition_hash = hashlib.sha256(
            json.dumps(definition, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return Exercise(
            self.name,
            self.title,
            checker,
            rules=rules,
            definition_hash=definition_hash,
        )


def _callable_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


__all__ = ["ExerciseBuilder"]
