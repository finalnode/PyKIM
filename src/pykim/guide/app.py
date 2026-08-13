"""NiceGUI-Prototyp für Setup, Aufgabenübersicht und Dokubuch."""

import argparse
import base64
import asyncio
import json
import platform
import threading
import webbrowser
from pathlib import Path

import pykim
from pykim.trainer.exercises import exercise_names, get_exercise
from pykim.trainer.activities import get_activity
from pykim.trainer.assignments import get_assignment
from .course_setup import (
    activate_installed_course_content,
    course_import_target,
    course_setup_info,
    install_course_archive,
    install_course_setup,
    install_new_course_archive,
    install_new_course_setup,
    setup_info,
    sync_installed_course_content,
)
from .branding import APP_DISPLAY_NAME
from .course_archive import (
    MAX_ARCHIVE_SIZE,
    course_content_source,
    parse_course_archive,
)
from .course_studio_view import register_course_studio_page
# Der verschlüsselte Abgabeexport ist vorerst ausgeblendet und bleibt als
# getrennte technische Vorarbeit erhalten; er ist kein Teil der Kurs-Setupdatei.
from pykim.submission.export import (
    course_certificate_info,
    create_encrypted_submission,
    install_course_certificate,
)

from .content import CHEATSHEET, PYODIDE_PLAYGROUND, PYXEL_REFERENCE
from .course_catalog import load_course_catalog
from .author_view import render_authoring_view
from .activity_view import (
    current_parsons_order,
    parsons_html,
    render_matching_activity,
    saved_activity_value,
)
from .library import (
    PACKAGED_CONTENT_ROOT,
    PARADIGMS,
    render_task_markdown,
    task_documents,
    task_hints,
    task_sources,
)
from .learning_view import (
    friendly_python_error,
    render_overview,
    render_task_hints,
    render_task_sources,
    render_test_results as render_exercise_test_results,
)
from .course import (
    create_course,
    exercise_file,
    get_course_directories,
    get_course_directory,
    get_ide_preference,
    get_runtime_preference,
    get_student_name,
    reset_exercise_file,
    set_course_directory,
    set_ide_preference,
    set_runtime_preference,
    trash_course,
)
from .runtime import (
    bundled_wheelhouse,
    discover_runtimes,
    is_managed_runtime,
    provision_managed_runtime,
    repair_runtime,
    runtime_diagnostics,
)
from .examples_view import render_examples_view
from .pyxel_examples_view import render_pyxel_examples_view
from .projects_view import render_projects_view
from .extensions_view import render_extensions_view
from .execution import execution_manager, script_example_manager
from .execution_security import ACTIVE_PROTECTION
from .progress import (
    clear_exercise_progress,
    load_progress,
    save_journal_entry,
    save_task_answer,
)
from .script_view import render_script_reader
from .script_api import register_script_api
from .theme import configure_theme
from .updates import check_updates, install_content_update, format_content_version
from .navigation import create_navigation
from .system import (
    detected_ides,
    install_or_repair_pyxel,
    open_path,
    open_in_preferred_ide,
    read_student_source,
    run_student_program,
    save_student_source,
    source_hash,
    SourceConflictError,
    system_status,
    system_user_name,
)

IDE_LABELS = {
    "system": "Systemstandard",
    "thonny": "Thonny",
    "vscode": "VS Code",
    "pycharm": "PyCharm",
}


def _preferred_ide_label() -> str:
    preference = get_ide_preference()
    if preference["ide"] == "custom":
        path = Path(preference["path"])
        return path.stem if path.name else "eigener IDE"
    return IDE_LABELS.get(preference["ide"], "IDE")


def course_name_confirmation_matches(value: object, expected: str) -> bool:
    """Prüfe den aktuellen Eingabewert ohne verzögerten UI-Zustand."""
    return isinstance(value, str) and value == expected


def prepare_windows_browser_fallback(
    event_manager,
    url: str,
    *,
    delay: float = 12.0,
    opener=webbrowser.open,
) -> threading.Event:
    """Öffne bei einem hängenden nativen Windows-Fenster den Browser."""
    window_shown = threading.Event()
    event_manager.on("shown", lambda _: window_shown.set())

    def open_if_needed() -> None:
        if window_shown.wait(delay):
            return
        print(
            "Das native Windows-Fenster wurde nicht rechtzeitig sichtbar; "
            f"öffne {APP_DISPLAY_NAME} im Standardbrowser unter {url}"
        )
        opener(url)

    threading.Thread(
        target=open_if_needed,
        name="pykim-windows-browser-fallback",
        daemon=True,
    ).start()
    return window_shown


def parse_arguments(arguments: list[str] | None = None) -> argparse.Namespace:
    """Lese die bewusst kleine Kommandozeile der Suite."""
    parser = argparse.ArgumentParser(description=f"{APP_DISPLAY_NAME} starten")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="im normalen Browser statt als Desktopfenster starten",
    )
    return parser.parse_args(arguments)


def app_icon_path() -> Path | str:
    """Nutze im Checkout das echte PyKIM-Icon und sonst den Emoji-Fallback."""
    project_icon = (
        Path(__file__).resolve().parents[3]
        / "packaging"
        / "macos"
        / "assets"
        / "app-icon-master.png"
    )
    bundled_icon = Path(__file__).resolve().parent / "assets" / "app-icon.png"
    if bundled_icon.is_file():
        return bundled_icon
    return project_icon if project_icon.is_file() else "🤖"


def browser_favicon() -> str:
    """Bette das kleine Icon direkt ein und umgehe den aggressiven Favicon-Cache."""
    favicon = Path(__file__).resolve().parent / "assets" / "app-icon-64.png"
    if not favicon.is_file():
        return "🤖"
    encoded = base64.b64encode(favicon.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def apply_macos_app_icon(icon: Path | str) -> bool:
    """Setze auch beim Start aus dem Quellcode das macOS-Dock-Icon."""
    if not isinstance(icon, Path) or not icon.is_file():
        return False
    try:
        from AppKit import NSApplication, NSImage

        image = NSImage.alloc().initWithContentsOfFile_(str(icon))
        if image is None:
            return False
        NSApplication.sharedApplication().setApplicationIconImage_(image)
        return True
    except Exception:
        return False


def configure_native_app_icon(native_config, icon: Path | str) -> bool:
    """Reiche das Icon an den separaten pywebview/Cocoa-Prozess weiter."""
    if not isinstance(icon, Path) or not icon.is_file():
        return False
    native_config.start_args["icon"] = str(icon)
    return True


def main(
    *,
    show: bool = True,
    native: bool | None = None,
    arguments: list[str] | None = None,
    run_server: bool = True,
) -> None:
    desktop = not parse_arguments(arguments).browser if native is None else native
    try:
        from nicegui import app as nicegui_app, run as nicegui_run, ui
    except ImportError:
        raise RuntimeError(
            f"{APP_DISPLAY_NAME} benötigt NiceGUI. Installiere es mit "
            "pip install 'pykim[guide]'."
        ) from None

    register_script_api(nicegui_app)
    register_course_studio_page(
        ui, nicegui_app, nicegui_run, desktop=desktop
    )

    course_sync_state: dict[str, object] = {
        "result": None,
        "error": "",
        "pending": False,
    }
    course_selection_state = {"confirmed": False}

    @ui.page("/")
    def index() -> None:
        ide_open_buttons = []
        dirty_exercises: set[str] = set()
        # Farben des OSZ KIM: kräftiges Orange, technisches Grau und Weiß.
        configure_theme(ui)

        async def confirm_external_course_import(
            course_name: str = "der ausgewählte Kurs",
            source: str = "",
        ) -> bool:
            """Hole vor dem Einrichten einer externen Kursquelle Zustimmung ein."""
            with ui.dialog() as security_dialog, ui.card().classes("w-full max-w-xl"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("security", color="warning", size="md")
                    ui.label("Externe Kursquelle importieren?").classes(
                        "text-xl font-bold"
                    )
                ui.label(course_name).classes("font-bold")
                if source:
                    ui.label(source).classes("text-sm text-grey-7 break-all")
                ui.label(
                    "Die Suite prüft Struktur und Trainerdateien beim Import. "
                    "Python-Programme aus Kursen laufen derzeit jedoch noch nicht "
                    "auf jedem Betriebssystem in einer garantierten OS-Sandbox."
                )
                ui.label(
                    "Erst beim späteren, bewussten Start eines Programms kann dessen "
                    "Code mit deinen Benutzerrechten auf Dateien, Netzwerk oder "
                    "weitere Systemfunktionen zugreifen. Importiere deshalb nur "
                    "Kurse aus einer Quelle, der du vertraust."
                ).classes("text-warning")
                trust = ui.checkbox(
                    "Ich vertraue der Quelle und möchte den Kurs importieren."
                )
                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button(
                        "Abbrechen",
                        on_click=lambda: security_dialog.submit(False),
                    ).props("flat")
                    confirm_button = ui.button(
                        "Kurs importieren",
                        icon="download",
                        on_click=lambda: security_dialog.submit(True),
                    ).props("color=warning")
                    confirm_button.disable()
                trust.on_value_change(
                    lambda event: (
                        confirm_button.enable()
                        if event.value
                        else confirm_button.disable()
                    )
                )
            return bool(await security_dialog)

        async def choose_course_collision(info) -> str | None:
            """Frage bei einem belegten Ziel nach Kopie, Update oder Abbruch."""
            target = course_import_target(info)
            if not target.exists():
                return "reuse"
            with ui.dialog() as collision_dialog, ui.card().classes("w-full max-w-xl"):
                ui.label("Kurs ist bereits vorhanden").classes("text-xl font-bold")
                ui.label(
                    f"Der reguläre Kursordner „{target.name}“ existiert bereits."
                )
                ui.label(
                    "Als zweiten Kurs anlegen bewahrt beide Kursstände getrennt. "
                    "Beim Aktualisieren bleiben vorhandene Schülerlösungen, Projekte "
                    "und Lernstände erhalten; nur die aktive Kursquelle wird ersetzt."
                ).classes("text-sm text-grey-7")
                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button(
                        "Abbrechen",
                        on_click=lambda: collision_dialog.submit(None),
                    ).props("flat")
                    ui.button(
                        "Bestehenden aktualisieren",
                        icon="sync",
                        on_click=lambda: collision_dialog.submit("reuse"),
                    ).props("outline color=warning")
                    ui.button(
                        "Als zweiten Kurs anlegen",
                        icon="content_copy",
                        on_click=lambda: collision_dialog.submit("copy"),
                    ).props("color=primary")
            result = await collision_dialog
            return result if result in {"reuse", "copy"} else None

        if not course_selection_state["confirmed"]:
            async def select_course(course: Path, card, button, sync_activity) -> None:
                card.classes(add="pykim-course-opening")
                sync_activity.set_visibility(True)
                button.text = "Wird geöffnet …"
                button.disable()
                await ui.run_javascript(
                    "await new Promise(resolve => requestAnimationFrame("
                    "() => requestAnimationFrame(resolve)))"
                )
                set_course_directory(course)
                course_sync_state.update(result=None, error="", pending=True)
                try:
                    await asyncio.gather(
                        nicegui_run.io_bound(
                            activate_installed_course_content, course
                        ),
                        asyncio.sleep(1.05),
                    )
                except Exception as error:
                    course_sync_state["error"] = str(error)
                course_selection_state["confirmed"] = True
                ui.navigate.reload()

            with ui.column().classes(
                "w-full max-w-4xl mx-auto items-stretch gap-3 p-6"
            ):
                with ui.row().classes("w-full items-baseline gap-3"):
                    ui.label(APP_DISPLAY_NAME).classes("text-2xl font-bold text-primary")
                    ui.label("Kurs auswählen").classes("text-lg text-grey-7")
                    ui.space()
                    ui.button(
                        "Kurs erstellen",
                        icon="inventory_2",
                        on_click=lambda: ui.navigate.to("/course-builder"),
                    ).props("flat")
                known_courses = get_course_directories()
                for course in known_courses:
                    try:
                        info = course_setup_info(course)
                    except (OSError, ValueError):
                        info = None
                    with ui.card().classes(
                        "w-full py-2 px-3 shadow-none border gap-1"
                    ) as course_card:
                        with ui.row().classes("w-full items-center no-wrap gap-3"):
                            ui.icon("school", color="primary", size="sm")
                            with ui.column().classes("grow gap-0 min-w-0"):
                                ui.label(
                                    info.course if info is not None else course.name
                                ).classes("font-bold")
                                details = (
                                    f"{info.school} · {info.teacher}"
                                    if info is not None
                                    else str(course)
                                )
                            ui.label(details).classes(
                                    "text-sm text-grey-7 ellipsis"
                                )
                            def open_course_folder(selected=course) -> None:
                                try:
                                    open_path(selected)
                                except (OSError, RuntimeError) as error:
                                    ui.notify(
                                        f"Ordner konnte nicht geöffnet werden: {error}",
                                        type="negative",
                                    )

                            ui.button(
                                icon="folder_open",
                                on_click=open_course_folder,
                            ).props("flat round dense").tooltip("Kursordner öffnen")
                            open_course_button = ui.button(
                                "Öffnen",
                                icon="arrow_forward",
                            ).props("flat dense")
                            expected_name = (
                                info.course if info is not None else course.name
                            )
                            with ui.dialog() as delete_dialog, ui.card().classes(
                                "w-full max-w-lg"
                            ):
                                ui.label("Kurs in den Papierkorb verschieben?").classes(
                                    "text-xl font-bold"
                                )
                                ui.label(
                                    "Schülerlösungen, Antworten und Lernstand in diesem "
                                    "Kursordner werden ebenfalls verschoben. Der Vorgang kann "
                                    "über den Systempapierkorb rückgängig gemacht werden."
                                )
                                ui.label(
                                    f"Gib zur Bestätigung exakt „{expected_name}“ ein."
                                ).classes("text-negative")
                                delete_name = ui.input("Kursname").classes("w-full")

                                async def delete_selected_course(
                                    button,
                                    selected=course,
                                    dialog=delete_dialog,
                                ) -> None:
                                    button.disable()
                                    try:
                                        await nicegui_run.io_bound(trash_course, selected)
                                        dialog.close()
                                        ui.notify(
                                            "Der Kurs wurde in den Papierkorb verschoben.",
                                            type="positive",
                                        )
                                        ui.navigate.reload()
                                    except Exception as error:
                                        ui.notify(
                                            f"Kurs konnte nicht gelöscht werden: {error}",
                                            type="negative",
                                        )
                                        button.enable()

                                with ui.row().classes("w-full justify-end"):
                                    ui.button(
                                        "Abbrechen",
                                        on_click=delete_dialog.close,
                                    ).props("flat")
                                    confirm_delete = ui.button(
                                        "In Papierkorb",
                                        icon="delete",
                                    ).props("color=negative")
                                    confirm_delete.disable()
                                    confirm_delete.on(
                                        "click",
                                        lambda _, action=delete_selected_course,
                                        button=confirm_delete: action(button),
                                    )
                                delete_name.on_value_change(
                                    lambda event,
                                    button=confirm_delete,
                                    expected=expected_name: (
                                        button.enable()
                                        if course_name_confirmation_matches(
                                            event.value, expected
                                        )
                                        else button.disable()
                                    ),
                                )
                            ui.button(
                                icon="delete_outline",
                                on_click=delete_dialog.open,
                            ).props("flat round dense color=negative").tooltip(
                                "Kurs löschen"
                            )
                        with ui.column().classes(
                            "w-full items-center gap-1 py-1 text-positive"
                        ) as course_sync_activity:
                            with ui.row().classes("items-center justify-center gap-2"):
                                ui.icon("sync", size="sm").classes(
                                    "pykim-course-sync-icon"
                                )
                                ui.label(
                                    "Lokaler Kurs wird geladen · Online-Abgleich folgt"
                                ).classes("pykim-course-sync-dots text-sm font-medium")
                        course_sync_activity.set_visibility(False)
                        pixel_palette = (
                            ("#f36b2b", "#ffd166"),
                            ("#00a8e8", "#70d6ff"),
                            ("#9b5de5", "#f15bb5"),
                            ("#21ba45", "#8bd450"),
                            ("#ff9f1c", "#ff4d6d"),
                        )
                        ui.html(
                            "".join(
                                '<span style="'
                                f'--pixel-x:{(index * 37 + index * index * 3) % 94 + 2}%;'
                                f'--pixel-y:{(index * 53 + index * index * 7) % 78 + 8}%;'
                                f'--pixel-size:{0.46 + (index % 4) * 0.12:.2f}rem;'
                                f'--pixel-delay:-{(index * 0.23) % 3.7:.2f}s;'
                                f'--pixel-duration:{2.25 + (index % 6) * 0.31:.2f}s;'
                                f'--pixel-color-a:{pixel_palette[index % len(pixel_palette)][0]};'
                                f'--pixel-color-b:{pixel_palette[index % len(pixel_palette)][1]}'
                                '"></span>'
                                for index in range(32)
                            ),
                            sanitize=False,
                        ).classes("pykim-course-pixel-field").props(
                            "aria-hidden=true"
                        )
                        open_course_button.on(
                            "click",
                            lambda _, selected=course, card=course_card,
                            button=open_course_button,
                            activity=course_sync_activity: select_course(
                                selected, card, button, activity
                            ),
                        )
                if not known_courses:
                    ui.label("Noch kein Kurs eingerichtet.").classes("text-grey-7")

                ui.separator()
                with ui.row().classes("w-full items-center gap-3 no-wrap"):
                    with ui.column().classes("grow gap-0"):
                        ui.label("Kurs hinzufügen").classes("font-bold")
                        ui.label(
                            "Eine .pykim-setup-Datei oder ein portables Kurs-ZIP auswählen."
                        ).classes("text-sm text-grey-7")

                    async def upload_new_course(event) -> None:
                        course_upload.disable()
                        try:
                            data = await event.file.read()
                            filename = event.file.name or "Ausgewählte Kursdatei"
                            is_archive = filename.casefold().endswith(".zip")
                            if is_archive:
                                bundle = await nicegui_run.io_bound(
                                    parse_course_archive, data
                                )
                                info = bundle.setup
                                source = f"Lokales ZIP-Archiv · {filename}"
                            elif filename.casefold().endswith(".pykim-setup"):
                                info = setup_info(data)
                                source = info.repository
                            else:
                                raise ValueError(
                                    "Wähle eine .pykim-setup- oder .zip-Datei."
                                )
                            course_import_activity.set_visibility(False)
                            if not await confirm_external_course_import(
                                info.course, source
                            ):
                                course_upload.reset()
                                ui.notify("Kursimport abgebrochen.", type="info")
                                return
                            collision = await choose_course_collision(info)
                            if collision is None:
                                course_upload.reset()
                                ui.notify("Kursimport abgebrochen.", type="info")
                                return
                            course_import_activity.set_visibility(True)
                            installer = (
                                install_new_course_archive
                                if is_archive
                                else install_new_course_setup
                            )
                            info, course = await nicegui_run.io_bound(
                                installer, data, collision=collision
                            )
                            course_selection_state["confirmed"] = True
                            ui.notify(
                                f"{info.course} wurde eingerichtet.",
                                type="positive",
                            )
                            ui.navigate.reload()
                        except Exception as error:
                            ui.notify(
                                f"Kurs konnte nicht eingerichtet werden: {error}",
                                type="negative",
                            )
                            course_upload.reset()
                        finally:
                            course_upload.enable()
                            course_import_activity.set_visibility(False)

                    def begin_course_import() -> None:
                        course_import_activity.set_visibility(True)

                    def reject_course_import() -> None:
                        course_import_activity.set_visibility(False)
                        ui.notify(
                            "Die Kursdatei konnte nicht hochgeladen werden.",
                            type="negative",
                        )

                    with ui.column().classes("w-72 items-stretch gap-2"):
                        course_upload = ui.upload(
                            label="Setupdatei oder Kurs-ZIP auswählen",
                            on_begin_upload=begin_course_import,
                            on_upload=upload_new_course,
                            on_rejected=reject_course_import,
                            auto_upload=True,
                            max_files=1,
                            max_file_size=MAX_ARCHIVE_SIZE,
                        ).props("accept=.pykim-setup,.zip flat bordered").classes("w-full")
                        with ui.column().classes(
                            "w-full gap-1 rounded border p-3 bg-orange-1"
                        ) as course_import_activity:
                            with ui.row().classes("items-center gap-2"):
                                ui.spinner(size="sm", color="primary")
                                ui.label("Kurs wird eingerichtet …").classes("font-bold")
                            ui.linear_progress(value=None, color="primary").props(
                                "indeterminate rounded"
                            )
                            ui.label(
                                "Kursdatei und Inhalte werden geprüft und eingerichtet. "
                                "Bei Online-Kursen kann der erste Import etwas dauern."
                            ).classes("text-xs text-grey-7")
                        course_import_activity.set_visibility(False)

                ui.separator()
                with ui.row().classes("w-full items-center gap-2"):
                    ui.icon("public", color="primary")
                    with ui.column().classes("grow gap-0"):
                        ui.label("Freie Kurse entdecken").classes("font-bold")
                        ui.label(
                            "Öffentliche PyKIM-Kurse direkt aus dem Kurskatalog installieren."
                        ).classes("text-sm text-grey-7")
                    catalog_refresh_button = ui.button(
                        "Katalog aktualisieren", icon="refresh"
                    ).props("flat dense")
                catalog_container = ui.column().classes("w-full gap-2")
                catalog_state = {"courses": load_course_catalog(online=False)}

                def render_course_catalog() -> None:
                    catalog_container.clear()
                    installed_repositories = set()
                    for path in get_course_directories():
                        try:
                            installed_setup = course_setup_info(path)
                        except (OSError, ValueError):
                            installed_setup = None
                        if installed_setup is not None:
                            installed_repositories.add(
                                installed_setup.repository.removesuffix(".git")
                            )
                    with catalog_container:
                        for catalog_course in catalog_state["courses"]:
                            installed = (
                                catalog_course.setup.repository.removesuffix(".git")
                                in installed_repositories
                            )
                            caption = " · ".join(catalog_course.tags)
                            if installed:
                                caption += " · Installiert"
                            with ui.expansion(
                                f"{catalog_course.setup.course} · {catalog_course.level}",
                                caption=caption,
                                icon="menu_book",
                            ).classes("w-full border rounded").props(
                                "header-class='text-primary'"
                            ):
                                ui.label(catalog_course.description).classes(
                                    "text-sm text-grey-8"
                                )
                                with ui.row().classes("w-full items-center gap-2"):
                                    ui.label(
                                        f"{catalog_course.setup.school} · "
                                        f"{catalog_course.setup.teacher}"
                                    ).classes("text-xs text-grey-6")
                                    ui.space()
                                    ui.link(
                                        "Repository ansehen",
                                        catalog_course.setup.repository.removesuffix(".git"),
                                        new_tab=True,
                                    ).classes("text-xs text-primary")
                                with ui.row().classes(
                                    "w-full items-center justify-end gap-2"
                                ):
                                    if installed:
                                        ui.badge("Bereits installiert", color="positive")
                                    else:
                                        install_button = ui.button(
                                            "Installieren", icon="download"
                                        ).props("outline color=primary")
                                        install_status = ui.row().classes(
                                            "items-center gap-2 text-primary"
                                        )
                                        with install_status:
                                            ui.spinner(size="sm", color="primary")
                                            ui.label("Kurs wird geladen …")
                                        install_status.set_visibility(False)

                                        async def install_catalog_course(
                                            item=catalog_course,
                                            button=install_button,
                                            status=install_status,
                                        ) -> None:
                                            button.disable()
                                            try:
                                                if not await confirm_external_course_import(
                                                    item.setup.course,
                                                    item.setup.repository,
                                                ):
                                                    button.enable()
                                                    return
                                                collision = await choose_course_collision(
                                                    item.setup
                                                )
                                                if collision is None:
                                                    button.enable()
                                                    return
                                                status.set_visibility(True)
                                                info, _course = await nicegui_run.io_bound(
                                                    install_new_course_setup,
                                                    item.setup_data,
                                                    collision=collision,
                                                )
                                                course_selection_state["confirmed"] = True
                                                course_sync_state.update(
                                                    result=None, error="", pending=False
                                                )
                                                ui.notify(
                                                    f"{info.course} wurde installiert.",
                                                    type="positive",
                                                )
                                                ui.navigate.reload()
                                            except Exception as error:
                                                status.set_visibility(False)
                                                button.enable()
                                                ui.notify(
                                                    f"Kursinstallation fehlgeschlagen: {error}",
                                                    type="negative",
                                                )

                                        install_button.on(
                                            "click",
                                            lambda _, action=install_catalog_course: action(),
                                        )

                async def refresh_course_catalog() -> None:
                    catalog_refresh_button.disable()
                    try:
                        catalog_state["courses"] = await nicegui_run.io_bound(
                            load_course_catalog
                        )
                        render_course_catalog()
                        ui.notify("Kurskatalog wurde aktualisiert.", type="positive")
                    finally:
                        catalog_refresh_button.enable()

                catalog_refresh_button.on("click", refresh_course_catalog)
                render_course_catalog()
            return

        ui.link("Zum Hauptinhalt springen", "#pykim-main").classes("pykim-skip-link")
        with ui.header().classes("pykim-header"):
            with ui.row().classes("pykim-header-top w-full items-center no-wrap"):
                configured = get_course_directory()
                header_setup = None
                if configured is not None:
                    try:
                        header_setup = course_setup_info(configured)
                    except (OSError, ValueError):
                        header_setup = None
                ui.label(APP_DISPLAY_NAME).classes("text-xl font-bold")
                if header_setup is not None:
                    ui.label(f"· {header_setup.course}").classes(
                        "text-lg font-medium text-white"
                    )
                ui.space()
                current_student = get_student_name(configured) or system_user_name()
                ui.label(f"Hallo, {current_student}").classes("text-sm")
                update_badge = ui.badge("Updates werden geprüft …", color="grey")
                update_badge.classes("cursor-pointer").props(
                    "title='Verfügbare Updates anzeigen' role=button tabindex=0"
                )
                ui.button(
                    "Kurs wechseln",
                    on_click=lambda: (
                        course_selection_state.update(confirmed=False),
                        ui.navigate.reload(),
                    ),
                    icon="swap_horiz",
                ).props("flat dense color=white")
                ui.label(
                    "Kein Kursordner" if configured is None else str(configured)
                ).classes("pykim-course-path text-sm")

            tabs, (
                setup_tab,
                tools_tab,
                overview_tab,
                tasks_tab,
                examples_tab,
                projects_tab,
                extensions_tab,
                submission_tab,
                sheet_tab,
                script_tab,
                pyxel_tab,
                browser_tab,
            ) = create_navigation(ui)

        with ui.tab_panels(tabs, value=overview_tab).classes(
            "w-full max-w-6xl mx-auto mb-10"
        ).props("id=pykim-main role=main"):
            with ui.tab_panel(setup_tab):
                ui.label("Kursordner einrichten").classes("text-2xl font-bold")
                ui.markdown(
                    "Der Ordner darf auf einem lokalen, USB- oder eingebundenen "
                    "WebDAV-Laufwerk liegen. Vorhandene Lösungen werden nicht überschrieben."
                )
                default = str(get_course_directory() or Path.home() / "PyKIM-Kurs")
                with ui.row().classes("w-full items-end gap-2"):
                    path = ui.input("Kursordner", value=default).classes("grow")

                    def initial_browser_directory() -> Path:
                        candidate = Path(path.value or Path.home()).expanduser()
                        while not candidate.is_dir() and candidate != candidate.parent:
                            candidate = candidate.parent
                        return candidate if candidate.is_dir() else Path.home()

                    async def open_course_browser() -> None:
                        if desktop and nicegui_app.native.main_window is not None:
                            import webview

                            selected = await nicegui_app.native.main_window.create_file_dialog(
                                dialog_type=webview.FileDialog.FOLDER,
                                directory=str(initial_browser_directory()),
                            )
                            if selected:
                                path.set_value(str(Path(selected[0]).resolve()))
                            return
                        try:
                            show_directory(initial_browser_directory())
                            folder_dialog.open()
                        except OSError as error:
                            ui.notify(str(error), type="warning")

                    ui.button(
                        "Ordner auswählen",
                        on_click=open_course_browser,
                        icon="folder_open",
                    )

                with ui.dialog() as folder_dialog, ui.card().classes("w-full max-w-2xl"):
                    ui.label("Kursordner auswählen").classes("text-xl font-bold")
                    current_directory = ui.input("Aktueller Ordner").classes("w-full")
                    current_directory.props("readonly")
                    directory_list = ui.column().classes(
                        "w-full gap-1 max-h-96 overflow-y-auto border rounded p-2"
                    )

                    def show_directory(directory: Path) -> None:
                        selected = directory.expanduser().resolve()
                        try:
                            children = sorted(
                                (entry for entry in selected.iterdir() if entry.is_dir()),
                                key=lambda entry: entry.name.casefold(),
                            )
                        except (OSError, PermissionError) as error:
                            ui.notify(f"Ordner nicht lesbar: {error}", type="warning")
                            return

                        current_directory.set_value(str(selected))
                        directory_list.clear()
                        with directory_list:
                            if selected != selected.parent:
                                ui.button(
                                    "..  Übergeordneter Ordner",
                                    on_click=lambda parent=selected.parent: show_directory(parent),
                                    icon="drive_folder_upload",
                                ).props("flat").classes("w-full justify-start")
                            for child in children[:250]:
                                ui.button(
                                    child.name,
                                    on_click=lambda target=child: show_directory(target),
                                    icon="folder",
                                ).props("flat").classes("w-full justify-start")
                            if len(children) > 250:
                                ui.label(
                                    "Es werden nur die ersten 250 Unterordner angezeigt."
                                ).classes("text-sm text-grey-7")

                    def use_current_directory() -> None:
                        path.set_value(current_directory.value)
                        folder_dialog.close()

                    with ui.row().classes("w-full justify-end"):
                        ui.button("Abbrechen", on_click=folder_dialog.close).props("flat")
                        ui.button(
                            "Diesen Ordner verwenden",
                            on_click=use_current_directory,
                            icon="check",
                        )

                student = ui.input(
                    "Dein Name oder Kürzel (optional)",
                    value=current_student,
                    placeholder="z. B. Ada L. oder ada-l",
                ).classes("w-full")
                ui.label(
                    "Diese Angabe wird nur im Kursordner gespeichert, damit du deine "
                    "Unterlagen und deinen Lernfortschritt zuordnen kannst."
                ).classes("text-sm text-grey-7")

                ui.separator()
                ui.label("Bevorzugte Entwicklungsumgebung").classes("text-xl font-bold")
                installed_ides = detected_ides()
                ide_labels = {**IDE_LABELS, "custom": "Eigener Programmpfad"}
                available_ide_options = {"system": ide_labels["system"]}
                available_ide_options.update(
                    {
                        key: f"{ide_labels[key]} – gefunden"
                        for key in ("thonny", "vscode", "pycharm")
                        if key in installed_ides
                    }
                )
                available_ide_options["custom"] = ide_labels["custom"]
                preference = get_ide_preference()
                selected_ide = (
                    preference["ide"]
                    if preference["ide"] in available_ide_options
                    else "system"
                )
                ide_choice = ui.radio(
                    available_ide_options,
                    value=selected_ide,
                ).props("inline")
                custom_ide_path = ui.input(
                    "Pfad zur eigenen IDE oder .app-Datei",
                    value=preference["path"],
                    placeholder="z. B. /Applications/Meine IDE.app",
                ).classes("w-full")
                ui.label("Die Auswahl wird automatisch gespeichert.").classes(
                    "text-sm text-grey-7"
                )

                def save_ide() -> None:
                    if ide_choice.value == "custom" and not custom_ide_path.value:
                        return
                    try:
                        saved = set_ide_preference(
                            ide_choice.value,
                            custom_ide_path.value or "",
                        )
                        ui.notify(
                            f"Standard-IDE gespeichert: {ide_labels[saved['ide']]}",
                            type="positive",
                        )
                        button_text = f"In {_preferred_ide_label()} öffnen"
                        for button in ide_open_buttons:
                            button.set_text(button_text)
                    except ValueError as error:
                        ui.notify(str(error), type="negative")

                ide_choice.on_value_change(lambda _: save_ide())
                custom_ide_path.on_value_change(lambda _: save_ide())

                ui.separator()
                ui.label("Python-Laufzeit für Aufgaben").classes("text-xl font-bold")
                ui.label(
                    "Die Suite und die Entwicklungsumgebung verwenden für Schülerprogramme "
                    "denselben geprüften Interpreter."
                ).classes("text-sm text-grey-7")
                offline_wheels = bundled_wheelhouse()
                ui.label(
                    "Offline-Pakete gefunden: Die Einrichtung benötigt kein Internet."
                    if offline_wheels
                    else "Noch kein Offline-Paket eingebunden: Für die Einrichtung kann Internetzugang erforderlich sein."
                ).classes("text-sm text-positive" if offline_wheels else "text-sm text-orange")
                runtimes = discover_runtimes(path.value or None)
                runtime_options = {
                    item.executable: (
                        f"Python {item.version or '?'} · {item.source} · "
                        + (
                            "bereit"
                            if item.supported and item.pykim and item.pyxel
                            else " · ".join(
                                problem for problem, applies in (
                                    ("Python-Version ungeeignet", not item.supported),
                                    ("PyKIM fehlt", not item.pykim),
                                    ("Pyxel fehlt", not item.pyxel),
                                ) if applies
                            )
                        )
                    )
                    for item in runtimes
                }
                ready_runtime_paths = {
                    item.executable for item in runtimes
                    if item.supported and item.pykim and item.pyxel
                }
                configured_runtime = get_runtime_preference()
                runtime_value = (
                    configured_runtime
                    if configured_runtime in runtime_options
                    else next(iter(ready_runtime_paths), None)
                )
                runtime_choice = ui.select(
                    runtime_options,
                    value=runtime_value,
                    label="Interpreter",
                ).classes("w-full")

                def save_runtime() -> None:
                    if not runtime_choice.value:
                        return
                    if runtime_choice.value not in ready_runtime_paths:
                        runtime_setup_confirmation.open()
                        return
                    try:
                        set_runtime_preference(runtime_choice.value)
                        ui.notify("Python-Laufzeit gespeichert.", type="positive")
                    except ValueError as error:
                        ui.notify(str(error), type="negative")

                runtime_choice.on_value_change(lambda _: save_runtime())
                if not ready_runtime_paths:
                    ui.label(
                        "Noch keine vollständige Laufzeit mit PyKIM und Pyxel gefunden."
                    ).classes("text-orange")
                incomplete = [
                    item for item in runtimes
                    if not (item.supported and item.pykim and item.pyxel)
                ]
                for item in incomplete:
                    missing = []
                    if not item.supported:
                        missing.append("Python-Version ungeeignet")
                    if not item.pykim:
                        missing.append("PyKIM fehlt")
                    if not item.pyxel:
                        missing.append("Pyxel fehlt")
                    ui.label(
                        f"{item.source}: {item.executable} – {', '.join(missing)}"
                    ).classes("text-xs text-grey-7")

                async def provision_selected_runtime() -> None:
                    selected = runtime_choice.value
                    if not selected:
                        return
                    runtime_setup_confirmation.close()
                    runtime_setup_button.disable()
                    runtime_activity.set_visibility(True)
                    try:
                        ready = await nicegui_run.io_bound(
                            provision_managed_runtime,
                            path.value,
                            selected,
                        )
                        ui.notify(
                            f"Python {ready.version}: PyKIM-Laufzeit ist bereit.",
                            type="positive",
                        )
                        runtime_choice.options[ready.executable] = (
                            f"Python {ready.version} · PyKIM-Kursumgebung · bereit"
                        )
                        runtime_choice.set_value(ready.executable)
                        runtime_choice.update()
                        runtime_repair_button.enable()
                    except Exception as error:
                        ui.notify(f"Einrichtung fehlgeschlagen: {error}", type="negative")
                        runtime_choice.set_value(runtime_value)
                    finally:
                        runtime_activity.set_visibility(False)
                        runtime_setup_button.enable()

                with ui.dialog() as runtime_setup_confirmation, ui.card():
                    ui.label("PyKIM-Laufzeit einrichten?").classes("text-xl font-bold")
                    ui.label(
                        "Die Suite erstellt außerhalb des Kursordners eine isolierte "
                        "Python-Umgebung und installiert dort PyKIM und Pyxel."
                    )
                    ui.label(
                        "Aufgaben, Projekte und Lernstand werden nicht verändert."
                    ).classes("text-sm text-grey-7")
                    with ui.row().classes("justify-end w-full"):
                        ui.button(
                            "Abbrechen",
                            on_click=lambda: (
                                runtime_setup_confirmation.close(),
                                runtime_choice.set_value(runtime_value),
                            ),
                        ).props("flat")
                        runtime_setup_button = ui.button(
                            "Umgebung einrichten",
                            on_click=provision_selected_runtime,
                            icon="build",
                        )

                async def repair_selected_runtime() -> None:
                    runtime_repair_confirmation.close()
                    runtime_repair_button.disable()
                    runtime_activity.set_visibility(True)
                    try:
                        ready = await nicegui_run.io_bound(repair_runtime, path.value)
                        ui.notify(
                            f"Python {ready.version}: Laufzeit wurde erfolgreich repariert.",
                            type="positive",
                        )
                    except Exception as error:
                        ui.notify(f"Reparatur fehlgeschlagen: {error}", type="negative")
                    finally:
                        runtime_activity.set_visibility(False)
                        runtime_repair_button.enable()

                with ui.row().classes("items-center gap-2"):
                    runtime_repair_button = ui.button(
                        "Laufzeit reparieren",
                        on_click=lambda: runtime_repair_confirmation.open(),
                        icon="handyman",
                    ).props("outline")
                    runtime_activity = ui.spinner(size="lg", color="primary")
                    runtime_activity.set_visibility(False)
                    if not (
                        configured_runtime
                        and is_managed_runtime(configured_runtime, path.value)
                    ):
                        runtime_repair_button.disable()
                        runtime_repair_button.tooltip(
                            "Wähle oder erstelle zuerst eine verwaltete PyKIM-Kursumgebung."
                        )

                    def copy_runtime_diagnostics() -> None:
                        import json

                        report = json.dumps(
                            runtime_diagnostics(path.value),
                            ensure_ascii=False,
                            indent=2,
                        )
                        ui.clipboard.write(report)
                        ui.notify("Runtime-Diagnose wurde kopiert.", type="positive")

                    ui.button(
                        "Diagnose kopieren",
                        on_click=copy_runtime_diagnostics,
                        icon="content_copy",
                    ).props("flat")

                with ui.dialog() as runtime_repair_confirmation, ui.card():
                    ui.label("PyKIM-Laufzeit reparieren?").classes("text-xl font-bold")
                    ui.label(
                        "PyKIM, Pyxel und benötigte Pakete werden in der verwalteten "
                        "Kursumgebung erneut installiert."
                    )
                    ui.label("Schülerdateien werden nicht verändert.").classes("text-sm text-grey-7")
                    with ui.row().classes("w-full justify-end"):
                        ui.button("Abbrechen", on_click=runtime_repair_confirmation.close).props("flat")
                        ui.button(
                            "Jetzt reparieren",
                            on_click=repair_selected_runtime,
                            icon="handyman",
                        )

                def setup() -> None:
                    try:
                        result = create_course(path.value, student.value)
                        ui.notify(
                            f"{len(result['created'])} Dateien angelegt; "
                            f"{len(result['existing'])} vorhandene Dateien behalten.",
                            type="positive",
                        )
                    except OSError as error:
                        ui.notify(f"Setup fehlgeschlagen: {error}", type="negative")

                ui.button("Kursordner anlegen oder ergänzen", on_click=setup, icon="create_new_folder")

                ui.separator()
                ui.label("Kursdatei und Lerninhalte").classes("text-xl font-bold")
                ui.label(
                    "Eine Setupdatei lädt den Kurs aus seinem Repository. Ein portables "
                    "Kurs-ZIP enthält denselben geprüften Stand für die vollständig "
                    "offline nutzbare Einrichtung."
                ).classes("text-sm text-grey-7")
                setup_certificate_status = ui.column().classes("w-full gap-1")

                def render_setup_certificate() -> None:
                    setup_certificate_status.clear()
                    course = Path(path.value).expanduser().resolve()
                    with setup_certificate_status:
                        try:
                            info = course_setup_info(course)
                        except (OSError, ValueError) as error:
                            ui.label(f"Setupdatei ungültig: {error}").classes("text-negative")
                            return
                        if info is None:
                            ui.label("Noch keine Kurs-Setupdatei importiert.").classes("text-grey-7")
                        else:
                            ui.label(f"Kurs: {info.course}").classes("font-bold")
                            source = course_content_source(course)
                            if source.get("type") == "archive":
                                ui.label("Quelle: lokales Kurs-ZIP · offline")
                            else:
                                ui.label(f"{info.repository} · {info.branch}")

                async def import_setup_certificate(
                    data: bytes,
                    filename: str = "course.pykim-setup",
                ) -> None:
                    course = Path(path.value).expanduser().resolve()
                    if not course.is_dir():
                        ui.notify("Lege zuerst den Kursordner an.", type="warning")
                        return
                    is_archive = filename.casefold().endswith(".zip")
                    if is_archive:
                        bundle = await nicegui_run.io_bound(parse_course_archive, data)
                        candidate = bundle.setup
                        source = f"Lokales ZIP-Archiv · {filename}"
                    elif filename.casefold().endswith(".pykim-setup"):
                        candidate = setup_info(data)
                        source = candidate.repository
                    else:
                        ui.notify(
                            "Wähle eine .pykim-setup- oder .zip-Datei.",
                            type="negative",
                        )
                        return
                    if not await confirm_external_course_import(
                        candidate.course,
                        source,
                    ):
                        ui.notify("Kursimport abgebrochen.", type="info")
                        return
                    certificate_activity.set_visibility(True)
                    certificate_button.disable()
                    try:
                        installer = (
                            install_course_archive
                            if is_archive
                            else install_course_setup
                        )
                        info = await nicegui_run.io_bound(
                            installer, data, course
                        )
                        render_setup_certificate()
                        from pykim.trainer.activities import refresh_activities
                        from pykim.trainer.exercises import refresh_exercises
                        refresh_exercises()
                        refresh_activities()
                        ui.notify(
                            f"Setupdatei für {info.course} importiert; Lerninhalte wurden aktiviert.",
                            type="positive", timeout=5000,
                        )
                        ui.navigate.reload()
                    except Exception as error:
                        ui.notify(f"Import oder Synchronisierung fehlgeschlagen: {error}", type="negative")
                    finally:
                        certificate_activity.set_visibility(False)
                        certificate_button.enable()

                async def choose_setup_certificate() -> None:
                    if not desktop or nicegui_app.native.main_window is None:
                        return
                    import webview

                    selected = await nicegui_app.native.main_window.create_file_dialog(
                        dialog_type=webview.FileDialog.OPEN,
                        directory=str(Path.home() / "Downloads"),
                    )
                    if selected:
                        certificate_path = Path(selected[0])
                        if not (
                            certificate_path.name.casefold().endswith(".pykim-setup")
                            or certificate_path.suffix.casefold() == ".zip"
                        ):
                            ui.notify(
                                "Wähle eine .pykim-setup- oder .zip-Datei.",
                                type="negative",
                            )
                            return
                        await import_setup_certificate(
                            certificate_path.read_bytes(), certificate_path.name
                        )

                async def upload_setup_certificate(event) -> None:
                    await import_setup_certificate(
                        await event.file.read(), event.file.name
                    )

                with ui.row().classes("items-center gap-2"):
                    if desktop:
                        certificate_button = ui.button(
                            "Setupdatei oder Kurs-ZIP auswählen",
                            on_click=choose_setup_certificate,
                            icon="settings_suggest",
                        ).props("outline")
                    else:
                        certificate_button = ui.upload(
                            label="Setupdatei oder Kurs-ZIP auswählen",
                            on_upload=upload_setup_certificate,
                            auto_upload=True,
                            max_file_size=MAX_ARCHIVE_SIZE,
                        ).props("accept=.pykim-setup,.zip")
                    with ui.column().classes("gap-1") as certificate_activity:
                        with ui.row().classes("items-center gap-2"):
                            ui.spinner(size="sm", color="primary")
                            ui.label("Kursinhalt wird geprüft und eingerichtet …")
                        ui.linear_progress(value=None, color="primary").props(
                            "indeterminate rounded"
                        ).classes("w-72")
                    certificate_activity.set_visibility(False)
                render_setup_certificate()

                ui.separator()
                ui.label("Systemcheck").classes("text-xl font-bold")
                status = system_status()

                def status_line(text: str, available: bool = True) -> None:
                    with ui.row().classes("items-center gap-2"):
                        ui.icon(
                            "check_circle" if available else "info",
                            color="positive" if available else "grey",
                        )
                        ui.label(text)

                with ui.column().classes("w-full gap-1"):
                    status_line(
                        f"Python {status.python}"
                        + ("" if status.python_supported else " – benötigt wird mindestens 3.10"),
                        status.python_supported,
                    )
                    status_line(f"PyKIM {status.pykim}")
                    status_line("Pyxel installiert" if status.pyxel else "Pyxel fehlt", status.pyxel)
                    status_line("Thonny gefunden" if status.thonny else "Thonny nicht gefunden", status.thonny)
                    status_line("VS Code gefunden" if status.vscode else "VS Code nicht gefunden", status.vscode)
                ui.label("Schutz bei Codeausführung").classes("font-bold mt-2")
                with ui.column().classes("w-full gap-1"):
                    status_line("Schülercode läuft in einem getrennten Prozess")
                    status_line(
                        "Integrierte Aufgabenläufe begrenzen Laufzeit und gespeicherte Ausgabe"
                    )
                    status_line("Typische Zugangsdaten werden nicht weitergegeben")
                    status_line(
                        "Noch keine aktive Betriebssystem-Sandbox für Dateisystem und Netzwerk",
                        ACTIVE_PROTECTION.os_sandbox_active,
                    )
                ui.label(ACTIVE_PROTECTION.summary).classes(
                    "text-sm text-orange-8"
                )
                with ui.row().classes("items-center gap-3"):
                    ui.link(
                        "Thonny herunterladen",
                        "https://thonny.org/",
                        new_tab=True,
                    )
                    ui.link(
                        "VS Code herunterladen",
                        "https://code.visualstudio.com/download",
                        new_tab=True,
                    )
                    ui.link(
                        "Python herunterladen",
                        "https://www.python.org/downloads/",
                        new_tab=True,
                    )

                def repair_pyxel() -> None:
                    try:
                        install_or_repair_pyxel()
                        ui.notify(
                            f"Pyxel wurde installiert bzw. repariert. Bitte {APP_DISPLAY_NAME} neu starten.",
                            type="positive",
                        )
                    except Exception as error:
                        ui.notify(f"Pyxel-Installation fehlgeschlagen: {error}", type="negative")

                with ui.dialog() as pyxel_confirmation, ui.card():
                    ui.label("Pyxel installieren oder reparieren?").classes("font-bold")
                    ui.code(
                        f'{__import__("sys").executable} -m pip install --upgrade "pyxel>=2.2,<3"',
                        language="bash",
                    )
                    ui.label("Der Kursordner und alle Schülerlösungen bleiben unverändert.")
                    with ui.row():
                        ui.button("Abbrechen", on_click=pyxel_confirmation.close).props("flat")
                        ui.button(
                            "Installation starten",
                            on_click=lambda: (pyxel_confirmation.close(), repair_pyxel()),
                        )
                ui.button(
                    "Pyxel installieren / reparieren",
                    on_click=pyxel_confirmation.open,
                    icon="build",
                ).props("outline")

            with ui.tab_panel(tools_tab):
                ui.label("IDE, Dateien und Updates").classes("text-2xl font-bold")
                ui.markdown(
                    "Diese Werkzeuge werden lokal gestartet und öffnen sich in einem "
                    f"**eigenen Fenster** neben {APP_DISPLAY_NAME}."
                )
                course = get_course_directory()
                if course is None:
                    ui.label("Richte zuerst im Setup einen Kursordner ein.").classes("text-orange")
                else:
                    def start_local(action, success: str) -> None:
                        try:
                            action()
                            ui.notify(success, type="positive")
                        except (OSError, RuntimeError, ValueError) as error:
                            ui.notify(f"Start fehlgeschlagen: {error}", type="negative")

                    with ui.row():
                        ui.button(
                            "Kursordner öffnen",
                            on_click=lambda: start_local(
                                lambda: open_path(course), "Kursordner wurde geöffnet."
                            ),
                            icon="folder_open",
                        )
                        ui.button(
                            "In bevorzugter IDE öffnen",
                            on_click=lambda: start_local(
                                lambda: open_in_preferred_ide(course),
                                "Bevorzugte IDE wurde gestartet.",
                            ),
                            icon="terminal",
                        )
                        if system_status().thonny:
                            ui.button(
                                "In Thonny öffnen",
                                on_click=lambda: start_local(
                                    lambda: open_path(course, "thonny"), "Thonny wurde gestartet."
                                ),
                                icon="school",
                            )
                        if system_status().vscode:
                            ui.button(
                                "In VS Code öffnen",
                                on_click=lambda: start_local(
                                    lambda: open_path(course, "vscode"), "VS Code wurde gestartet."
                                ),
                                icon="code",
                            )

                    ui.separator()
                    ui.label("Pyxel-Ressourceneditor").classes("text-xl font-bold")
                    ui.markdown(
                        "Ressourcendateien gehören immer zu einem Projekt. Lege unter "
                        "**Meine Projekte** ein Pyxel-Spiel an und öffne dort den "
                        "Sprite- und Musikeditor."
                    )
                    ui.button(
                        "Zu meinen Projekten",
                        on_click=lambda: tabs.set_value(projects_tab),
                        icon="folder_special",
                    )

                ui.separator()
                ui.label("Updates").classes("text-xl font-bold").props("id=pykim-updates")
                ui.label(
                    "App und Lerninhalte werden getrennt geprüft. Schülerlösungen und "
                    "Lernstand werden dabei niemals verändert."
                ).classes("text-grey-7")
                startup_sync = course_sync_state["result"]
                startup_sync_error = str(course_sync_state["error"])
                if startup_sync_error:
                    course_sync_text = (
                        "Kursrepository beim Start nicht erreichbar: "
                        f"{startup_sync_error}"
                    )
                    course_sync_class = "text-warning"
                elif startup_sync is not None and startup_sync.checked_online:
                    course_sync_text = (
                        "Kursrepository beim Start abgeglichen: "
                        + startup_sync.message
                    )
                    course_sync_class = "text-positive"
                else:
                    course_sync_text = (
                        startup_sync.message
                        if startup_sync is not None
                        else "Kursrepository wurde noch nicht abgeglichen."
                    )
                    course_sync_class = "text-grey-7"
                course_sync_label = ui.label(course_sync_text).classes(course_sync_class)
                app_update_label = ui.label("App-Version wird geprüft …")
                content_update_label = ui.label("Inhaltsversion wird geprüft …")
                update_state: dict[str, object] = {"status": None}

                async def refresh_course_content() -> None:
                    course_sync_button.disable()
                    course_sync_label.text = "Kursrepository wird abgeglichen …"
                    update_badge.text = "Kursabgleich läuft …"
                    update_badge.props("color=positive")
                    try:
                        result = await nicegui_run.io_bound(
                            sync_installed_course_content
                        )
                        course_sync_state["result"] = result
                        course_sync_state["error"] = ""
                        course_sync_label.text = result.message
                        if not result.checked_online:
                            ui.notify(result.message, type="warning")
                        elif result.updated:
                            ui.notify(
                                "Neue Kursinhalte wurden aktiviert.",
                                type="positive",
                            )
                            ui.navigate.reload()
                        else:
                            ui.notify("Die Kursinhalte sind aktuell.", type="positive")
                    except Exception as error:
                        course_sync_state["error"] = str(error)
                        course_sync_label.text = f"Kursabgleich fehlgeschlagen: {error}"
                        ui.notify(
                            f"Kursabgleich fehlgeschlagen: {error}",
                            type="negative",
                        )
                    finally:
                        course_sync_state["pending"] = False
                        status = update_state["status"]
                        if course_sync_state["error"]:
                            update_badge.text = "Kursabgleich offline"
                            update_badge.props("color=warning")
                        elif (
                            status is not None
                            and status.app is not None
                            and status.app.newer
                        ):
                            update_badge.text = "Update verfügbar"
                            update_badge.props("color=orange")
                        else:
                            update_badge.text = "Aktuell"
                            update_badge.props("color=positive")
                        course_sync_button.enable()
                        refresh_update_dialog()

                def open_app_download() -> None:
                    status = update_state["status"]
                    if status is None or status.app is None:
                        return
                    target = status.app.download_url or status.app.release_url
                    if target:
                        ui.navigate.to(target, new_tab=True)
                        update_dialog.close()

                async def activate_content_update() -> None:
                    status = update_state["status"]
                    if status is None or status.content is None:
                        return
                    try:
                        await nicegui_run.io_bound(
                            install_content_update, status.content.manifest
                        )
                        content_update_label.text = (
                            f"Inhalte {status.content.available} wurden aktiviert."
                        )
                        content_button.disable()
                        dialog_content_button.disable()
                        dialog_content_button.set_visibility(False)
                        dialog_content_label.text = (
                            f"Inhalte {format_content_version(status.content.available)} "
                            "wurden aktiviert."
                        )
                        ui.notify(
                            f"Neue Lerninhalte aktiviert. Bitte {APP_DISPLAY_NAME} neu starten.",
                            type="positive",
                        )
                    except Exception as error:
                        ui.notify(f"Inhaltsupdate fehlgeschlagen: {error}", type="negative")

                with ui.row().classes("items-center"):
                    course_sync_button = ui.button(
                        "Kursinhalte abgleichen",
                        on_click=refresh_course_content,
                        icon="sync",
                    ).props("outline")
                    app_button = ui.button(
                        "App-Update öffnen", on_click=open_app_download, icon="download"
                    )
                    content_button = ui.button(
                        "Lerninhalte aktualisieren",
                        on_click=activate_content_update,
                        icon="library_books",
                    )
                    refresh_button = ui.button(
                        "Jetzt prüfen", icon="refresh"
                    ).props("outline")
                app_button.disable()
                content_button.disable()

                async def update_dialog_content() -> None:
                    if header_setup is not None:
                        await refresh_course_content()
                    else:
                        await activate_content_update()

                with ui.dialog() as update_dialog, ui.card().classes(
                    "w-[38rem] max-w-[95vw] gap-4"
                ):
                    with ui.row().classes("w-full items-center gap-2"):
                        ui.icon("system_update", size="md").classes("text-primary")
                        ui.label(f"{APP_DISPLAY_NAME} aktualisieren").classes("text-xl font-bold")
                        ui.space()
                        ui.button(icon="close", on_click=update_dialog.close).props(
                            "flat round dense aria-label='Dialog schließen'"
                        )
                    ui.label(
                        f"Prüfe getrennt, ob eine neue Version von {APP_DISPLAY_NAME} oder neue Lerninhalte "
                        "bereitstehen. Du entscheidest, was installiert wird."
                    ).classes("text-grey-7")
                    with ui.card().classes("w-full shadow-none border"):
                        ui.label("Desktop-App").classes("font-bold")
                        dialog_app_label = ui.label("App-Version wird geprüft …")
                        dialog_app_button = ui.button(
                            "App herunterladen",
                            on_click=open_app_download,
                            icon="download",
                        )
                    with ui.card().classes("w-full shadow-none border"):
                        dialog_content_title = ui.label("Lerninhalte").classes("font-bold")
                        dialog_content_label = ui.label(
                            "Inhaltsversion wird geprüft …"
                        )
                        dialog_content_button = ui.button(
                            "Lerninhalte aktualisieren",
                            on_click=update_dialog_content,
                            icon="library_books",
                        )
                    dialog_update_hint = ui.label().classes("text-grey-7")
                    with ui.row().classes("w-full justify-end"):
                        ui.button("Später", on_click=update_dialog.close).props("flat")
                dialog_app_button.disable()
                dialog_content_button.disable()
                dialog_app_button.set_visibility(False)
                dialog_content_button.set_visibility(False)

                def refresh_update_dialog() -> None:
                    status = update_state["status"]
                    if status is None:
                        dialog_app_label.text = "App-Version wird geprüft …"
                        dialog_content_label.text = "Inhaltsversion wird geprüft …"
                        dialog_update_hint.text = "Die Updateprüfung läuft."
                        dialog_app_button.disable()
                        dialog_content_button.disable()
                        dialog_app_button.set_visibility(False)
                        dialog_content_button.set_visibility(False)
                        return

                    app_newer = status.app is not None and status.app.newer
                    content_newer = (
                        header_setup is None
                        and status.content is not None
                        and status.content.newer
                    )
                    if status.app is None:
                        dialog_app_label.text = "App-Prüfung ist momentan nicht verfügbar."
                        dialog_app_button.disable()
                        dialog_app_button.set_visibility(False)
                    elif app_newer:
                        dialog_app_label.text = (
                            f"Version {status.app.available} ist verfügbar; installiert "
                            f"ist {status.app.installed}."
                        )
                        dialog_app_button.enable()
                        dialog_app_button.set_visibility(True)
                    else:
                        dialog_app_label.text = (
                            f"Version {status.app.installed} ist bereits aktuell."
                        )
                        dialog_app_button.disable()
                        dialog_app_button.set_visibility(False)

                    if header_setup is not None:
                        dialog_content_title.text = "Kursinhalte"
                        dialog_content_button.text = "Kurs jetzt abgleichen"
                        dialog_content_button.set_visibility(True)
                        dialog_content_button.enable()
                        sync_result = course_sync_state["result"]
                        sync_error = str(course_sync_state["error"])
                        if sync_error:
                            dialog_content_label.text = (
                                f"Der letzte Abgleich ist fehlgeschlagen: {sync_error}"
                            )
                        elif sync_result is not None and sync_result.checked_online:
                            dialog_content_label.text = (
                                f"{header_setup.course}: {sync_result.message}"
                            )
                        else:
                            dialog_content_label.text = (
                                f"{header_setup.course} kann jetzt mit dem Kursrepository "
                                "abgeglichen werden."
                            )
                    elif status.content is None:
                        dialog_content_title.text = "Lerninhalte"
                        dialog_content_button.text = "Lerninhalte aktualisieren"
                        dialog_content_label.text = (
                            "Die Inhaltsprüfung ist momentan nicht verfügbar."
                        )
                        dialog_content_button.disable()
                        dialog_content_button.set_visibility(False)
                    elif content_newer and status.content.compatible:
                        dialog_content_label.text = (
                            f"Inhalte {format_content_version(status.content.available)} "
                            "sind verfügbar; aktiv ist "
                            f"{format_content_version(status.content.installed)}."
                        )
                        dialog_content_button.enable()
                        dialog_content_button.set_visibility(True)
                    elif not status.content.compatible:
                        dialog_content_label.text = (
                            "Die neuen Lerninhalte benötigen zuerst das App-Update."
                        )
                        dialog_content_button.disable()
                        dialog_content_button.set_visibility(False)
                    else:
                        dialog_content_label.text = (
                            "Die Lerninhalte "
                            f"{format_content_version(status.content.installed)} sind aktuell."
                        )
                        dialog_content_button.disable()
                        dialog_content_button.set_visibility(False)

                    if header_setup is not None:
                        dialog_update_hint.text = (
                            "App und ausgewählter Kurs werden unabhängig aktualisiert."
                        )
                    elif app_newer or content_newer:
                        dialog_update_hint.text = (
                            "Wähle die gewünschte Aktualisierung oder verschiebe sie mit „Später“."
                        )
                    else:
                        dialog_update_hint.text = "Es ist keine Aktualisierung erforderlich."

                async def refresh_updates() -> None:
                    refresh_button.disable()
                    update_badge.text = "Updates werden geprüft …"
                    try:
                        status = await nicegui_run.io_bound(
                            check_updates, PACKAGED_CONTENT_ROOT
                        )
                        update_state["status"] = status
                        if status.app is None:
                            app_update_label.text = "App-Prüfung nicht verfügbar."
                            app_button.disable()
                        elif status.app.newer:
                            app_update_label.text = (
                                f"Neue App: {status.app.available} · installiert: "
                                f"{status.app.installed}"
                            )
                            app_button.enable()
                        else:
                            app_update_label.text = (
                                f"App {status.app.installed} ist aktuell."
                            )
                            app_button.disable()
                        if header_setup is not None:
                            content_update_label.text = (
                                "Kursinhalte werden über das Repository des ausgewählten "
                                "Kurses aktualisiert."
                            )
                            content_button.disable()
                        elif status.content is None:
                            content_update_label.text = "Inhaltsprüfung nicht verfügbar."
                            content_button.disable()
                        elif status.content.newer and status.content.compatible:
                            content_update_label.text = (
                                "Neue Lerninhalte: "
                                f"{format_content_version(status.content.available)} · aktiv: "
                                f"{format_content_version(status.content.installed)}"
                            )
                            content_button.enable()
                        elif not status.content.compatible:
                            content_update_label.text = (
                                "Die neuen Inhalte benötigen zuerst ein App-Update."
                            )
                            content_button.disable()
                        else:
                            content_update_label.text = (
                                "Lerninhalte "
                                f"{format_content_version(status.content.installed)} sind aktuell."
                            )
                            content_button.disable()
                        if status.error:
                            update_badge.text = "Updateprüfung teilweise offline"
                            update_badge.props("color=warning")
                        elif (
                            (status.app is not None and status.app.newer)
                            or (
                                header_setup is None
                                and status.content is not None
                                and status.content.newer
                            )
                        ):
                            update_badge.text = "Update verfügbar"
                            update_badge.props("color=orange")
                        else:
                            update_badge.text = "Aktuell"
                            update_badge.props("color=positive")
                        refresh_update_dialog()
                    finally:
                        refresh_button.enable()

                async def open_update_dialog() -> None:
                    refresh_update_dialog()
                    update_dialog.open()
                    if update_state["status"] is None:
                        await refresh_updates()

                refresh_button.on("click", refresh_updates)
                update_badge.on("click", open_update_dialog)
                ui.timer(0.2, refresh_updates, once=True)
                if course_sync_state["pending"]:
                    ui.timer(0.35, refresh_course_content, once=True)

                author_course = get_course_directory()
                if author_course is not None and course_setup_info(author_course) is not None:
                    render_authoring_view(ui)

            with ui.tab_panel(overview_tab):
                overview_container = ui.column().classes("w-full")

                def refresh_overview() -> None:
                    overview_container.clear()
                    with overview_container:
                        overview_course = get_course_directory()
                        if (
                            overview_course is not None
                            and course_setup_info(overview_course) is not None
                        ):
                            render_overview(ui)
                        else:
                            ui.label(APP_DISPLAY_NAME).classes("text-2xl font-bold")
                            ui.label(
                                "Lege zuerst einen Kursordner an und importiere die "
                                ".pykim-setup-Datei deiner Lehrkraft. Danach erscheinen "
                                "hier Skript, Aufgaben und Lernstand."
                            ).classes("text-grey-7")

                refresh_overview()

            with ui.tab_panel(tasks_tab):
                progress = load_progress()
                journal = progress.get("journal", {})
                answers = progress.get("answers", {})
                ui.label("Aufgaben und Testfälle").classes("text-2xl font-bold")
                current_paradigm = None
                tasks_course = get_course_directory()
                has_course_setup = (
                    tasks_course is not None
                    and course_setup_info(tasks_course) is not None
                )
                visible_tasks = tuple(
                    document
                    for paradigm in PARADIGMS
                    for document in task_documents(paradigm)
                ) if has_course_setup else ()
                if not visible_tasks:
                    ui.label(
                        "Noch kein Kurs eingerichtet. Importiere im Setup die "
                        ".pykim-setup-Datei deiner Lehrkraft."
                    ).classes("text-grey-7")
                trainable_names = set(exercise_names())
                material_tasks = tuple(
                    document for document in visible_tasks
                    if document.name not in trainable_names
                )
                if material_tasks:
                    ui.separator()
                    ui.label("Weitere Aufgaben").classes(
                        "text-xl font-bold text-primary"
                    )
                    ui.label(
                        "Freie Antworten und interaktive Zuordnungsaufgaben."
                    ).classes("text-grey-7")
                    for material in material_tasks:
                        with ui.expansion(material.title, icon="description").classes(
                            "w-full"
                        ):
                            hint_key = f"{material.paradigm}/{material.name}"
                            ui.markdown(
                                render_task_markdown(material.content)
                            ).classes("prose max-w-none")
                            render_task_sources(ui, task_sources(material.content))
                            render_task_hints(
                                ui, hint_key, task_hints(material.content)
                            )
                            activity = get_activity(material.name)
                            if activity is not None and activity.mode == "matching":
                                render_matching_activity(
                                    ui, activity, paradigm=material.paradigm
                                )
                                continue
                            answer_key = hint_key
                            old_answer = (
                                answers.get(answer_key, {})
                                if isinstance(answers, dict)
                                else {}
                            )
                            answer = ui.textarea(
                                "Meine Antwort",
                                value=(
                                    old_answer.get("text", "")
                                    if isinstance(old_answer, dict)
                                    else ""
                                ),
                            ).props("outlined autogrow").classes("w-full")
                            ui.button(
                                "Antwort speichern",
                                on_click=lambda key=answer_key, field=answer: (
                                    save_task_answer(key, field.value),
                                    ui.notify(
                                        "Antwort wurde gespeichert.",
                                        type="positive",
                                    ),
                                ),
                                icon="save",
                            )
                for task_document in (
                    document for document in visible_tasks
                    if document.name in trainable_names
                ):
                    name = task_document.name
                    if task_document.paradigm != current_paradigm:
                        current_paradigm = task_document.paradigm
                        ui.separator()
                        ui.label(
                            "Imperative Aufgaben"
                            if current_paradigm == "imperativ"
                            else "Objektorientierte Aufgaben"
                        ).classes("text-xl font-bold text-primary")
                    exercise = get_exercise(name)
                    with ui.expansion(exercise.title, icon="task_alt").classes("w-full"):
                        assignment = get_assignment(name)
                        with ui.card().classes("w-full bg-orange-1 shadow-none"):
                            with ui.row().classes("w-full items-center"):
                                ui.label("Aufgabenstellung").classes("text-lg font-bold")
                                ui.space()
                                ui.badge(assignment.difficulty.upper(), color="primary")
                            ui.markdown(render_task_markdown(task_document.content)).classes(
                                "prose max-w-none"
                            )
                            render_task_sources(
                                ui, task_sources(task_document.content)
                            )
                        render_task_hints(
                            ui,
                            f"{task_document.paradigm}/{name}",
                            task_hints(task_document.content),
                        )
                        target = exercise_file(name)
                        activity = get_activity(name)
                        if (
                            activity is not None
                            and activity.mode == "parsons"
                            and target is not None
                        ):
                            answer_key = f"{task_document.paradigm}/{name}"
                            saved_order = saved_activity_value(answer_key)
                            order = (
                                saved_order
                                if isinstance(saved_order, list)
                                and set(saved_order) == {block.id for block in activity.blocks}
                                else [block.id for block in reversed(activity.blocks)]
                            )
                            ui.label(
                                "Ziehe die Blöcke in die richtige Reihenfolge. Mit den "
                                "Pfeiltasten an jedem Block geht es auch ohne Drag-and-drop."
                            ).classes("text-grey-7")
                            ui.html(parsons_html(activity, order), sanitize=False).classes("w-full")
                            parsons_order_status = ui.label(
                                "Ordne zuerst alle Blöcke und prüfe dann den Code."
                            ).classes("text-grey-7")
                            parsons_output = ui.code(
                                "Noch nicht ausgeführt.", language="text"
                            ).classes("w-full pykim-no-code-actions")
                            parsons_output.set_visibility(False)
                            parsons_tests = ui.column().classes("w-full gap-2")
                            with parsons_tests:
                                ui.label(
                                    "Die automatischen Tests starten erst, wenn die "
                                    "Blockreihenfolge stimmt."
                                ).classes("text-grey-7")

                            def refresh_parsons_tests(
                                exercise_name=name, container=parsons_tests,
                            ) -> None:
                                container.clear()
                                with container:
                                    render_exercise_test_results(ui, exercise_name)

                            async def run_parsons(
                                puzzle=activity,
                                path=target,
                                output=parsons_output,
                                order_status=parsons_order_status,
                                key=answer_key,
                                refresh=refresh_parsons_tests,
                            ) -> None:
                                selected_course = get_course_directory()
                                if selected_course is None:
                                    ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                                    return
                                current_order = await current_parsons_order(ui, puzzle)
                                try:
                                    source = puzzle.assemble(current_order)
                                    save_task_answer(
                                        key, json.dumps(current_order, ensure_ascii=False)
                                    )
                                except (OSError, ValueError, SourceConflictError) as error:
                                    ui.notify(f"Puzzle konnte nicht gespeichert werden: {error}", type="negative")
                                    return
                                if not puzzle.order_is_correct(current_order):
                                    order_status.text = (
                                        "Die Reihenfolge stimmt noch nicht. Verschiebe mindestens "
                                        "einen Block und prüfe erneut."
                                    )
                                    order_status.classes(
                                        add="text-negative", remove="text-grey-7 text-positive"
                                    )
                                    ui.notify(
                                        "Blockreihenfolge noch nicht korrekt – das Programm wurde "
                                        "noch nicht ausgeführt.",
                                        type="warning",
                                    )
                                    return
                                order_status.text = (
                                    "Reihenfolge korrekt. Programm und Tests werden ausgeführt …"
                                )
                                order_status.classes(
                                    add="text-positive", remove="text-grey-7 text-negative"
                                )
                                try:
                                    old_source = read_student_source(path, selected_course)
                                    save_student_source(
                                        path,
                                        source,
                                        selected_course,
                                        expected_hash=source_hash(old_source),
                                    )
                                except (OSError, ValueError, SourceConflictError) as error:
                                    ui.notify(f"Puzzle konnte nicht gespeichert werden: {error}", type="negative")
                                    return
                                output.set_visibility(True)
                                output.set_content("Programm läuft …")
                                result = await nicegui_run.io_bound(
                                    execution_manager.execute, path, selected_course
                                )
                                rendered = result.stdout
                                if result.stderr:
                                    rendered += ("\n" if rendered else "") + result.stderr
                                output.set_content(
                                    rendered.strip()
                                    or f"Programm beendet (Code {result.returncode}), ohne Ausgabe."
                                )
                                refresh()
                                refresh_overview()

                            with ui.row().classes("items-center gap-2"):
                                ui.button(
                                    "Reihenfolge prüfen und Code ausführen",
                                    on_click=run_parsons,
                                    icon="play_arrow",
                                ).props("color=primary")
                            continue
                        if target is not None:
                            course = get_course_directory()
                            try:
                                source = (
                                    read_student_source(target, course)
                                    if course is not None
                                    else ""
                                )
                            except (OSError, ValueError) as error:
                                source = ""
                                ui.label(f"Quellcode konnte nicht geladen werden: {error}").classes(
                                    "text-negative"
                                )

                            ui.label("Dein vollständiger Quellcode").classes("font-bold mt-2")
                            source_editor = ui.codemirror(
                                value=source,
                                language="Python",
                                line_wrapping=False,
                            ).classes("w-full").style("height: 24rem")

                            editor_state = {
                                "disk_hash": source_hash(source),
                                "dirty": False,
                            }
                            save_state = ui.label("Gespeichert").classes("text-grey-7 text-sm")

                            def mark_dirty(
                                _, exercise_name=name, state=editor_state,
                                label=save_state,
                            ) -> None:
                                state["dirty"] = True
                                dirty_exercises.add(exercise_name)
                                label.set_text("Ungespeicherte Änderungen")
                                label.classes(replace="text-orange-8 text-sm")
                                ui.run_javascript("window.pykimHasUnsavedChanges = true")

                            source_editor.on("change", mark_dirty)

                            action_row = ui.row()
                            with ui.expansion(
                                "Programmausgabe",
                                icon="terminal",
                            ).classes("w-full border rounded"):
                                execution_output = ui.code(
                                    "Noch keine Ausgabe in dieser Sitzung.",
                                    language="text",
                                ).classes("w-full")

                            test_results_container = ui.column().classes("w-full gap-2")

                            def render_test_results(
                                exercise_name=name,
                                container=test_results_container,
                            ) -> None:
                                container.clear()
                                with container:
                                    render_exercise_test_results(ui, exercise_name)

                            render_test_results()

                            def save_task(
                                path=target, editor=source_editor, state=editor_state,
                                label=save_state, exercise_name=name, notify=True,
                            ) -> bool:
                                selected_course = get_course_directory()
                                if selected_course is None:
                                    ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                                    return False
                                try:
                                    save_student_source(
                                        path, editor.value, selected_course,
                                        expected_hash=state["disk_hash"],
                                    )
                                    state["disk_hash"] = source_hash(editor.value)
                                    state["dirty"] = False
                                    dirty_exercises.discard(exercise_name)
                                    label.set_text("Gespeichert")
                                    label.classes(replace="text-grey-7 text-sm")
                                    ui.run_javascript(
                                        "window.pykimHasUnsavedChanges = "
                                        + str(bool(dirty_exercises)).lower()
                                    )
                                    if notify:
                                        ui.notify("Quellcode wurde gespeichert.", type="positive")
                                    return True
                                except SourceConflictError:
                                    label.set_text("Datei wurde außerhalb der Suite geändert")
                                    label.classes(replace="text-negative text-sm")
                                    ui.notify(
                                        "Die Datei wurde inzwischen in einer IDE geändert. "
                                        "Lade sie neu, damit nichts überschrieben wird.",
                                        type="warning",
                                    )
                                    return False
                                except (OSError, ValueError) as error:
                                    ui.notify(f"Speichern fehlgeschlagen: {error}", type="negative")
                                    return False

                            async def save_and_start_task(
                                path=target,
                                editor=source_editor,
                                output_view=execution_output,
                                refresh_tests=render_test_results,
                                refresh_summary=refresh_overview,
                                save_current=save_task,
                                exercise_name=name,
                                code_editor=source_editor,
                            ) -> None:
                                selected_course = get_course_directory()
                                if selected_course is None:
                                    ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                                    return
                                if execution_manager.is_running(path):
                                    ui.notify("Diese Aufgabe läuft bereits.", type="warning")
                                    return
                                if not save_current(notify=False):
                                    return
                                run_button.disable()
                                stop_button.enable()
                                run_status.set_text("LÄUFT")
                                run_status.props("color=warning")
                                try:
                                    output_view.set_content("Programm läuft …")
                                    result = await nicegui_run.io_bound(
                                        execution_manager.execute, path, selected_course
                                    )
                                    output = result.stdout
                                    if result.stderr:
                                        output += ("\n" if output else "") + result.stderr
                                    output_view.set_content(
                                        output.strip()
                                        or f"Programm beendet (Code {result.returncode}), ohne Ausgabe."
                                    )
                                    refresh_tests()
                                    refresh_summary()
                                    if result.stderr:
                                        line, message = friendly_python_error(result.stderr)
                                        code_editor.line_tooltips = {line: message} if line else {}
                                    else:
                                        code_editor.line_tooltips = {}
                                    ui.notify(
                                        "Programm wurde gestoppt."
                                        if result.stopped else "Tests aktualisiert."
                                        if result.returncode == 0
                                        else f"Programm mit Fehlercode {result.returncode} beendet.",
                                        type="warning" if result.stopped else
                                        "positive" if result.returncode == 0 else "negative",
                                    )
                                except (OSError, ValueError, RuntimeError) as error:
                                    ui.notify(str(error), type="negative")
                                finally:
                                    run_button.enable()
                                    stop_button.disable()
                                    run_status.set_text("BEREIT")
                                    run_status.props("color=grey")

                            def stop_task(path=target, output_view=execution_output) -> None:
                                if execution_manager.stop(path):
                                    output_view.set_content("Programm wird beendet …")
                                    run_status.set_text("WIRD BEENDET")
                                else:
                                    ui.notify("Diese Aufgabe läuft gerade nicht.", type="info")

                            def reload_task(
                                path=target, editor=source_editor, state=editor_state,
                                label=save_state, exercise_name=name,
                            ) -> None:
                                selected_course = get_course_directory()
                                if selected_course is None:
                                    return
                                try:
                                    current = read_student_source(path, selected_course)
                                    editor.set_value(current)
                                    state.update(disk_hash=source_hash(current), dirty=False)
                                    dirty_exercises.discard(exercise_name)
                                    label.set_text("Neu von Datei geladen")
                                    label.classes(replace="text-grey-7 text-sm")
                                    ui.run_javascript(
                                        "window.pykimHasUnsavedChanges = "
                                        + str(bool(dirty_exercises)).lower()
                                    )
                                except (OSError, ValueError) as error:
                                    ui.notify(f"Neuladen fehlgeschlagen: {error}", type="negative")

                            def reset_task(
                                exercise_name=name, editor=source_editor,
                                state=editor_state, label=save_state,
                                refresh_tests=render_test_results,
                                refresh_summary=refresh_overview,
                            ) -> None:
                                selected_course = get_course_directory()
                                if selected_course is None:
                                    return
                                try:
                                    reset_path = reset_exercise_file(exercise_name, selected_course)
                                    clear_exercise_progress(exercise_name, selected_course)
                                    current = read_student_source(reset_path, selected_course)
                                    editor.set_value(current)
                                    state.update(disk_hash=source_hash(current), dirty=False)
                                    dirty_exercises.discard(exercise_name)
                                    label.set_text("Aufgabe zurückgesetzt; Backup wurde angelegt")
                                    refresh_tests()
                                    refresh_summary()
                                    ui.notify("Aufgabe und Lernstand wurden zurückgesetzt.", type="positive")
                                except (OSError, ValueError) as error:
                                    ui.notify(f"Zurücksetzen fehlgeschlagen: {error}", type="negative")

                            def open_task_in_ide(path=target) -> None:
                                try:
                                    open_in_preferred_ide(path)
                                    ui.notify("Aufgabe wurde in der IDE geöffnet.", type="positive")
                                except (OSError, RuntimeError) as error:
                                    ui.notify(f"IDE konnte nicht gestartet werden: {error}", type="negative")

                            def copy_task_source(editor=source_editor) -> None:
                                ui.clipboard.write(editor.value)
                                ui.notify("Quellcode wurde kopiert.", type="positive")

                            with action_row:
                                ui.button(
                                    "Speichern",
                                    on_click=save_task,
                                    icon="save",
                                )
                                run_button = ui.button(
                                    "Ausführen",
                                    on_click=save_and_start_task,
                                    icon="play_arrow",
                                )
                                stop_button = ui.button(
                                    "Stoppen", on_click=stop_task, icon="stop",
                                ).props("outline")
                                stop_button.disable()
                                ui.button(
                                    "Kopieren",
                                    on_click=copy_task_source,
                                    icon="content_copy",
                                ).props("outline")
                                ide_button = ui.button(
                                    f"In {_preferred_ide_label()} öffnen",
                                    on_click=open_task_in_ide,
                                    icon="open_in_new",
                                ).props("outline")
                                ide_open_buttons.append(ide_button)
                                ui.button(
                                    "Neu laden", on_click=reload_task, icon="refresh",
                                ).props("flat")
                                with ui.dialog() as reset_dialog, ui.card():
                                    ui.label("Aufgabe wirklich zurücksetzen?").classes("font-bold")
                                    ui.label(
                                        "Quellcode und Lernstand werden zurückgesetzt. "
                                        "Vorher legt PyKIM Backups an."
                                    )
                                    with ui.row():
                                        ui.button("Abbrechen", on_click=reset_dialog.close).props("flat")
                                        ui.button(
                                            "Zurücksetzen",
                                            on_click=lambda dialog=reset_dialog, reset=reset_task: (
                                                dialog.close(), reset()
                                            ),
                                        )
                                ui.button(
                                    "Zurücksetzen", on_click=reset_dialog.open, icon="restart_alt",
                                ).props("flat color=negative")
                                run_status = ui.badge("BEREIT", color="grey")

                            source_editor.map_key("Mod-s", save_task)
                            source_editor.map_key("F5", save_and_start_task)
                        old_entry = journal.get(name, {}) if isinstance(journal, dict) else {}
                        notes = ui.textarea(
                            "Mein Dokubuch-Eintrag",
                            value=old_entry.get("text", "") if isinstance(old_entry, dict) else "",
                        ).classes("w-full")
                        ui.button(
                            "Eintrag speichern",
                            on_click=lambda exercise=name, field=notes: (
                                save_journal_entry(exercise, field.value),
                                ui.notify("Dokubuch gespeichert", type="positive"),
                            ),
                        )

            with ui.tab_panel(examples_tab):
                render_examples_view(ui, _preferred_ide_label(), ide_open_buttons)

            with ui.tab_panel(projects_tab):
                refresh_projects = render_projects_view(
                    ui, _preferred_ide_label(), ide_open_buttons
                )

            with ui.tab_panel(extensions_tab):
                render_extensions_view(ui)

            with ui.tab_panel(submission_tab):
                ui.label("Verschlüsselte Moodle-Abgabe").classes("text-2xl font-bold")
                ui.markdown(
                    "Moodle dient nur zum Hochladen der erzeugten Datei. Die Suite "
                    "überträgt selbst keine Daten. Nur die Lehrkraft mit dem privaten "
                    "Schlüssel kann den Export lesen."
                )
                submission_course = get_course_directory()
                if submission_course is None:
                    ui.label("Richte zuerst im Setup einen Kursordner ein.").classes(
                        "text-orange"
                    )
                else:
                    ui.label("1. Zertifikat der Lehrkraft").classes("text-xl font-bold")
                    certificate_container = ui.column().classes("w-full gap-1")

                    def render_certificate() -> None:
                        certificate_container.clear()
                        with certificate_container:
                            try:
                                info = course_certificate_info(submission_course)
                            except (OSError, ValueError) as error:
                                ui.label(f"Zertifikat ungültig: {error}").classes("text-negative")
                                return
                            if info is None:
                                ui.label("Noch kein Kurszertifikat importiert.").classes("text-grey-7")
                                return
                            ui.label(f"Kurs: {info.course}").classes("font-bold")
                            ui.label(f"Lehrkraft: {info.teacher}")
                            ui.label(f"Schule: {info.school}")
                            if info.content is not None:
                                ui.label("Inhaltsquelle").classes("font-bold mt-2")
                                ui.label(f"Repository: {info.content.repository}")
                                ui.label(f"Branch: {info.content.branch}")
                                if info.content.certificate_name:
                                    ui.label(
                                        f"Zertifikatshash: certificates/"
                                        f"{info.content.certificate_name}"
                                    )
                                ui.label(
                                    "Pfade: "
                                    f"{info.content.scripts_path}, "
                                    f"{info.content.assignments_path}, "
                                    f"{info.content.trainers_path}"
                                )
                            ui.label(f"Gültig bis: {info.valid_until}")
                            ui.label(f"Fingerabdruck: {info.fingerprint}").classes(
                                "font-mono text-xs break-all"
                            )

                    render_certificate()

                    def import_certificate_data(data: bytes) -> None:
                        try:
                            info = install_course_certificate(data, submission_course)
                            render_certificate()
                            ui.notify(
                                f"Zertifikat für {info.course} wurde importiert.",
                                type="positive",
                            )
                        except (OSError, ValueError) as error:
                            ui.notify(f"Import fehlgeschlagen: {error}", type="negative")

                    async def import_uploaded_certificate(event) -> None:
                        import_certificate_data(await event.file.read())

                    async def choose_native_certificate() -> None:
                        if nicegui_app.native.main_window is None:
                            return
                        import webview

                        downloads = Path.home() / "Downloads"
                        try:
                            # pywebview akzeptiert keine Bindestriche in Dateifiltern;
                            # .pykim-cert wird deshalb nach der Auswahl inhaltlich geprüft.
                            selected = await nicegui_app.native.main_window.create_file_dialog(
                                dialog_type=webview.FileDialog.OPEN,
                                directory=str(downloads if downloads.is_dir() else Path.home()),
                            )
                        except Exception as error:
                            ui.notify(f"Dateiauswahl fehlgeschlagen: {error}", type="negative")
                            return
                        if selected:
                            try:
                                certificate_path = Path(selected[0])
                                if certificate_path.suffix != ".pykim-cert":
                                    raise ValueError("Wähle eine Datei mit der Endung .pykim-cert aus.")
                                import_certificate_data(certificate_path.read_bytes())
                            except (OSError, ValueError) as error:
                                ui.notify(f"Datei konnte nicht gelesen werden: {error}", type="negative")

                    if desktop:
                        ui.button(
                            "Zertifikat auswählen",
                            on_click=choose_native_certificate,
                            icon="workspace_premium",
                        ).props("outline")
                    else:
                        ui.upload(
                            label=".pykim-cert aus dem Lernraum auswählen",
                            on_upload=import_uploaded_certificate,
                            auto_upload=True,
                            max_file_size=1_000_000,
                        ).props("accept=.pykim-cert").classes("w-full")

                    ui.separator()
                    ui.label("2. Lernstand exportieren").classes("text-xl font-bold")
                    ui.markdown(
                        "Verschlüsselt werden dein bestätigter Name, Systemname, die "
                        "aktuellen Quellcodes, letzte Testergebnisse, Leistungsübersicht "
                        "und Codefingerprints. Andere Rechnerdaten werden nicht erfasst."
                    )
                    include_journal = ui.checkbox(
                        "Meine Dokubuch-Einträge ebenfalls exportieren",
                        value=False,
                    )
                    export_result = ui.label("").classes("text-sm")

                    async def export_learning_record() -> None:
                        try:
                            target = await nicegui_run.io_bound(
                                create_encrypted_submission,
                                submission_course,
                                None,
                                include_journal=include_journal.value,
                            )
                            export_result.set_text(f"Export erstellt: {target}")
                            ui.notify("Verschlüsselte Moodle-Abgabe erstellt.", type="positive")
                            open_path(target.parent)
                        except (OSError, ValueError) as error:
                            ui.notify(f"Export fehlgeschlagen: {error}", type="negative")

                    ui.button(
                        "Verschlüsselte Abgabe erstellen",
                        on_click=export_learning_record,
                        icon="lock",
                    )

            with ui.tab_panel(sheet_tab):
                ui.markdown(CHEATSHEET).classes("prose max-w-none")
            with ui.tab_panel(script_tab):
                render_script_reader(ui)
            with ui.tab_panel(pyxel_tab):
                ui.markdown(PYXEL_REFERENCE).classes("prose max-w-none")
                ui.separator()
                render_pyxel_examples_view(
                    ui,
                    _preferred_ide_label(),
                    ide_open_buttons,
                    on_project_saved=refresh_projects,
                )
            with ui.tab_panel(browser_tab):
                ui.label("Python-Grundlagen im Browser").classes("text-2xl font-bold")
                ui.markdown(
                    "Diese Pyodide-Spielwiese ist nur für **reines Python ohne PyKIM und "
                    "Pyxel** gedacht, zum Beispiel für Variablen, Schleifen, Listen und "
                    "Funktionen. PyKIM- und Pyxel-Programme benötigen Grafik, Audio und "
                    "die lokale Runtime und werden deshalb über **Ausführen** in der Suite "
                    "gestartet."
                )
                ui.html(PYODIDE_PLAYGROUND, sanitize=False).classes("w-full")

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

    if not run_server:
        return

    nicegui_app.on_shutdown(execution_manager.stop_all)
    nicegui_app.on_shutdown(script_example_manager.stop_all)
    port = None
    icon = app_icon_path()
    if desktop and platform.system() == "Darwin":
        configure_native_app_icon(nicegui_app.native, icon)
    if desktop and platform.system() == "Windows":
        from nicegui.native.event_manager import event_manager
        from nicegui.native.native_mode import find_open_port

        port = find_open_port()
        prepare_windows_browser_fallback(
            event_manager,
            f"http://127.0.0.1:{port}/",
        )
    ui.run(
        title=f"{APP_DISPLAY_NAME} {pykim.__version__}",
        favicon=browser_favicon(),
        host="127.0.0.1",
        port=port,
        reload=False,
        show=show and not desktop,
        native=desktop,
        window_size=(1280, 850) if desktop else None,
    )


if __name__ == "__main__":
    main()
