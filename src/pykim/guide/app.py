"""NiceGUI-Prototyp für Setup, Aufgabenübersicht und Dokubuch."""

import argparse
from pathlib import Path

from pykim.trainer.exercises import exercise_names, get_exercise
from pykim.trainer.assignments import get_assignment
from pykim.submission.export import (
    course_certificate_info,
    create_encrypted_submission,
    install_course_certificate,
)

from .content import CHEATSHEET, PYODIDE_PLAYGROUND, PYXEL_REFERENCE, SCRIPT
from .course import (
    create_course,
    exercise_file,
    get_course_directory,
    get_ide_preference,
    get_student_name,
    set_ide_preference,
)
from .examples import copy_example_to_course, example_programs, launch_example
from .progress import load_progress, save_journal_entry
from .system import (
    github_version,
    detected_ides,
    execute_student_program,
    install_or_repair_pyxel,
    launch_pyxel_editor,
    launch_pyxel_example,
    open_path,
    open_in_preferred_ide,
    pyxel_examples,
    read_student_source,
    run_student_program,
    save_student_source,
    system_status,
    system_user_name,
    update_from_github,
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


def _latest_attempts(progress: dict[str, object]) -> dict[str, dict[str, object]]:
    latest: dict[str, dict[str, object]] = {}
    attempts = progress.get("attempts", [])
    if isinstance(attempts, list):
        for attempt in attempts:
            if isinstance(attempt, dict) and isinstance(attempt.get("exercise"), str):
                latest[attempt["exercise"]] = attempt
    return latest


def _render_test_results(ui, exercise_name: str) -> None:
    attempt = _latest_attempts(load_progress()).get(exercise_name)
    if attempt is None:
        with ui.card().classes("w-full bg-grey-1 shadow-none border"):
            ui.label("Automatische Tests").classes("font-bold")
            ui.label(
                "Noch kein Testlauf vorhanden. Starte dein Programm, "
                "um die einzelnen Prüffälle auszuführen."
            ).classes("text-grey-7")
        return

    tests = attempt.get("tests", [])
    passed_tests = int(attempt.get("passed", 0))
    total_tests = int(attempt.get("total", len(tests)))
    with ui.row().classes("w-full items-center gap-3 mt-3"):
        ui.label("Automatische Tests").classes("text-lg font-bold")
        ui.badge(
            f"{passed_tests} / {total_tests} bestanden",
            color="positive" if passed_tests == total_tests else "negative",
        )
    with ui.expansion("Testdetails anzeigen", icon="fact_check").classes(
        "w-full border rounded"
    ):
        for index, test in enumerate(tests, start=1):
            passed = bool(test["passed"])
            style = "pykim-test-passed" if passed else "pykim-test-failed"
            with ui.card().classes(f"w-full pykim-test-result {style}"):
                with ui.row().classes("w-full items-center"):
                    ui.icon(
                        "check_circle" if passed else "cancel",
                        color="positive" if passed else "negative",
                    )
                    ui.label(f"Testfall {index}").classes("font-bold")
                    ui.space()
                    ui.badge(
                        "BESTANDEN" if passed else "FEHLGESCHLAGEN",
                        color="positive" if passed else "negative",
                    )
                ui.label(test["message"]).classes("text-base")
                if test.get("hint"):
                    ui.label(f"Tipp: {test['hint']}").classes(
                        "w-full pykim-test-hint"
                    )


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
) -> None:
    desktop = not parse_arguments(arguments).browser if native is None else native
    try:
        from nicegui import app as nicegui_app, run as nicegui_run, ui
    except ImportError:
        raise RuntimeError(
            "Das Begleitheft benötigt NiceGUI. Installiere es mit "
            "pip install 'pykim[guide]'."
        ) from None

    @ui.page("/")
    def index() -> None:
        ide_open_buttons = []
        # Farben des OSZ KIM: kräftiges Orange, technisches Grau und Weiß.
        ui.colors(primary="#f36b2b", secondary="#9b9da0", accent="#5f6164")
        ui.add_head_html(r"""
            <style>
                pre.pykim-copy-ready {
                    position: relative;
                    padding: 1rem 7rem 1rem 1.1rem !important;
                    background: #f5f5f4 !important;
                    border: 1px solid #d7d8d9;
                    border-left: 4px solid #f36b2b;
                    border-radius: .45rem;
                    box-shadow: 0 1px 2px rgba(40, 40, 40, .06);
                }
                pre.pykim-copy-ready code {
                    background: transparent !important;
                }
                .pykim-copy-button {
                    position: absolute; top: .55rem; right: .55rem; z-index: 2;
                    border: 0; border-radius: .4rem; padding: .35rem .65rem;
                    background: #686a6d; color: white; cursor: pointer;
                    font: 500 .8rem system-ui, sans-serif;
                }
                .pykim-copy-button:hover { background: #f36b2b; }
                .pykim-playground textarea {
                    width: 100%; min-height: 15rem; padding: 1rem;
                    border: 1px solid #cfd0d1; border-left: 4px solid #f36b2b;
                    border-radius: .45rem; background: #f5f5f4;
                    font: 14px/1.5 ui-monospace, SFMono-Regular, Consolas, monospace;
                }
                .pykim-run-button, .pykim-clear-button {
                    border: 0; border-radius: .4rem; padding: .55rem .9rem;
                    color: white; cursor: pointer; margin-right: .4rem;
                }
                .pykim-run-button { background: #f36b2b; }
                .pykim-clear-button { background: #686a6d; }
                .pykim-test-result {
                    border: 1px solid #d7d8d9;
                    border-left-width: 5px;
                    border-radius: .45rem;
                    box-shadow: none;
                }
                .pykim-test-passed {
                    border-left-color: #2e7d32;
                    background: #f2f8f3;
                }
                .pykim-test-failed {
                    border-left-color: #d14b34;
                    background: #fff5f2;
                }
                .pykim-test-hint {
                    background: #fff4eb;
                    border-left: 3px solid #f36b2b;
                    border-radius: .3rem;
                    padding: .55rem .75rem;
                }
            </style>
            <script type="module">
                import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v314.0.2/full/pyodide.mjs";
                let runtime = null;
                const ready = loadPyodide().then(value => {
                    runtime = value;
                    const status = document.getElementById('pyodide-status');
                    if (status) status.innerHTML = '<strong>Python ist bereit.</strong>';
                    return value;
                }).catch(error => {
                    const status = document.getElementById('pyodide-status');
                    if (status) status.textContent = `Pyodide konnte nicht geladen werden: ${error}`;
                    throw error;
                });
                window.runPyKIMPython = async () => {
                    const output = document.getElementById('pyodide-output');
                    const code = document.getElementById('pyodide-code').value;
                    output.textContent = 'Wird ausgeführt …';
                    try {
                        const pyodide = await ready;
                        let text = '';
                        pyodide.setStdout({batched: value => text += `${value}\n`});
                        pyodide.setStderr({batched: value => text += `${value}\n`});
                        const result = await pyodide.runPythonAsync(code);
                        if (result !== undefined) text += String(result);
                        output.textContent = text || 'Programm ohne Ausgabe beendet.';
                    } catch (error) {
                        output.textContent = String(error);
                    }
                };
            </script>
            <script>
                (() => {
                    const addCopyButtons = root => {
                        root.querySelectorAll('pre:not(.pykim-copy-ready)').forEach(pre => {
                            pre.classList.add('pykim-copy-ready');
                            const button = document.createElement('button');
                            button.className = 'pykim-copy-button';
                            button.type = 'button';
                            button.textContent = 'Kopieren';
                            button.addEventListener('click', async () => {
                                const code = pre.querySelector('code');
                                const text = (code || pre).innerText;
                                if (navigator.clipboard?.writeText) {
                                    await navigator.clipboard.writeText(text);
                                } else {
                                    const area = document.createElement('textarea');
                                    area.value = text;
                                    area.style.position = 'fixed';
                                    area.style.opacity = '0';
                                    document.body.appendChild(area);
                                    area.select();
                                    document.execCommand('copy');
                                    area.remove();
                                }
                                button.textContent = 'Kopiert ✓';
                                setTimeout(() => button.textContent = 'Kopieren', 1500);
                            });
                            pre.appendChild(button);
                        });
                    };
                    document.addEventListener('DOMContentLoaded', () => {
                        addCopyButtons(document);
                        new MutationObserver(() => addCopyButtons(document)).observe(
                            document.body, {childList: true, subtree: true}
                        );
                    });
                })();
            </script>
        """)
        with ui.header().classes("items-center"):
            ui.label("PyKIM-Begleitheft").classes("text-xl font-bold")
            ui.space()
            configured = get_course_directory()
            current_student = get_student_name(configured) or system_user_name()
            ui.label(f"Hallo, {current_student}").classes("text-sm")
            ui.label("Kein Kursordner" if configured is None else str(configured)).classes("text-sm")

        with ui.tabs().classes("w-full") as tabs:
            setup_tab = ui.tab("Setup", icon="settings")
            tools_tab = ui.tab("Werkzeuge", icon="construction")
            overview_tab = ui.tab("Übersicht", icon="dashboard")
            tasks_tab = ui.tab("Aufgaben", icon="checklist")
            examples_tab = ui.tab("Beispiele", icon="lightbulb")
            submission_tab = ui.tab("Abgabe", icon="upload_file")
            sheet_tab = ui.tab("Cheatsheet", icon="bolt")
            script_tab = ui.tab("Skript", icon="menu_book")
            pyxel_tab = ui.tab("Pyxel", icon="sports_esports")
            browser_tab = ui.tab("Python im Browser", icon="code")

        with ui.tab_panels(tabs, value=overview_tab).classes("w-full max-w-6xl mx-auto"):
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
                ui.label("IDE, Updates und Pyxel-Werkzeuge").classes("text-2xl font-bold")
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
                    ui.markdown("Der offizielle Editor bearbeitet **Sprites, Tilemaps, Sounds und Musik** in einer gemeinsamen `.pyxres`-Datei.")
                    resource = ui.input(
                        "Ressourcendatei",
                        value=str(course / "eigene_projekte" / "mein_spiel.pyxres"),
                    ).classes("w-full")

                    def start_editor() -> None:
                        start_local(
                            lambda: launch_pyxel_editor(resource.value),
                            "Pyxel-Editor wurde gestartet.",
                        )

                    ui.button("Sprite- und Musikeditor öffnen", on_click=start_editor, icon="palette")

                    ui.separator()
                    ui.label("Offizielle Pyxel-Beispiele").classes("text-xl font-bold")
                    ui.markdown(
                        "Die Beispiele gehören zur installierten Pyxel-Version und öffnen "
                        "sich als ausführbare Programme in einem eigenen Fenster."
                    )
                    examples = pyxel_examples()
                    if not examples:
                        ui.label("Es wurden keine Pyxel-Beispiele gefunden.").classes("text-orange")
                    else:
                        example_options = {
                            str(example): example.stem.replace("_", " ")
                            for example in examples
                        }
                        selected_example = ui.select(
                            example_options,
                            value=str(examples[0]),
                            label="Beispiel auswählen",
                        ).classes("w-full")

                        with ui.row():
                            ui.button(
                                "Beispiel starten",
                                on_click=lambda: start_local(
                                    lambda: launch_pyxel_example(selected_example.value),
                                    "Pyxel-Beispiel wurde gestartet.",
                                ),
                                icon="play_arrow",
                            )
                            ui.button(
                                "Quellcode öffnen",
                                on_click=lambda: start_local(
                                    lambda: open_path(selected_example.value),
                                    "Beispielcode wurde geöffnet.",
                                ),
                                icon="code",
                            ).props("outline")

                ui.separator()
                ui.label("Updates aus GitHub").classes("text-xl font-bold")
                update_label = ui.label("Noch nicht geprüft.")

                def check_update() -> None:
                    try:
                        info = github_version()
                        update_label.text = (
                            f"Installiert: {info['installed']} · GitHub: {info['github']}"
                        )
                    except OSError as error:
                        update_label.text = f"Updateprüfung fehlgeschlagen: {error}"

                def perform_update() -> None:
                    try:
                        update_from_github()
                        ui.notify("Update installiert. Bitte Suite neu starten.", type="positive")
                    except Exception as error:
                        ui.notify(f"Update fehlgeschlagen: {error}", type="negative")

                with ui.row():
                    ui.button("GitHub-Version prüfen", on_click=check_update, icon="refresh")
                    with ui.dialog() as confirmation, ui.card():
                        ui.label("PyKIM wirklich aus dem GitHub-main-Branch aktualisieren?")
                        ui.label("Schülerdateien im Kursordner werden dabei nicht verändert.")
                        with ui.row():
                            ui.button("Abbrechen", on_click=confirmation.close).props("flat")
                            ui.button("Update installieren", on_click=lambda: (confirmation.close(), perform_update()))
                    ui.button("Entwicklungsversion installieren", on_click=confirmation.open, icon="system_update")

            with ui.tab_panel(overview_tab):
                progress = load_progress()
                latest = _latest_attempts(progress)
                completed = sum(bool(item.get("successful")) for item in latest.values())
                ui.label("Mein Lernstand").classes("text-2xl font-bold")
                ui.linear_progress(value=completed / max(1, len(exercise_names())))
                ui.label(f"{completed} von {len(exercise_names())} Aufgaben vollständig gelöst")
                with ui.grid(columns=2).classes("w-full gap-4"):
                    for name in exercise_names():
                        exercise = get_exercise(name)
                        attempt = latest.get(name)
                        with ui.card().classes("w-full"):
                            ui.label(exercise.title).classes("font-bold")
                            if attempt is None:
                                ui.label("Noch nicht begonnen").classes("text-grey")
                            else:
                                ui.label(f"Tests: {attempt['passed']}/{attempt['total']}")
                                optimization = attempt.get("optimization")
                                if isinstance(optimization, dict):
                                    ui.label(f"Optimierung: {optimization['score']} %")

            with ui.tab_panel(tasks_tab):
                progress = load_progress()
                journal = progress.get("journal", {})
                ui.label("Aufgaben und Testfälle").classes("text-2xl font-bold")
                for name in exercise_names():
                    exercise = get_exercise(name)
                    with ui.expansion(exercise.title, icon="task_alt").classes("w-full"):
                        assignment = get_assignment(name)
                        with ui.card().classes("w-full bg-orange-1 shadow-none"):
                            with ui.row().classes("w-full items-center"):
                                ui.label("Aufgabenstellung").classes("text-lg font-bold")
                                ui.space()
                                ui.badge(assignment.difficulty.upper(), color="primary")
                            ui.label(assignment.summary).classes("text-base")
                            with ui.column().classes("gap-1"):
                                for requirement in assignment.requirements:
                                    ui.label(f"• {requirement}")
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
                                    _render_test_results(ui, exercise_name)

                            render_test_results()

                            def save_task(path=target, editor=source_editor) -> bool:
                                selected_course = get_course_directory()
                                if selected_course is None:
                                    ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                                    return False
                                try:
                                    save_student_source(path, editor.value, selected_course)
                                    ui.notify("Quellcode wurde gespeichert.", type="positive")
                                    return True
                                except (OSError, ValueError) as error:
                                    ui.notify(f"Speichern fehlgeschlagen: {error}", type="negative")
                                    return False

                            async def save_and_start_task(
                                path=target,
                                editor=source_editor,
                                output_view=execution_output,
                                refresh_tests=render_test_results,
                            ) -> None:
                                selected_course = get_course_directory()
                                if selected_course is None:
                                    ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                                    return
                                try:
                                    save_student_source(path, editor.value, selected_course)
                                    output_view.set_content("Programm läuft …")
                                    result = await nicegui_run.io_bound(
                                        execute_student_program, path, selected_course
                                    )
                                    output = result.stdout
                                    if result.stderr:
                                        output += ("\n" if output else "") + result.stderr
                                    output_view.set_content(
                                        output.strip()
                                        or f"Programm beendet (Code {result.returncode}), ohne Ausgabe."
                                    )
                                    refresh_tests()
                                    ui.notify(
                                        "Tests aktualisiert."
                                        if result.returncode == 0
                                        else f"Programm mit Fehlercode {result.returncode} beendet.",
                                        type="positive" if result.returncode == 0 else "negative",
                                    )
                                except (OSError, ValueError) as error:
                                    ui.notify(str(error), type="negative")

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
                                ui.button(
                                    "Ausführen",
                                    on_click=save_and_start_task,
                                    icon="play_arrow",
                                )
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
                ui.label("PyKIM-Beispiele").classes("text-2xl font-bold")
                ui.markdown(
                    "Die Originale gehören zum Paket und bleiben unverändert. "
                    "Zum Bearbeiten wird automatisch eine persönliche Kopie unter "
                    "`eigene_projekte/beispiele` verwendet."
                )
                for example in example_programs():
                    with ui.expansion(example.title, icon="code").classes("w-full"):
                        with ui.row().classes("w-full items-center"):
                            ui.label(example.description).classes("text-base")
                            ui.space()
                            ui.badge(example.category, color="secondary")
                        example_editor = ui.codemirror(
                            value=example.source,
                            language="Python",
                            line_wrapping=False,
                        ).classes("w-full").style("height: 24rem")
                        example_editor.disable()

                        def copy_example_source(editor=example_editor) -> None:
                            ui.clipboard.write(editor.value)
                            ui.notify("Beispielcode wurde kopiert.", type="positive")

                        def start_example(example_name=example.name) -> None:
                            try:
                                launch_example(example_name)
                                ui.notify("Beispiel wurde gestartet.", type="positive")
                            except (OSError, ValueError) as error:
                                ui.notify(f"Start fehlgeschlagen: {error}", type="negative")

                        def save_example_copy(example_name=example.name) -> None:
                            course = get_course_directory()
                            if course is None:
                                ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                                return
                            try:
                                target, created = copy_example_to_course(example_name, course)
                                ui.notify(
                                    f"Kopie angelegt: {target.relative_to(course)}"
                                    if created
                                    else "Die persönliche Kopie ist bereits vorhanden.",
                                    type="positive",
                                )
                            except (OSError, ValueError) as error:
                                ui.notify(str(error), type="negative")

                        def open_example_in_ide(example_name=example.name) -> None:
                            course = get_course_directory()
                            if course is None:
                                ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                                return
                            try:
                                target, _created = copy_example_to_course(example_name, course)
                                open_in_preferred_ide(target)
                                ui.notify("Beispiel wurde in der IDE geöffnet.", type="positive")
                            except (OSError, RuntimeError, ValueError) as error:
                                ui.notify(str(error), type="negative")

                        with ui.row():
                            ui.button("Ausführen", on_click=start_example, icon="play_arrow")
                            ui.button(
                                "Kopieren", on_click=copy_example_source, icon="content_copy"
                            ).props("outline")
                            example_ide_button = ui.button(
                                f"In {_preferred_ide_label()} öffnen",
                                on_click=open_example_in_ide,
                                icon="open_in_new",
                            ).props("outline")
                            ide_open_buttons.append(example_ide_button)
                            ui.button(
                                "Als eigenes Projekt speichern",
                                on_click=save_example_copy,
                                icon="content_copy",
                            ).props("outline")

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
                ui.markdown(SCRIPT).classes("prose max-w-none")
            with ui.tab_panel(pyxel_tab):
                ui.markdown(PYXEL_REFERENCE).classes("prose max-w-none")
            with ui.tab_panel(browser_tab):
                ui.label("Python direkt im Browser").classes("text-2xl font-bold")
                ui.markdown(
                    "Diese erste Pyodide-Spielwiese führt normales Python vollständig "
                    "im Browser aus. Ein browserfähiges PyKIM-Canvas folgt als nächste Stufe."
                )
                ui.html(PYODIDE_PLAYGROUND, sanitize=False).classes("w-full")

    ui.run(
        title="PyKIM-Begleitheft",
        favicon="🤖",
        host="127.0.0.1",
        reload=False,
        show=show and not desktop,
        native=desktop,
        window_size=(1280, 850) if desktop else None,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
