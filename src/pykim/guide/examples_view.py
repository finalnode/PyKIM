"""Beispielgalerie mit Starten, Kopieren und persönlichen Projektkopien."""

from .course import get_course_directory
from .examples import copy_example_to_course, example_programs, launch_example
from .system import open_in_preferred_ide


def render_examples_view(ui, preferred_ide_label: str, ide_open_buttons: list) -> None:
    ui.label("PyKIM-Beispiele").classes("text-2xl font-bold")
    ui.markdown(
        "Die Originale gehören zum Paket und bleiben unverändert. Zum Bearbeiten "
        "wird automatisch ein persönliches Projekt unter "
        "`Projekte/beispiele` angelegt."
    )
    for example in example_programs():
        with ui.expansion(example.title, icon="code").classes("w-full"):
            with ui.row().classes("w-full items-center"):
                ui.label(example.description).classes("text-base")
                ui.space()
                ui.badge(example.category, color="secondary")
            editor = ui.codemirror(
                value=example.source, language="Python", line_wrapping=False,
            ).classes("w-full").style("height: 24rem")
            editor.disable()

            def copy_source(source_editor=editor) -> None:
                ui.clipboard.write(source_editor.value)
                ui.notify("Beispielcode wurde kopiert.", type="positive")

            def start(example_name=example.name) -> None:
                try:
                    launch_example(example_name)
                    ui.notify("Beispiel wurde gestartet.", type="positive")
                except (OSError, ValueError) as error:
                    ui.notify(f"Start fehlgeschlagen: {error}", type="negative")

            def personal_copy(example_name=example.name):
                course = get_course_directory()
                if course is None:
                    ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                    return None
                try:
                    return course, copy_example_to_course(example_name, course)
                except (OSError, ValueError) as error:
                    ui.notify(str(error), type="negative")
                    return None

            def save(example_name=example.name) -> None:
                result = personal_copy(example_name)
                if result is None:
                    return
                course, (target, created) = result
                ui.notify(
                    f"Kopie angelegt: {target.relative_to(course)}"
                    if created else "Die persönliche Kopie ist bereits vorhanden.",
                    type="positive",
                )

            def open_in_ide(example_name=example.name) -> None:
                result = personal_copy(example_name)
                if result is None:
                    return
                _course, (target, _created) = result
                try:
                    open_in_preferred_ide(target)
                    ui.notify("Beispiel wurde in der IDE geöffnet.", type="positive")
                except (OSError, RuntimeError, ValueError) as error:
                    ui.notify(str(error), type="negative")

            with ui.row():
                ui.button("Ausführen", on_click=start, icon="play_arrow")
                ui.button("Kopieren", on_click=copy_source, icon="content_copy").props(
                    "outline"
                )
                ide_button = ui.button(
                    f"In {preferred_ide_label} öffnen",
                    on_click=open_in_ide,
                    icon="open_in_new",
                ).props("outline")
                ide_open_buttons.append(ide_button)
                ui.button(
                    "Als eigenes Projekt speichern",
                    on_click=save,
                    icon="content_copy",
                ).props("outline")


__all__ = ["render_examples_view"]
