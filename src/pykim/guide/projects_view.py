"""NiceGUI-Ansicht für persönliche Schülerprojekte."""

from .course import get_course_directory
from .projects import create_project, launch_project, launch_project_editor, student_projects
from .system import open_in_preferred_ide, open_path


TEMPLATE_LABELS = {
    "pykim": "PyKIM-Projekt",
    "pyxel": "Pyxel-Spiel mit Ressourcen",
    "empty": "Leeres Python-Projekt",
}


def render_projects_view(ui, preferred_ide_label: str, ide_open_buttons: list) -> None:
    ui.label("Meine Projekte").classes("text-2xl font-bold")
    ui.markdown(
        "Jedes Projekt besitzt einen eigenen Ordner unter `Projekte/`. "
        "Pyxel-Projekte speichern Bilder, Tilemaps, Sounds und Musik gemeinsam "
        "in `ressourcen.pyxres`."
    )
    course = get_course_directory()
    if course is None:
        ui.label("Richte zuerst im Setup einen Kursordner ein.").classes("text-orange")
        return

    project_list = ui.column().classes("w-full gap-3")

    def action(callback, success: str) -> None:
        try:
            callback()
            ui.notify(success, type="positive")
        except (OSError, RuntimeError, ValueError) as error:
            ui.notify(str(error), type="negative")

    def refresh() -> None:
        project_list.clear()
        projects = student_projects(course)
        with project_list:
            if not projects:
                ui.label("Du hast noch kein eigenes Projekt angelegt.").classes("text-grey-7")
            for project in projects:
                with ui.card().classes("w-full"):
                    with ui.row().classes("w-full items-center"):
                        ui.label(project.name).classes("text-lg font-bold")
                        ui.badge(TEMPLATE_LABELS.get(project.kind, project.kind), color="secondary")
                        ui.space()
                        ui.label(str(project.directory.relative_to(course))).classes("text-xs text-grey-7")
                    if project.resources is not None and not project.resources.exists():
                        ui.label(
                            "Ressourcen noch nicht gespeichert – öffne zuerst den Sprite- und Musikeditor."
                        ).classes("text-sm text-orange")
                    with ui.row().classes("items-center"):
                        ui.button(
                            "Starten",
                            on_click=lambda selected=project: action(
                                lambda: launch_project(selected, course),
                                "Projekt wurde gestartet.",
                            ),
                            icon="play_arrow",
                        )
                        ide_button = ui.button(
                            f"In {preferred_ide_label} öffnen",
                            on_click=lambda selected=project: action(
                                lambda: open_in_preferred_ide(selected.directory),
                                "Projekt wurde in der IDE geöffnet.",
                            ),
                            icon="open_in_new",
                        ).props("outline")
                        ide_open_buttons.append(ide_button)
                        ui.button(
                            "Ordner öffnen",
                            on_click=lambda selected=project: action(
                                lambda: open_path(selected.directory),
                                "Projektordner wurde geöffnet.",
                            ),
                            icon="folder_open",
                        ).props("outline")
                        if project.resources is not None:
                            ui.button(
                                "Sprite- und Musikeditor",
                                on_click=lambda selected=project: action(
                                    lambda: launch_project_editor(selected, course),
                                    "Pyxel-Ressourceneditor wurde gestartet.",
                                ),
                                icon="palette",
                            ).props("outline")

    with ui.dialog() as create_dialog, ui.card().classes("w-full max-w-xl"):
        ui.label("Neues Projekt").classes("text-xl font-bold")
        project_name = ui.input("Projektname", placeholder="z. B. Mein Labyrinth").classes("w-full")
        project_kind = ui.select(TEMPLATE_LABELS, value="pykim", label="Vorlage").classes("w-full")

        def submit() -> None:
            try:
                project = create_project(course, project_name.value or "", project_kind.value)
                create_dialog.close()
                project_name.set_value("")
                refresh()
                ui.notify(f"Projekt „{project.name}“ wurde angelegt.", type="positive")
            except (OSError, ValueError) as error:
                ui.notify(str(error), type="negative")

        with ui.row().classes("w-full justify-end"):
            ui.button("Abbrechen", on_click=create_dialog.close).props("flat")
            ui.button("Projekt anlegen", on_click=submit, icon="create_new_folder")

    ui.button("Neues Projekt", on_click=create_dialog.open, icon="add")
    refresh()


__all__ = ["render_projects_view"]
