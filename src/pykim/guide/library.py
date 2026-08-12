"""Dateibasierte Kapitel und Aufgabenstellungen des Lernstudios."""

from dataclasses import dataclass
from pathlib import Path
import re


PACKAGED_CONTENT_ROOT = Path(__file__).resolve().parent
PARADIGMS = ("imperativ", "oop")
BUTTON_DIRECTIVES = ("run", "copy")
_ANNOTATED_CODE = re.compile(
    r"(?P<directives>(?:^@button:(?:run|copy)[ \t]*\n)+)"
    r"(?P<fence>```python[ \t]*\n(?P<source>.*?)```)",
    flags=re.MULTILINE | re.DOTALL,
)


@dataclass(frozen=True)
class MarkdownDocument:
    name: str
    title: str
    paradigm: str
    content: str
    path: Path


@dataclass(frozen=True)
class TaskAssignment:
    summary: str
    requirements: tuple[str, ...]
    difficulty: str


def _title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback.replace("_", " ").replace("-", " ").title()


def _documents(folder: str, paradigm: str) -> tuple[MarkdownDocument, ...]:
    if paradigm not in PARADIGMS:
        raise ValueError(f"Unbekanntes Programmierparadigma: {paradigm}")
    from .updates import active_content_root

    directory = active_content_root(PACKAGED_CONTENT_ROOT) / folder / paradigm
    documents = []
    for path in sorted(directory.rglob("*.md")):
        relative = path.relative_to(directory)
        if any(part.startswith("_") for part in relative.parts):
            continue
        content = path.read_text(encoding="utf-8")
        documents.append(
            MarkdownDocument(path.stem, _title(content, path.stem), paradigm, content, path)
        )
    return tuple(documents)


def script_chapters(paradigm: str) -> tuple[MarkdownDocument, ...]:
    """Liefere die Skriptkapitel eines Lernwegs in Dateireihenfolge."""
    return _documents("Skripte", paradigm)


def script_code_examples() -> frozenset[str]:
    """Liefere exakt die mit @button:run freigegebenen Python-Blöcke."""
    examples: set[str] = set()
    for paradigm in PARADIGMS:
        for chapter in script_chapters(paradigm):
            for match in _ANNOTATED_CODE.finditer(chapter.content):
                buttons = _directive_buttons(match.group("directives"))
                if "run" in buttons:
                    examples.add(match.group("source").rstrip())
    return frozenset(examples)


def _directive_buttons(directives: str) -> tuple[str, ...]:
    requested = {
        line.removeprefix("@button:").strip()
        for line in directives.splitlines()
    }
    return tuple(button for button in BUTTON_DIRECTIVES if button in requested)


def render_script_markdown(content: str) -> str:
    """Verberge Autorenanweisungen und markiere den unmittelbar folgenden Block."""
    def replace(match: re.Match[str]) -> str:
        buttons = ",".join(_directive_buttons(match.group("directives")))
        marker = (
            f'<div class="pykim-code-options" data-buttons="{buttons}" '
            'aria-hidden="true"></div>'
        )
        return f"{marker}\n\n{match.group('fence')}"

    return _ANNOTATED_CODE.sub(replace, content)


def task_documents(paradigm: str) -> tuple[MarkdownDocument, ...]:
    """Liefere Aufgabenstellungen; der Dateiname ist die Trainerkennung."""
    return _documents("Aufgaben", paradigm)


def task_document(name: str) -> MarkdownDocument | None:
    for paradigm in PARADIGMS:
        for document in task_documents(paradigm):
            if document.name == name:
                return document
    return None


def task_assignment(name: str) -> TaskAssignment:
    """Erzeuge strukturierte Aufgabendaten ausschließlich aus dem Markdown."""
    document = task_document(name)
    if document is None:
        raise ValueError(f"Für {name!r} fehlt die Aufgabenstellung.")
    lines = document.content.splitlines()
    difficulty = next(
        (
            line.removeprefix("@difficulty:").strip()
            for line in lines
            if line.startswith("@difficulty:")
        ),
        "mittel",
    )
    body_lines = [line for line in lines if not line.startswith("@difficulty:")]
    summary = next(
        (
            line.strip()
            for line in body_lines
            if line.strip() and not line.startswith("#") and not line.startswith("-")
        ),
        document.title,
    )
    requirements = tuple(
        line.removeprefix("- ").strip()
        for line in body_lines
        if line.startswith("- ")
    )
    return TaskAssignment(summary, requirements, difficulty)


def render_task_markdown(content: str) -> str:
    """Blende Autorenmetadaten und die bereits angezeigte Überschrift aus."""
    lines = content.splitlines()
    heading_hidden = False
    visible = []
    for line in lines:
        if line.startswith("@difficulty:"):
            continue
        if not heading_hidden and line.startswith("# "):
            heading_hidden = True
            continue
        visible.append(line)
    return "\n".join(visible).strip()


def task_names() -> tuple[str, ...]:
    """Liefere nur automatisch prüfbare Aufgabenkennungen."""
    from pykim.trainer.exercises import exercise_names

    trainable = set(exercise_names())
    return tuple(
        document.name
        for paradigm in PARADIGMS
        for document in task_documents(paradigm)
        if document.name in trainable
    )
