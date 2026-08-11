"""Sicherer Arbeitsbereich für gemeinsam versionierte Trainer- und Markdownentwürfe."""

import ast
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from pykim.trainer.exercises import get_exercise

from .library import task_document


@dataclass(frozen=True)
class AuthorDraft:
    name: str
    trainer_source: str
    assignment_markdown: str

    @property
    def content_hash(self) -> str:
        payload = self.trainer_source.rstrip() + "\n---\n" + self.assignment_markdown.rstrip()
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def assignment_markdown(
    title: str,
    summary: str,
    requirements: str,
    difficulty: str,
) -> str:
    bullets = [line.strip().removeprefix("- ") for line in requirements.splitlines() if line.strip()]
    if not bullets:
        bullets = ["Beschreibe hier das überprüfbare Ziel."]
    return "\n".join(
        [
            f"# {title.strip()}",
            f"@difficulty:{difficulty}",
            "",
            summary.strip(),
            "",
            "## Anforderungen",
            "",
            *(f"- {item}" for item in bullets),
            "",
        ]
    )


def validate_author_draft(draft: AuthorDraft) -> tuple[str, ...]:
    issues: list[str] = []
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", draft.name):
        issues.append("Die Kennung muss ein kebab-case-Name sein.")
    try:
        tree = ast.parse(draft.trainer_source)
    except SyntaxError as error:
        issues.append(f"Trainer-Python enthält einen Syntaxfehler in Zeile {error.lineno}.")
        tree = None
    if tree is not None:
        builders = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "ExerciseBuilder"
        ]
        if not builders:
            issues.append("Im Trainercode fehlt ExerciseBuilder(...).")
        elif not builders[0].args or not isinstance(builders[0].args[0], ast.Constant) or builders[0].args[0].value != draft.name:
            issues.append("Die ExerciseBuilder-Kennung stimmt nicht mit dem Entwurfsnamen überein.")
        if not any(isinstance(node, ast.Name) and node.id == "EXERCISE" for node in ast.walk(tree)):
            issues.append("Die Trainerdatei muss EXERCISE exportieren.")
    lines = draft.assignment_markdown.splitlines()
    if not any(line.startswith("# ") for line in lines):
        issues.append("Im Markdown fehlt die Überschrift der Aufgabe.")
    if not any(line.startswith("@difficulty:") for line in lines):
        issues.append("Im Markdown fehlt @difficulty:.")
    if not any(line.startswith("- ") for line in lines):
        issues.append("Im Markdown fehlt mindestens eine überprüfbare Anforderung.")
    return tuple(issues)


def load_published_draft(name: str) -> AuthorDraft:
    get_exercise(name)  # verständliche Fehlermeldung für unbekannte Kennungen
    import pykim.trainer.exercises as exercise_package

    source_path = next(
        (
            path
            for path in Path(exercise_package.__file__).parent.glob("*.py")
            if f'ExerciseBuilder("{name}"' in path.read_text(encoding="utf-8")
        ),
        None,
    )
    if source_path is None:
        raise ValueError(f"Die Trainerquelle für {name!r} wurde nicht gefunden.")
    document = task_document(name)
    if document is None:
        raise ValueError(f"Für {name!r} fehlt das Aufgaben-Markdown.")
    return AuthorDraft(
        name,
        source_path.read_text(encoding="utf-8"),
        document.content,
    )


def save_author_draft(
    course: str | Path,
    draft: AuthorDraft,
    *,
    paradigm: str,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    issues = validate_author_draft(draft)
    if issues:
        raise ValueError(" ".join(issues))
    if paradigm not in {"imperativ", "oop"}:
        raise ValueError("Der Lernweg muss imperativ oder oop sein.")
    root = Path(course).expanduser().resolve() / ".pykim" / "author_drafts"
    trainer_path = root / "trainer" / f"{draft.name.replace('-', '_')}.py"
    markdown_path = root / "Aufgaben" / paradigm / f"{draft.name}.md"
    if not overwrite and (trainer_path.exists() or markdown_path.exists()):
        raise FileExistsError(
            "Der Entwurf existiert bereits. Aktiviere Überschreiben nur bewusst."
        )
    trainer_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    trainer_path.write_text(draft.trainer_source.rstrip() + "\n", encoding="utf-8")
    markdown_path.write_text(draft.assignment_markdown.rstrip() + "\n", encoding="utf-8")
    return trainer_path, markdown_path


__all__ = [
    "AuthorDraft", "assignment_markdown", "load_published_draft",
    "save_author_draft", "validate_author_draft",
]
