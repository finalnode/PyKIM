"""Gemeinsamer Seitenrahmen der in:si-Lernumgebung."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pykim

from .branding import APP_DISPLAY_NAME
from .course import get_course_directory, get_student_name
from .course_setup import course_setup_info
from .navigation import create_navigation
from .system import system_user_name


@dataclass(frozen=True, slots=True)
class WorkspaceLayout:
    """UI-Elemente und Werte, die nach dem Aufbau des Headers benötigt werden."""

    tabs: Any
    pages: tuple[Any, ...]
    update_badge: Any
    course_setup: Any
    student_name: str


def render_workspace_header(ui, course_selection) -> WorkspaceLayout:
    """Erzeuge Kopfzeile und Hauptnavigation und liefere deren Bindungen zurück."""
    ui.link("Zum Hauptinhalt springen", "#pykim-main").classes("pykim-skip-link")
    configured = get_course_directory()
    course_setup = None
    if configured is not None:
        try:
            course_setup = course_setup_info(configured)
        except (OSError, ValueError):
            course_setup = None
    student_name = get_student_name(configured) or system_user_name()

    with ui.header().classes("pykim-header"):
        with ui.row().classes("pykim-header-top w-full items-center no-wrap"):
            ui.label(APP_DISPLAY_NAME).classes("text-xl font-bold")
            if course_setup is not None:
                ui.label(f"· {course_setup.course}").classes(
                    "text-lg font-medium text-white"
                )
            ui.space()
            ui.label(f"Hallo, {student_name}").classes("text-sm")
            update_badge = ui.badge("Updates werden geprüft …", color="grey")
            update_badge.classes("cursor-pointer").props(
                "title='Verfügbare Updates anzeigen' role=button tabindex=0"
            )
            ui.button(
                "Kurs wechseln",
                on_click=lambda: (
                    course_selection.update(confirmed=False),
                    ui.navigate.reload(),
                ),
                icon="swap_horiz",
            ).props("flat dense color=white")
            ui.label(
                "Kein Kursordner" if configured is None else str(configured)
            ).classes("pykim-course-path text-sm")
        tabs, pages = create_navigation(ui)

    return WorkspaceLayout(
        tabs=tabs,
        pages=pages,
        update_badge=update_badge,
        course_setup=course_setup,
        student_name=student_name,
    )


def render_workspace_footer(ui) -> None:
    """Erzeuge den stabilen Footer unabhängig von den fachlichen Views."""
    with ui.element("footer").classes("pykim-footer w-full"):
        with ui.row().classes(
            "w-full max-w-6xl mx-auto items-center justify-between gap-3"
        ):
            ui.label("Concept by human. Crafted by human + AI.").classes(
                "pykim-footer-claim"
            )
            with ui.row().classes("items-center gap-4"):
                ui.label(f"Version {pykim.__version__}").classes(
                    "pykim-footer-version"
                )
                ui.link(
                    "PyKIM auf GitHub",
                    "https://github.com/finalnode/PyKIM",
                    new_tab=True,
                ).classes("pykim-footer-link")
                ui.link(
                    "MIT-Lizenz",
                    "https://github.com/finalnode/PyKIM/blob/main/LICENSE",
                    new_tab=True,
                ).classes("pykim-footer-link")


__all__ = ["WorkspaceLayout", "render_workspace_footer", "render_workspace_header"]
