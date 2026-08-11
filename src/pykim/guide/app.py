"""NiceGUI-Prototyp für Setup, Aufgabenübersicht und Dokubuch."""

import argparse
from pathlib import Path

from pykim.trainer.exercises import get_exercise
from pykim.trainer.assignments import get_assignment
from pykim.submission.export import (
    course_certificate_info,
    create_encrypted_submission,
    install_course_certificate,
)

from .content import CHEATSHEET, PYODIDE_PLAYGROUND, PYXEL_REFERENCE
from .author_view import render_authoring_view
from .library import (
    PACKAGED_CONTENT_ROOT,
    PARADIGMS,
    render_task_markdown,
    task_documents,
)
from .learning_view import (
    friendly_python_error,
    render_overview,
    render_test_results as render_exercise_test_results,
)
from .course import (
    create_course,
    exercise_file,
    get_course_directory,
    get_ide_preference,
    get_runtime_preference,
    get_student_name,
    reset_exercise_file,
    set_ide_preference,
    set_runtime_preference,
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
from .execution import execution_manager, script_example_manager
from .progress import clear_exercise_progress, load_progress, save_journal_entry
from .script_view import render_script_reader
from .script_api import register_script_api
from .theme import configure_theme
from .updates import check_updates, install_content_update
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


def parse_arguments(arguments: list[str] | None = None) -> argparse.Namespace:
    """Lese die bewusst kleine Kommandozeile des Begleithefts."""
    parser = argparse.ArgumentParser(description="PyKIM-Lernstudio starten")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="im normalen Browser statt als Desktopfenster starten",
    )
    return parser.parse_args(arguments)


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
            "Das Begleitheft benötigt NiceGUI. Installiere es mit "
            "pip install 'pykim[guide]'."
        ) from None

    register_script_api(nicegui_app)

    @ui.page("/")
    def index() -> None:
        ide_open_buttons = []
        dirty_exercises: set[str] = set()
        # Farben des OSZ KIM: kräftiges Orange, technisches Grau und Weiß.
        configure_theme(ui)
        ui.link("Zum Hauptinhalt springen", "#pykim-main").classes("pykim-skip-link")
        with ui.header().classes("pykim-header"):
            with ui.row().classes("pykim-header-top w-full items-center no-wrap"):
                ui.label("PyKIM-Begleitheft").classes("text-xl font-bold")
                ui.space()
                configured = get_course_directory()
                current_student = get_student_name(configured) or system_user_name()
                ui.label(f"Hallo, {current_student}").classes("text-sm")
                update_badge = ui.badge("Updates werden geprüft …", color="grey")
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
                submission_tab,
                sheet_tab,
                script_tab,
                pyxel_tab,
                browser_tab,
            ) = create_navigation(ui)

        with ui.tab_panels(tabs, value=overview_tab).classes(
            "w-full max-w-6xl mx-auto"
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
                            "Pyxel wurde installiert bzw. repariert. Bitte Suite neu starten.",
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
                    "**eigenen Fenster** neben dem PyKIM-Lernstudio."
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
                ui.label("Updates").classes("text-xl font-bold")
                ui.label(
                    "App und Lerninhalte werden getrennt geprüft. Schülerlösungen und "
                    "Lernstand werden dabei niemals verändert."
                ).classes("text-grey-7")
                app_update_label = ui.label("App-Version wird geprüft …")
                content_update_label = ui.label("Inhaltsversion wird geprüft …")
                update_state: dict[str, object] = {"status": None}

                def open_app_download() -> None:
                    status = update_state["status"]
                    if status is None or status.app is None:
                        return
                    target = status.app.download_url or status.app.release_url
                    if target:
                        ui.navigate.to(target, new_tab=True)

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
                        ui.notify(
                            "Neue Lerninhalte aktiviert. Bitte die Suite neu starten.",
                            type="positive",
                        )
                    except Exception as error:
                        ui.notify(f"Inhaltsupdate fehlgeschlagen: {error}", type="negative")

                with ui.row().classes("items-center"):
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
                        if status.content is None:
                            content_update_label.text = "Inhaltsprüfung nicht verfügbar."
                            content_button.disable()
                        elif status.content.newer and status.content.compatible:
                            content_update_label.text = (
                                f"Neue Lerninhalte: {status.content.available} · aktiv: "
                                f"{status.content.installed}"
                            )
                            content_button.enable()
                        elif not status.content.compatible:
                            content_update_label.text = (
                                "Die neuen Inhalte benötigen zuerst ein App-Update."
                            )
                            content_button.disable()
                        else:
                            content_update_label.text = (
                                f"Lerninhalte {status.content.installed} sind aktuell."
                            )
                            content_button.disable()
                        if status.error:
                            update_badge.text = "Updateprüfung teilweise offline"
                            update_badge.props("color=warning")
                        elif (
                            (status.app is not None and status.app.newer)
                            or (status.content is not None and status.content.newer)
                        ):
                            update_badge.text = "Update verfügbar"
                            update_badge.props("color=orange")
                        else:
                            update_badge.text = "Aktuell"
                            update_badge.props("color=positive")
                    finally:
                        refresh_button.enable()

                refresh_button.on("click", refresh_updates)
                ui.timer(0.2, refresh_updates, once=True)

                render_authoring_view(ui)

            with ui.tab_panel(overview_tab):
                overview_container = ui.column().classes("w-full")

                def refresh_overview() -> None:
                    overview_container.clear()
                    with overview_container:
                        render_overview(ui)

                refresh_overview()

            with ui.tab_panel(tasks_tab):
                progress = load_progress()
                journal = progress.get("journal", {})
                ui.label("Aufgaben und Testfälle").classes("text-2xl font-bold")
                current_paradigm = None
                for task_document in (
                    document
                    for paradigm in PARADIGMS
                    for document in task_documents(paradigm)
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
                        target = exercise_file(name)
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
                render_projects_view(ui, _preferred_ide_label(), ide_open_buttons)

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
                    ui, _preferred_ide_label(), ide_open_buttons
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

    if not run_server:
        return

    nicegui_app.on_shutdown(execution_manager.stop_all)
    nicegui_app.on_shutdown(script_example_manager.stop_all)
    ui.run(
        title="PyKIM-Begleitheft",
        favicon="🤖",
        host="127.0.0.1",
        reload=False,
        show=show and not desktop,
        native=desktop,
        window_size=(1280, 850) if desktop else None,
    )


if __name__ == "__main__":
    main()
