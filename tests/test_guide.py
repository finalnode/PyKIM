import json
import ast
import hashlib
import io
import threading
import time
import zipfile
from urllib.error import HTTPError
from pathlib import Path

import pykim
import pytest
from pykim.guide.app import parse_arguments
from pykim.guide.content import PYODIDE_PLAYGROUND
from pykim.guide.course import (
    create_course,
    provision_course_exercises,
    exercise_file,
    get_course_directory,
    get_ide_preference,
    get_student_name,
    reset_exercise_file,
    set_ide_preference,
    get_runtime_preference,
    set_runtime_preference,
)
from pykim.guide.ide import (
    configure_thonny,
    configure_vscode,
    discover_ides,
    launch_ide,
    thonny_profile_directory,
)
from pykim.guide.runtime import (
    RuntimeCandidate,
    discover_runtimes,
    inspect_runtime,
    managed_runtime_path,
    selected_runtime,
    _installed_python_paths,
    provision_managed_runtime,
    bundled_wheelhouse,
    repair_runtime,
    runtime_diagnostics,
)
from pykim.guide.progress import (
    load_progress,
    clear_exercise_progress,
    record_attempt,
    remove_packaged_example_attempts,
    save_journal_entry,
)
from pykim.guide.execution import ExecutionManager, ScriptExampleManager
from pykim.guide.script_quality import (
    annotated_script_blocks,
    classify_script_block,
    run_headless,
)
from pykim.guide.author_workspace import (
    AuthorDraft,
    assignment_markdown,
    load_published_draft,
    save_author_draft,
    validate_author_draft,
)
from pykim.guide.examples import copy_example_to_course, example_programs, launch_example
from pykim.guide.pyxel_examples_view import copy_pyxel_example_to_course
from pykim.guide.projects import (
    create_project,
    launch_project,
    load_project,
    project_text,
    project_text_hash,
    project_slug,
    save_project_text,
    student_projects,
)
from pykim.guide.library import (
    PACKAGED_CONTENT_ROOT,
    script_chapters,
    script_code_examples,
    render_script_markdown,
    render_task_markdown,
    task_assignment,
    task_document,
    task_names,
)
from pykim.guide.updates import (
    active_content_root,
    check_app_update,
    check_content_update,
    install_content_update,
    check_updates,
    format_content_version,
    sync_certificate_content,
    verify_certificate_trainers,
    verify_certificate_authorization,
)
from pykim.guide.system import (
    execute_student_program,
    execute_script_example,
    github_version,
    install_or_repair_pyxel,
    launch_pyxel_editor,
    launch_pyxel_example,
    open_path,
    pyxel_examples,
    read_student_source,
    run_student_program,
    save_student_source,
    source_hash,
    SourceConflictError,
    system_status,
    system_user_name,
)
from pykim.trainer.assignments import ASSIGNMENTS, get_assignment
from pykim.trainer.models import CheckReport, CheckResult, OptimizationResult
from pykim.trainer.authoring import generate_exercise_source


def test_guide_starts_as_desktop_by_default_and_supports_browser_fallback():
    assert not parse_arguments([]).browser
    assert parse_arguments(["--browser"]).browser


def test_browser_playground_starts_with_plain_python_and_has_reset_action():
    assert "for zahl in range(1, 6)" in PYODIDE_PLAYGROUND
    assert "from pykim" not in PYODIDE_PLAYGROUND
    assert "resetPyKIMBrowserExample" in PYODIDE_PLAYGROUND
    assert "stopPyKIMBrowserPython" in PYODIDE_PLAYGROUND
    assert "erst beim Ausführen geladen" in PYODIDE_PLAYGROUND
    assert "pyodide-highlight" in PYODIDE_PLAYGROUND
    assert "handlePyKIMBrowserEditorKey" in PYODIDE_PLAYGROUND


def test_every_exercise_has_a_complete_assignment():
    from pykim.trainer.exercises import exercise_names

    assert set(ASSIGNMENTS) == set(exercise_names())
    assert get_assignment("quadrat-5").requirements
    assert task_assignment("quadrat-5").difficulty == "einfach"
    assert task_assignment("musik-pixel-klasse").difficulty == "fortgeschritten"
    assert "@difficulty:" not in render_task_markdown(
        task_document("quadrat-5").content
    )


def test_markdown_library_covers_all_trainers_and_both_learning_paths():
    from pykim.trainer.exercises import exercise_names

    assert set(task_names()) == set(exercise_names())
    assert script_chapters("imperativ")
    assert script_chapters("oop")


def test_content_overlay_can_replace_scripts_without_touching_packaged_files(
    tmp_path, monkeypatch
):
    overlay = tmp_path / "overlay"
    chapter = overlay / "Skripte" / "imperativ" / "00_neu.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text("# Aktualisiertes Kapitel\n", encoding="utf-8")
    monkeypatch.setenv("PYKIM_CONTENT_DIR", str(overlay))

    assert active_content_root(PACKAGED_CONTENT_ROOT) == overlay
    assert [item.title for item in script_chapters("imperativ")] == [
        "Aktualisiertes Kapitel"
    ]


def test_bundled_content_manifest_matches_all_markdown_files():
    manifest = json.loads(
        (PACKAGED_CONTENT_ROOT / "content-manifest.json").read_text(encoding="utf-8")
    )
    expected = manifest["files"]
    actual = {
        path.relative_to(PACKAGED_CONTENT_ROOT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for folder, pattern in (("Skripte", "*.md"), ("Aufgaben", "*.md"), ("Trainer", "*.yml"))
        for path in (PACKAGED_CONTENT_ROOT / folder).rglob(pattern)
    }

    assert expected == actual


def test_content_update_is_hash_checked_and_activated_atomically(tmp_path, monkeypatch):
    source = io.BytesIO()
    content = b"# Neues Kapitel\n"
    with zipfile.ZipFile(source, "w") as bundle:
        bundle.writestr("Skripte/imperativ/01_neu.md", content)
    archive = source.getvalue()
    manifest = {
        "content_version": "2099.1",
        "package_url": "https://example.invalid/content.zip",
        "package_sha256": hashlib.sha256(archive).hexdigest(),
        "files": {
            "Skripte/imperativ/01_neu.md": hashlib.sha256(content).hexdigest()
        },
    }

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return archive

    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("pykim.guide.updates.urlopen", lambda request, timeout: Response())

    installed = install_content_update(manifest)

    assert (installed / "Skripte/imperativ/01_neu.md").read_bytes() == content
    assert active_content_root(PACKAGED_CONTENT_ROOT) == installed


def test_content_update_rejects_changed_archive(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return b"manipuliert"

    monkeypatch.setattr("pykim.guide.updates.urlopen", lambda request, timeout: Response())
    with pytest.raises(ValueError, match="Prüfsumme"):
        install_content_update(
            {
                "content_version": "2099.2",
                "package_url": "https://example.invalid/content.zip",
                "package_sha256": "0" * 64,
                "files": {"Skripte/imperativ/x.md": "0" * 64},
            }
        )


def test_damaged_active_content_falls_back_to_packaged_files(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    version = "2099.3"
    root = tmp_path / "config" / "content" / "versions" / version
    chapter = root / "Skripte" / "imperativ" / "x.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text("beschädigt", encoding="utf-8")
    (root / "content-manifest.json").write_text(
        json.dumps({"content_version": version, "files": {
            "Skripte/imperativ/x.md": "0" * 64
        }}),
        encoding="utf-8",
    )
    marker = tmp_path / "config" / "content" / "active.json"
    marker.write_text(json.dumps({"content_version": version}), encoding="utf-8")

    assert active_content_root(PACKAGED_CONTENT_ROOT) == PACKAGED_CONTENT_ROOT
    assert task_document("quadrat-5").paradigm == "imperativ"
    assert task_document("musik-pixel-klasse").paradigm == "oop"
    assert len(script_code_examples()) >= 50


def test_script_example_execution_captures_output_and_disables_progress():
    result = execute_script_example("print('Hallo aus dem Skript')")

    assert result.returncode == 0
    assert result.stdout.strip() == "Hallo aus dem Skript"
    assert result.stderr == ""


def test_script_example_uses_unbuffered_python(monkeypatch):
    calls = []

    class Completed:
        returncode = 0
        stdout = "28\n19\n"
        stderr = ""

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return Completed()

    monkeypatch.setattr("pykim.guide.system.subprocess.run", run)

    result = execute_script_example("print(28)\nprint(19)")

    assert calls[0][0][1] == "-u"
    assert calls[0][1]["env"]["PYTHONUNBUFFERED"] == "1"
    assert result.stdout == "28\n19\n"


def test_all_executable_script_blocks_are_valid_python():
    for source in script_code_examples():
        ast.parse(source)


def test_loop_comparison_examples_are_visibly_animated_and_painted():
    examples = [
        source
        for source in script_code_examples()
        if "right(4)" in source and "down(4)" in source
    ]

    assert len(examples) == 2
    for source in examples:
        assert "set_position(60, 40)" in source
        assert "speed(15)" in source
        assert 'paint("purple")' in source
        assert source.rstrip().endswith("run()")


def test_every_run_annotated_block_is_a_complete_program():
    audits = annotated_script_blocks()

    assert audits
    assert all(audit.runnable for audit in audits)
    assert {audit.kind for audit in audits} == {"console", "pykim", "pyxel"}


def test_every_console_and_pykim_script_example_runs_headless():
    failures = []
    for audit in annotated_script_blocks():
        if audit.kind == "pyxel":
            continue
        result = run_headless(audit)
        if result.returncode != 0:
            failures.append((audit.path.name, audit.line, result.stderr))

    assert failures == []


def test_author_workspace_loads_a_published_pair():
    draft = load_published_draft("quadrat-5")

    assert draft.name == "quadrat-5"
    assert "id: quadrat-5" in draft.trainer_source
    assert draft.assignment_markdown.startswith("# Quadrat")
    assert validate_author_draft(draft) == ()


def test_author_workspace_saves_both_files_with_overwrite_protection(tmp_path):
    trainer = generate_exercise_source(
        "entwurf-test", "Entwurf Test", ("pixels", "loop"), optimal_lines=8
    )
    markdown = assignment_markdown(
        "Entwurf Test", "Zeichne ein Muster.", "Male einen Punkt.\nNutze eine Schleife.", "mittel"
    )
    draft = AuthorDraft("entwurf-test", trainer, markdown)

    trainer_path, markdown_path = save_author_draft(
        tmp_path, draft, paradigm="imperativ"
    )

    assert trainer_path.read_text(encoding="utf-8") == trainer
    assert markdown_path.read_text(encoding="utf-8") == markdown
    assert len(draft.content_hash) == 64
    with pytest.raises(FileExistsError):
        save_author_draft(tmp_path, draft, paradigm="imperativ")
    save_author_draft(tmp_path, draft, paradigm="imperativ", overwrite=True)


def test_author_workspace_rejects_mismatched_builder_name():
    draft = AuthorDraft(
        "richtiger-name",
        generate_exercise_source("anderer-name", "Titel", ("loop",)),
        assignment_markdown("Titel", "Zusammenfassung", "Anforderung", "einfach"),
    )

    assert any("Kennung" in issue for issue in validate_author_draft(draft))


def test_script_button_annotations_apply_only_to_the_next_code_block():
    content = (
        "@button:run\n@button:copy\n```python\nprint('eins')\n```\n\n"
        "```python\nprint('zwei')\n```"
    )

    rendered = render_script_markdown(content)

    assert 'data-buttons="run,copy"' in rendered
    assert "@button:" not in rendered
    assert rendered.count("pykim-code-options") == 1


def test_course_setup_copies_legacy_solution_into_new_structure(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    legacy = course / "01_grundlagen" / "quadrat_5.py"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("# meine alte Lösung\nright(5)\n", encoding="utf-8")

    create_course(course)
    provision_course_exercises(course)

    migrated = course / "Aufgaben" / "imperativ" / "quadrat_5.py"
    assert migrated.read_text(encoding="utf-8") == legacy.read_text(encoding="utf-8")
    assert legacy.exists()


def test_packaged_examples_are_complete_and_copy_without_overwriting(tmp_path):
    examples = example_programs()
    assert len(examples) == 20
    assert all(example.source and example.path.exists() for example in examples)

    target, created = copy_example_to_course("paint_line", tmp_path)
    assert created
    target.write_text("# meine Änderung", encoding="utf-8")
    same_target, created = copy_example_to_course("paint_line", tmp_path)
    assert not created
    assert same_target == target
    assert target.read_text(encoding="utf-8") == "# meine Änderung"
    assert target.relative_to(tmp_path).parts[:2] == ("Projekte", "beispiele")
    assert (target.parent / "projekt.json").exists()


def test_create_and_load_pyxel_project_with_relative_resources(tmp_path):
    project = create_project(tmp_path, "Mein Rätsel!", "pyxel")

    assert project.slug == "mein_ratsel"
    assert project.entrypoint == tmp_path / "Projekte" / "mein_ratsel" / "main.py"
    assert project.resources == project.directory / "ressourcen.pyxres"
    assert project.documentation == project.directory / "README.md"
    assert "# Mein Projekt" in project.documentation.read_text(encoding="utf-8")
    assert 'pyxel.load("ressourcen.pyxres")' in project.entrypoint.read_text(encoding="utf-8")
    assert load_project(project.directory) == project
    assert student_projects(tmp_path) == (project,)
    with pytest.raises(FileExistsError, match="existiert bereits"):
        create_project(tmp_path, "Mein Rätsel!", "pyxel")


def test_project_code_and_documentation_detect_external_changes(tmp_path):
    project = create_project(tmp_path, "Dokumentiertes Spiel", "pykim")
    documentation = project_text(project, project.documentation)

    save_project_text(
        project,
        project.documentation,
        "# Meine Erklärung\n",
        expected_hash=project_text_hash(documentation),
    )
    assert project.documentation.read_text(encoding="utf-8") == "# Meine Erklärung\n"

    project.documentation.write_text("# Extern geändert\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="außerhalb"):
        save_project_text(
            project,
            project.documentation,
            "# Überschreiben\n",
            expected_hash=project_text_hash("# Meine Erklärung\n"),
        )


def test_project_metadata_cannot_escape_its_directory(tmp_path):
    directory = tmp_path / "Projekte" / "boese"
    directory.mkdir(parents=True)
    (directory / "projekt.json").write_text(
        json.dumps({
            "format": 1,
            "name": "Böse",
            "kind": "pyxel",
            "entrypoint": "../fremd.py",
            "resources": "ressourcen.pyxres",
        }),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Programmeinstieg"):
        load_project(directory)


def test_project_launch_uses_selected_runtime_and_project_working_directory(
    tmp_path, monkeypatch
):
    project = create_project(tmp_path, "Spiel", "pykim")
    python = tmp_path / "runtime" / "python"
    calls = []
    monkeypatch.setattr(
        "pykim.guide.runtime.selected_runtime",
        lambda course=None: RuntimeCandidate(str(python), "3.13", "Test", True, True, True),
    )
    monkeypatch.setattr(
        "pykim.guide.projects.subprocess.Popen",
        lambda command, cwd=None, env=None: calls.append((command, cwd, env)),
    )

    assert launch_project(project, tmp_path) == project.entrypoint
    assert calls[0][:2] == ([str(python), str(project.entrypoint)], project.directory)
    assert str(tmp_path.resolve()) in calls[0][2]["PYTHONPATH"].split(__import__("os").pathsep)


def test_project_slug_rejects_empty_names():
    with pytest.raises(ValueError, match="Buchstaben"):
        project_slug("!!!")


def test_all_packaged_examples_run_headless():
    failures = []
    for example in example_programs():
        audit = classify_script_block(example.source, example.path, 1)
        if not audit.runnable:
            failures.append((example.name, audit.reason))
            continue
        result = run_headless(audit)
        if result.returncode:
            failures.append((example.name, result.stderr))

    assert failures == []


def test_running_example_explicitly_disables_progress(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "pykim.guide.examples.subprocess.Popen",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )

    launch_example("interaktive_steuerung_aufgabe")

    assert calls[0][1]["env"]["PYKIM_PROGRESS_MODE"] == "disabled"


def test_cleanup_removes_only_packaged_example_attempts(tmp_path):
    course = tmp_path / "course"
    progress_directory = course / ".pykim"
    progress_directory.mkdir(parents=True)
    example_source = example_programs()[0].source
    progress_path = progress_directory / "progress.json"
    progress_path.write_text(
        json.dumps(
            {
                "format": 1,
                "attempts": [
                    {"exercise": "example", "source": example_source},
                    {"exercise": "mine", "source": "right(5)"},
                ],
                "journal": {},
            }
        ),
        encoding="utf-8",
    )

    assert remove_packaged_example_attempts(course) == 1
    assert load_progress(course)["attempts"] == [
        {"exercise": "mine", "source": "right(5)"}
    ]
    assert (progress_directory / "progress.before-example-cleanup.json").exists()


def test_course_setup_creates_all_starters_and_preserves_student_work(
    tmp_path, monkeypatch
):
    config = tmp_path / "config"
    course = tmp_path / "webdav" / "PyKIM-Kurs"
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(config))

    first = create_course(course, "Ada")
    provisioned = provision_course_exercises(course)
    square = course / "Aufgaben" / "imperativ" / "quadrat_5.py"
    square.write_text("# meine Lösung", encoding="utf-8")
    second = provision_course_exercises(course)

    assert first["created"] == [".pykim-course.json"]
    assert len(provisioned["created"]) == 11
    assert square.read_text(encoding="utf-8") == "# meine Lösung"
    assert "Aufgaben/imperativ/quadrat_5.py" in second["existing"]
    assert get_course_directory() == course.resolve()
    metadata = json.loads((course / ".pykim-course.json").read_text())
    assert metadata["student_name"] == "Ada"
    assert get_student_name(course) == "Ada"

    create_course(course, "Ada Lovelace")
    assert get_student_name(course) == "Ada Lovelace"


def test_system_user_name_falls_back_to_login(monkeypatch):
    monkeypatch.setattr("pykim.guide.system.getpass.getuser", lambda: "ada")
    monkeypatch.setattr("pykim.guide.system.platform.system", lambda: "Windows")

    assert system_user_name() == "ada"


@pytest.mark.parametrize(
    ("platform_name", "launcher"),
    (("Windows", "explorer"), ("Linux", "xdg-open")),
)
def test_system_file_opening_uses_platform_launcher(
    tmp_path, monkeypatch, platform_name, launcher
):
    target = tmp_path / "aufgabe.py"
    target.write_text("print('ok')", encoding="utf-8")
    calls = []
    monkeypatch.setattr("pykim.guide.system.platform.system", lambda: platform_name)
    monkeypatch.setattr(
        "pykim.guide.system.subprocess.Popen",
        lambda command, cwd=None: calls.append(command),
    )

    open_path(target)

    assert calls == [[launcher, str(target.resolve())]]


def test_ide_preference_is_saved_without_losing_course_directory(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    custom_ide = tmp_path / "MyEditor.app"
    custom_ide.mkdir()

    create_course(course)
    assert set_ide_preference("custom", str(custom_ide)) == {
        "ide": "custom",
        "path": str(custom_ide.resolve()),
    }
    assert get_ide_preference()["ide"] == "custom"
    assert get_course_directory() == course.resolve()

    with pytest.raises(ValueError, match="nicht gefunden"):
        set_ide_preference("custom", str(tmp_path / "missing"))


def test_runtime_preference_is_saved_without_losing_other_setup(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    create_course(tmp_path / "course")
    set_ide_preference("system")

    assert set_runtime_preference(python) == str(python.resolve())
    assert get_runtime_preference() == str(python.resolve())
    assert get_ide_preference()["ide"] == "system"
    assert get_course_directory() == (tmp_path / "course").resolve()


def test_runtime_discovery_includes_current_suite_python(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    candidates = discover_runtimes()

    current_path = str(Path(__import__("sys").executable).resolve())
    current = next(item for item in candidates if item.executable == current_path)
    assert current.supported and current.pykim and current.pyxel
    assert selected_runtime().executable == current.executable


def test_managed_runtime_is_local_and_stable(tmp_path, monkeypatch):
    local = tmp_path / "local-runtimes"
    monkeypatch.setenv("PYKIM_RUNTIME_DIR", str(local))
    course = tmp_path / "synced" / "course"

    first = managed_runtime_path(course)
    second = managed_runtime_path(course)

    assert first == second
    assert first.parent == local
    assert not first.is_relative_to(course)


def test_runtime_discovery_scans_conda_pyenv_and_uv(tmp_path, monkeypatch):
    home = tmp_path / "home"
    expected = {
        home / "miniconda3" / "envs" / "kurs" / "bin" / "python",
        home / ".pyenv" / "versions" / "3.12.4" / "bin" / "python",
        home / ".local" / "share" / "uv" / "python" / "cpython-3.13" / "bin" / "python3",
    }
    for executable in expected:
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_text("", encoding="utf-8")
    monkeypatch.setattr("pykim.guide.runtime.Path.home", lambda: home)
    monkeypatch.setattr("pykim.guide.runtime.platform.system", lambda: "Linux")
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)

    found = {path for path, _ in _installed_python_paths()}

    assert expected <= found


def test_provisioned_runtime_installs_package_and_becomes_preferred(tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    python = tmp_path / "runtime" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    source = tmp_path / "PyKIM.whl"
    source.write_text("", encoding="utf-8")
    calls = []
    ready = RuntimeCandidate(str(python), "3.13.1", "PyKIM-Kursumgebung", True, True, True)
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("pykim.guide.runtime.create_managed_runtime", lambda *args: ready)
    monkeypatch.setattr("pykim.guide.runtime._package_source", lambda: source)
    monkeypatch.setattr("pykim.guide.runtime.bundled_wheelhouse", lambda: None)
    monkeypatch.setattr("pykim.guide.runtime.inspect_runtime", lambda *args: ready)
    monkeypatch.setattr(
        "pykim.guide.runtime.subprocess.run",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )

    result = provision_managed_runtime(course, python)

    assert result == ready
    assert calls[0][0] == [str(python), "-m", "pip", "install", "--upgrade", str(source)]
    assert get_runtime_preference() == str(python.resolve())


def test_runtime_install_uses_bundled_wheels_offline(tmp_path, monkeypatch):
    wheelhouse = tmp_path / "wheels"
    wheelhouse.mkdir()
    (wheelhouse / "PyKIM-1.0-py3-none-any.whl").write_text("", encoding="utf-8")
    source = tmp_path / "PyKIM.whl"
    source.write_text("", encoding="utf-8")
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    calls = []
    monkeypatch.setenv("PYKIM_WHEELHOUSE", str(wheelhouse))
    monkeypatch.setattr("pykim.guide.runtime._package_source", lambda: source)
    monkeypatch.setattr(
        "pykim.guide.runtime.subprocess.run",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )

    from pykim.guide.runtime import _install_runtime_packages
    _install_runtime_packages(python)

    assert bundled_wheelhouse() == wheelhouse
    assert "--no-index" in calls[0][0]
    assert calls[0][0][calls[0][0].index("--find-links") + 1] == str(wheelhouse)


def test_runtime_diagnostics_does_not_contain_student_files(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    report = runtime_diagnostics(tmp_path / "course")

    assert set(report) == {"platform", "selected", "wheelhouse", "candidates"}
    assert all("executable" in item for item in report["candidates"])


def test_repair_refuses_to_modify_external_python(tmp_path, monkeypatch):
    python = tmp_path / "external" / "python"
    python.parent.mkdir()
    python.write_text("", encoding="utf-8")
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    set_runtime_preference(python)

    with pytest.raises(RuntimeError, match="verwaltete Kursumgebung"):
        repair_runtime(tmp_path / "course")


def test_vscode_workspace_uses_selected_runtime_and_preserves_settings(tmp_path):
    settings_directory = tmp_path / ".vscode"
    settings_directory.mkdir()
    settings = settings_directory / "settings.json"
    settings.write_text('{"editor.formatOnSave": true}', encoding="utf-8")
    python = tmp_path / "runtime" / "bin" / "python"

    settings_path, extensions_path = configure_vscode(tmp_path, python)
    data = json.loads(settings_path.read_text(encoding="utf-8"))

    assert data["editor.formatOnSave"] is True
    assert data["python.defaultInterpreterPath"] == str(python.resolve())
    assert data["python.terminal.activateEnvironment"] is True
    assert "ms-python.python" in extensions_path.read_text(encoding="utf-8")


def test_launch_vscode_configures_workspace_before_opening(tmp_path, monkeypatch):
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    calls = []
    monkeypatch.setattr(
        "pykim.guide.ide.discover_ides",
        lambda: {"vscode": __import__("pykim.guide.ide", fromlist=["IDEInstallation"]).IDEInstallation(
            "vscode", "Visual Studio Code", "/usr/bin/code"
        )},
    )
    monkeypatch.setattr("pykim.guide.ide.subprocess.Popen", lambda command: calls.append(command))

    launch_ide(tmp_path, "vscode", python=python)

    assert calls == [["/usr/bin/code", str(tmp_path.resolve())]]
    settings = json.loads((tmp_path / ".vscode" / "settings.json").read_text())
    assert settings["python.defaultInterpreterPath"] == str(python.resolve())


def test_thonny_uses_isolated_pykim_profile_and_selected_runtime(tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    python = tmp_path / "runtime" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))

    profile = configure_thonny(course, python)
    configuration = (profile / "configuration.ini").read_text(encoding="utf-8")

    assert profile == thonny_profile_directory(course)
    assert "backend_name = LocalCPython" in configuration
    assert f"executable = {python.resolve()}" in configuration
    assert "single_instance = False" in configuration


def test_launch_thonny_passes_dedicated_user_directory(tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    calls = []
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "pykim.guide.ide.discover_ides",
        lambda: {"thonny": __import__("pykim.guide.ide", fromlist=["IDEInstallation"]).IDEInstallation(
            "thonny", "Thonny", "/usr/bin/thonny"
        )},
    )
    monkeypatch.setattr(
        "pykim.guide.ide.subprocess.Popen",
        lambda command, env=None: calls.append((command, env)),
    )

    launch_ide(course, "thonny", python=python, course=course)

    assert calls[0][0] == ["/usr/bin/thonny", str(course.resolve())]
    assert calls[0][1]["THONNY_USER_DIR"] == str(thonny_profile_directory(course))


def test_progress_and_journal_travel_inside_the_course_folder(tmp_path):
    course = tmp_path / "mounted-drive"
    course.mkdir()
    report = CheckReport(
        "Testaufgabe",
        (
            CheckResult(True, "Position stimmt.", "Position falsch."),
            CheckResult(False, "Schleife stimmt.", "Schleife fehlt.", "Nutze for."),
        ),
        OptimizationResult(50, maximum=100),
    )

    assert record_attempt("test", report, "right()", course=course)
    save_journal_entry("test", "Ich brauche noch eine Schleife.", course=course)
    progress = load_progress(course)

    attempt = progress["attempts"][0]
    assert attempt["source"] == "right()"
    assert attempt["tests"][1]["hint"] == "Nutze for."
    assert attempt["optimization"]["score"] == 50
    assert progress["journal"]["test"]["text"].startswith("Ich brauche")
    assert (course / ".pykim" / "progress.json").exists()


def test_trainer_records_an_attempt_when_course_is_configured(
    tmp_path, monkeypatch, capsys
):
    course = tmp_path / "course"
    course.mkdir()
    monkeypatch.delenv("PYKIM_PROGRESS_MODE")
    monkeypatch.setenv("PYKIM_COURSE_DIR", str(course))
    pykim.set_position(50, 50)
    pykim.paint_start("purple")
    pykim.right(5)
    pykim.down(5)
    pykim.left(5)
    pykim.up(5)

    from pykim.trainer.runner import check_exercise

    check_exercise("quadrat-5", "right(5)")
    capsys.readouterr()
    progress = load_progress(course)

    assert len(progress["attempts"]) == 1
    assert progress["attempts"][0]["exercise"] == "quadrat-5"
    assert progress["attempts"][0]["successful"]


def test_trainer_check_verifies_setup_repository_first(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from pykim.guide.updates import TrainerVerification
    from pykim.trainer import runner

    course = tmp_path / "course"
    course.mkdir()
    setup = SimpleNamespace(repository="https://github.com/example/course.git")
    calls = []
    monkeypatch.setenv("PYKIM_COURSE_DIR", str(course))
    monkeypatch.setattr(
        "pykim.guide.course_setup.course_setup_info",
        lambda _course: setup,
    )
    monkeypatch.setattr(
        "pykim.guide.course_setup.verify_installed_course_setup",
        lambda _course, allow_offline: (
            setup,
            TrainerVerification(True, False),
        ),
    )
    monkeypatch.setattr(
        "pykim.guide.updates.verify_certificate_trainers",
        lambda configuration: calls.append(configuration) or TrainerVerification(True, False),
    )

    runner._refresh_remote_trainers()

    assert calls == [setup]


def test_record_attempt_is_disabled_without_a_configured_course(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "empty-config"))
    monkeypatch.delenv("PYKIM_COURSE_DIR", raising=False)
    report = CheckReport("Leer", ())

    assert not record_attempt("leer", report)


def test_trainer_does_not_record_progress_in_example_mode(tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    monkeypatch.setenv("PYKIM_COURSE_DIR", str(course))
    monkeypatch.setenv("PYKIM_PROGRESS_MODE", "disabled")

    from pykim.trainer.runner import check_exercise

    check_exercise("quadrat-5", "")

    assert load_progress(course)["attempts"] == []


def test_exercise_file_finds_the_generated_starter(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    create_course(course)
    provision_course_exercises(course)

    assert exercise_file("treppe-5") == course / "Aufgaben" / "imperativ" / "treppe_5.py"
    assert exercise_file("gibt-es-nicht") is None


def test_system_status_reports_versions_and_tools(monkeypatch):
    monkeypatch.setattr("pykim.guide.system.shutil.which", lambda name: f"/bin/{name}")

    status = system_status()

    assert status.pykim == pykim.__version__
    assert status.python_supported
    assert status.pyxel and status.thonny and status.vscode


def test_launch_pyxel_editor_uses_official_edit_command(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "pykim.guide.system.shutil.which",
        lambda name: "/usr/local/bin/pyxel" if name == "pyxel" else None,
    )
    monkeypatch.setattr(
        "pykim.guide.system.subprocess.Popen",
        lambda command, cwd=None: calls.append((command, cwd)),
    )
    resource = tmp_path / "assets" / "game.pyxres"

    assert launch_pyxel_editor(resource) == resource
    assert resource.parent.exists()
    assert calls == [
        (["/usr/local/bin/pyxel", "edit", str(resource)], resource.parent)
    ]


def test_pyxel_tools_use_bundled_python_without_global_command(tmp_path, monkeypatch):
    import pyxel

    package = tmp_path / "pyxel"
    examples = package / "examples"
    examples.mkdir(parents=True)
    example = examples / "01_hello.py"
    example.write_text("import pyxel", encoding="utf-8")
    monkeypatch.setattr(pyxel, "__file__", str(package / "__init__.py"))
    monkeypatch.setattr("pykim.guide.system.shutil.which", lambda _name: None)
    monkeypatch.setattr(
        "pykim.guide.system.python_command",
        lambda: ["/Applications/PyKIM.app/Contents/MacOS/PyKIM Python", "--pykim-python"],
    )
    calls = []
    monkeypatch.setattr(
        "pykim.guide.system.subprocess.Popen",
        lambda command, cwd=None: calls.append((command, cwd)),
    )
    resource = tmp_path / "assets" / "game.pyxres"

    assert launch_pyxel_editor(resource) == resource
    assert launch_pyxel_example(example) == example
    runner = "/Applications/PyKIM.app/Contents/MacOS/PyKIM Python"
    assert calls == [
        (
            [runner, "--pykim-python", "-m", "pyxel", "edit", str(resource)],
            resource.parent,
        ),
        (
            [runner, "--pykim-python", "-m", "pyxel", "run", str(example)],
            example.parent,
        ),
    ]


def test_list_and_launch_installed_pyxel_example(tmp_path, monkeypatch):
    import pyxel

    package = tmp_path / "pyxel"
    examples = package / "examples"
    examples.mkdir(parents=True)
    first = examples / "01_hello.py"
    second = examples / "02_game.py"
    first.write_text("import pyxel", encoding="utf-8")
    second.write_text("import pyxel", encoding="utf-8")
    monkeypatch.setattr(pyxel, "__file__", str(package / "__init__.py"))
    monkeypatch.setattr(
        "pykim.guide.system.shutil.which",
        lambda name: "/usr/local/bin/pyxel" if name == "pyxel" else None,
    )
    calls = []
    monkeypatch.setattr(
        "pykim.guide.system.subprocess.Popen",
        lambda command, cwd=None: calls.append((command, cwd)),
    )

    assert pyxel_examples() == (first, second)
    assert launch_pyxel_example(second) == second
    assert calls == [
        (["/usr/local/bin/pyxel", "run", str(second)], second.parent)
    ]
    with pytest.raises(ValueError, match="mitgelieferte"):
        launch_pyxel_example(tmp_path / "fremd.py")


def test_copy_pyxel_example_creates_project_with_assets(tmp_path, monkeypatch):
    import pyxel

    package = tmp_path / "installed" / "pyxel"
    examples = package / "examples"
    assets = examples / "assets"
    assets.mkdir(parents=True)
    example = examples / "02_jump_game.py"
    example.write_text('import pyxel\npyxel.load("assets/game.pyxres")\n', encoding="utf-8")
    (assets / "game.pyxres").write_bytes(b"resource")
    monkeypatch.setattr(pyxel, "__file__", str(package / "__init__.py"))
    course = tmp_path / "course"
    course.mkdir()

    target, created = copy_pyxel_example_to_course(example, course)
    same_target, created_again = copy_pyxel_example_to_course(example, course)

    assert created
    assert not created_again
    assert same_target == target
    assert target.read_text(encoding="utf-8") == example.read_text(encoding="utf-8")
    assert (target.parent / "assets" / "game.pyxres").read_bytes() == b"resource"
    metadata = json.loads((target.parent / "projekt.json").read_text(encoding="utf-8"))
    assert metadata["kind"] == "pyxel"
    assert metadata["resources"] == ""


def test_github_version_reads_remote_pyproject(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return b'[project]\nname = "PyKIM"\nversion = "9.9.9"\n'

    monkeypatch.setattr("pykim.guide.system.urlopen", lambda request, timeout: Response())

    info = github_version()

    assert info["github"] == "9.9.9"
    assert info["different"]


def test_release_update_selects_matching_macos_architecture(monkeypatch):
    monkeypatch.setattr("pykim.guide.updates.platform.machine", lambda: "x86_64")
    monkeypatch.setattr(
        "pykim.guide.updates._json_url",
        lambda url, timeout: {
            "tag_name": "v9.9.9",
            "html_url": "https://example.invalid/release",
            "assets": [
                {
                    "name": "PyKIM-Suite-9.9.9-macos-arm64.dmg",
                    "browser_download_url": "https://example.invalid/arm.dmg",
                },
                {
                    "name": "PyKIM-Suite-9.9.9-macos-x86_64.dmg",
                    "browser_download_url": "https://example.invalid/intel.dmg",
                },
            ],
        },
    )

    update = check_app_update()

    assert update.newer
    assert update.download_url.endswith("intel.dmg")


def test_content_update_compares_bundled_manifest(tmp_path, monkeypatch):
    packaged = tmp_path / "guide"
    packaged.mkdir()
    (packaged / "content-manifest.json").write_text(
        json.dumps({"content_version": "2026.08.1"}), encoding="utf-8"
    )
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "pykim.guide.updates._json_url",
        lambda url, timeout: {
            "content_version": "2026.08.2",
            "minimum_app_version": "0.2.0",
        },
    )

    update = check_content_update(packaged)

    assert update.installed == "2026.08.1"
    assert update.newer
    assert update.compatible


def test_content_version_is_displayed_as_german_date():
    assert format_content_version("2026.08.1") == "01.08.2026"
    assert format_content_version("commit-abc") == "commit-abc"


def test_certificate_content_sync_downloads_individual_hashed_files(tmp_path, monkeypatch):
    from pykim.submission.crypto import ContentConfiguration

    files = {
        "content.yml": (
            b"format: 1\nid: testkurs\nchapters:\n  imperativ:\n"
            b"    - Skripte/imperativ/01_start.md\nexercises:\n"
            b"  - id: quadrat-5\n    assignment: Aufgaben/imperativ/quadrat-5.md\n"
            b"    trainer: Trainer/quadrat-5.yml\n"
        ),
        "Skripte/imperativ/01_start.md": b"# Start\n",
        "Aufgaben/imperativ/quadrat-5.md": b"# Quadrat\n",
        "Trainer/quadrat-5.yml": (
            b"format: 1\nid: quadrat-5\ntitle: Quadrat\ntests:\n"
            b"  - type: square\n    start: [50, 50]\n    side: 5\n"
        ),
    }
    index = {
        "format": 1,
        "scope": "trainer",
        "files": {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            for name, data in files.items() if name.startswith("Trainer/")
        },
    }
    revision = "a" * 40
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "pykim.guide.updates._json_url",
        lambda _url, _timeout: {"sha": revision},
    )

    def download(url, _timeout):
        if url.endswith("/.pykim/trainer-hashes.json"):
            return json.dumps(index).encode("utf-8")
        return files[next(name for name in files if url.endswith("/" + name))]

    monkeypatch.setattr("pykim.guide.updates._download", download)
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
    )

    target = sync_certificate_content(configuration)

    assert target.name == revision
    assert (target / "Skripte/imperativ/01_start.md").read_bytes() == files[
        "Skripte/imperativ/01_start.md"
    ]
    assert active_content_root(PACKAGED_CONTENT_ROOT) == target


def test_certificate_authorization_uses_same_named_repository_hash(monkeypatch):
    from pykim.submission.crypto import ContentConfiguration

    certificate = b'{"format":"test-certificate"}'
    expected = hashlib.sha256(certificate).hexdigest()
    requested = []
    monkeypatch.setattr(
        "pykim.guide.updates._download",
        lambda url, _timeout: requested.append(url) or f"sha256:{expected}\n".encode("ascii"),
    )
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
        "python-11a.pykim-cert",
    )

    result = verify_certificate_authorization(certificate, configuration)

    assert result.checked_online
    assert requested == [
        "https://raw.githubusercontent.com/finalnode/PyKIM_Kurs/main/"
        "certificates/python-11a.pykim-cert"
    ]


def test_certificate_authorization_rejects_unlisted_certificate(monkeypatch):
    from pykim.submission.crypto import ContentConfiguration

    monkeypatch.setattr(
        "pykim.guide.updates._download",
        lambda *_args: b"sha256:" + b"0" * 64,
    )
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
        "python-11a.pykim-cert",
    )

    with pytest.raises(ValueError, match="nicht zugelassen"):
        verify_certificate_authorization(b"anderes Zertifikat", configuration)


def test_trainer_verification_ignores_remote_assignment_only_changes(tmp_path, monkeypatch):
    from pykim.submission.crypto import ContentConfiguration

    files = {
        "content.yml": (
            b"format: 1\nid: testkurs\nchapters: {}\nexercises:\n"
            b"  - id: quadrat-5\n    assignment: Aufgaben/imperativ/quadrat-5.md\n"
            b"    trainer: Trainer/quadrat-5.yml\n"
        ),
        "Aufgaben/imperativ/quadrat-5.md": b"# Alte Aufgabe\n",
        "Trainer/quadrat-5.yml": (
            b"format: 1\nid: quadrat-5\ntitle: Quadrat\ntests:\n"
            b"  - type: square\n    start: [50, 50]\n    side: 5\n"
        ),
    }
    index = {
        "format": 1,
        "scope": "trainer",
        "files": {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            for name, data in files.items() if name.startswith("Trainer/")
        },
    }
    revision = "b" * 40
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("pykim.guide.updates._json_url", lambda *_args: {"sha": revision})

    def download(url, _timeout):
        if url.endswith("/.pykim/trainer-hashes.json"):
            return json.dumps(index).encode("utf-8")
        return files[next(name for name in files if url.endswith("/" + name))]

    monkeypatch.setattr("pykim.guide.updates._download", download)
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
    )
    sync_certificate_content(configuration)

    files["Aufgaben/imperativ/quadrat-5.md"] = b"# Neue Aufgabenformulierung\n"
    result = verify_certificate_trainers(configuration)

    assert result.checked_online
    assert not result.updated


def test_trainer_verification_replaces_changed_trainer_data(tmp_path, monkeypatch):
    from pykim.submission.crypto import ContentConfiguration

    old_trainer = (
        b"format: 1\nid: quadrat-5\ntitle: Quadrat\ntests:\n"
        b"  - type: square\n    start: [50, 50]\n    side: 5\n"
    )
    new_trainer = old_trainer.replace(b"side: 5", b"side: 6")
    files = {
        "content.yml": (
            b"format: 1\nid: testkurs\nchapters: {}\nexercises:\n"
            b"  - id: quadrat-5\n    assignment: Aufgaben/imperativ/quadrat-5.md\n"
            b"    trainer: Trainer/quadrat-5.yml\n"
        ),
        "Aufgaben/imperativ/quadrat-5.md": b"# Quadrat\n",
        "Trainer/quadrat-5.yml": old_trainer,
    }

    def index():
        return {
            "format": 1,
            "scope": "trainer",
            "files": {
                name: {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
                for name, data in files.items() if name.startswith("Trainer/")
            },
        }

    revisions = iter(("c" * 40, "d" * 40))
    current_revision = [next(revisions)]
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "pykim.guide.updates._json_url",
        lambda *_args: {"sha": current_revision[0]},
    )

    def download(url, _timeout):
        if url.endswith("/.pykim/trainer-hashes.json"):
            return json.dumps(index()).encode("utf-8")
        return files[next(name for name in files if url.endswith("/" + name))]

    monkeypatch.setattr("pykim.guide.updates._download", download)
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
    )
    sync_certificate_content(configuration)

    files["Trainer/quadrat-5.yml"] = new_trainer
    current_revision[0] = next(revisions)
    result = verify_certificate_trainers(configuration)

    assert result.checked_online
    assert result.updated
    assert (
        active_content_root(PACKAGED_CONTENT_ROOT) / "Trainer/quadrat-5.yml"
    ).read_bytes() == new_trainer


def test_missing_first_release_is_treated_as_current(tmp_path, monkeypatch):
    packaged = tmp_path / "guide"
    packaged.mkdir()
    (packaged / "content-manifest.json").write_text(
        json.dumps({"content_version": "2026.08.1"}), encoding="utf-8"
    )
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "pykim.guide.updates._json_url",
        lambda url, timeout: (_ for _ in ()).throw(
            HTTPError(url, 404, "Not Found", None, None)
        ),
    )

    status = check_updates(packaged)

    assert status.error == ""
    assert status.app is not None and not status.app.newer
    assert status.content is not None and not status.content.newer


def test_run_student_program_is_limited_to_python_files_in_course(
    tmp_path, monkeypatch
):
    course = tmp_path / "course"
    task = course / "tasks" / "square.py"
    task.parent.mkdir(parents=True)
    task.write_text("print('ok')", encoding="utf-8")
    calls = []
    monkeypatch.setattr(
        "pykim.guide.system.subprocess.Popen",
        lambda command, cwd=None, env=None: calls.append((command, cwd, env)),
    )
    monkeypatch.setattr(
        "pykim.guide.runtime.selected_runtime",
        lambda course=None: RuntimeCandidate(
            __import__("sys").executable, "3.11.0", "Test", True, True, True
        ),
    )

    assert run_student_program(task, course) == task
    assert calls[0][0][1] == str(task)
    assert calls[0][1] == task.parent
    assert str(course.resolve()) in calls[0][2]["PYTHONPATH"].split(__import__("os").pathsep)

    outside = tmp_path / "outside.py"
    outside.write_text("print('no')", encoding="utf-8")
    with pytest.raises(ValueError, match="Kursordner"):
        run_student_program(outside, course)


def test_run_student_program_rejects_non_python_files(tmp_path):
    course = tmp_path / "course"
    course.mkdir()
    text = course / "notes.txt"
    text.write_text("nothing", encoding="utf-8")

    with pytest.raises(ValueError, match="Python-Dateien"):
        run_student_program(text, course)


def test_execute_student_program_captures_output(tmp_path, monkeypatch):
    course = tmp_path / "course"
    task = course / "task.py"
    course.mkdir()
    task.write_text("print('Hallo')", encoding="utf-8")

    class Completed:
        returncode = 0
        stdout = "Hallo\n"
        stderr = ""

    calls = []
    monkeypatch.setattr(
        "pykim.guide.system.subprocess.run",
        lambda command, **kwargs: (calls.append((command, kwargs)) or Completed()),
    )
    monkeypatch.setattr(
        "pykim.guide.runtime.selected_runtime",
        lambda course=None: RuntimeCandidate(
            __import__("sys").executable, "3.11.0", "Test", True, True, True
        ),
    )

    result = execute_student_program(task, course)

    assert result.stdout == "Hallo\n"
    assert result.returncode == 0
    assert calls[0][1]["capture_output"] is True


def test_read_and_save_student_source_only_inside_course(tmp_path):
    course = tmp_path / "course"
    task = course / "tasks" / "square.py"
    task.parent.mkdir(parents=True)
    task.write_text("right(4)\n", encoding="utf-8")

    assert read_student_source(task, course) == "right(4)\n"
    assert save_student_source(task, "right(5)\n", course) == task
    assert task.read_text(encoding="utf-8") == "right(5)\n"

    outside = tmp_path / "outside.py"
    outside.write_text("print('no')", encoding="utf-8")
    with pytest.raises(ValueError, match="Kursordner"):
        save_student_source(outside, "print('changed')", course)
    assert outside.read_text(encoding="utf-8") == "print('no')"


def test_student_source_detects_external_ide_changes(tmp_path):
    course = tmp_path / "course"
    task = course / "task.py"
    course.mkdir()
    task.write_text("right(4)\n", encoding="utf-8")
    loaded_hash = source_hash(task.read_text(encoding="utf-8"))

    task.write_text("# Änderung aus Thonny\n", encoding="utf-8")

    with pytest.raises(SourceConflictError, match="außerhalb"):
        save_student_source(task, "right(5)\n", course, expected_hash=loaded_hash)
    assert task.read_text(encoding="utf-8") == "# Änderung aus Thonny\n"


def test_reset_exercise_creates_backups_for_source_and_progress(tmp_path, monkeypatch):
    course = tmp_path / "course"
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    create_course(course)
    provision_course_exercises(course)
    task = exercise_file("quadrat-5", course)
    assert task is not None
    task.write_text("right(5)\n", encoding="utf-8")
    progress = course / ".pykim" / "progress.json"
    progress.parent.mkdir(exist_ok=True)
    progress.write_text(
        json.dumps({"format": 1, "attempts": [
            {"exercise": "quadrat-5"}, {"exercise": "treppe-5"}
        ], "journal": {}}),
        encoding="utf-8",
    )

    reset_exercise_file("quadrat-5", course)
    assert clear_exercise_progress("quadrat-5", course) == 1

    assert 'run(check="quadrat-5")' in task.read_text(encoding="utf-8")
    assert load_progress(course)["attempts"] == [{"exercise": "treppe-5"}]
    assert list((course / ".pykim" / "backups").glob("quadrat_5-*.py"))
    assert list((course / ".pykim" / "backups").glob("progress-quadrat-5-*.json"))


def test_execution_manager_captures_output_and_stops_programs(tmp_path):
    course = tmp_path / "course"
    course.mkdir()
    quick = course / "quick.py"
    quick.write_text("print('Hallo aus PyKIM')\n", encoding="utf-8")
    manager = ExecutionManager()

    result = manager.execute(quick, course)
    assert result.returncode == 0
    assert result.stdout.strip() == "Hallo aus PyKIM"

    slow = course / "slow.py"
    slow.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    results = []
    worker = threading.Thread(target=lambda: results.append(manager.execute(slow, course)))
    worker.start()
    for _ in range(100):
        if manager.is_running(slow):
            break
        time.sleep(0.01)
    assert manager.stop(slow)
    worker.join(timeout=5)
    assert not worker.is_alive()
    assert results[0].stopped


def test_script_example_manager_streams_output_before_program_finishes():
    manager = ScriptExampleManager()
    job_id = manager.start(
        "import time\nprint('sofort')\ntime.sleep(1)\nprint('fertig')"
    )

    live_status = None
    for _ in range(100):
        live_status = manager.status(job_id)
        if live_status and "sofort" in live_status["stdout"]:
            break
        time.sleep(0.01)

    assert live_status is not None
    assert "sofort" in live_status["stdout"]
    assert live_status["running"]

    for _ in range(200):
        final_status = manager.status(job_id)
        if final_status and not final_status["running"]:
            break
        time.sleep(0.01)
    assert final_status["returncode"] == 0
    assert "fertig" in final_status["stdout"]


def test_pyxel_repair_uses_supported_version_range(monkeypatch):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return object()

    monkeypatch.setattr("pykim.guide.system.subprocess.run", run)

    install_or_repair_pyxel()

    assert calls[0][0][-1] == "pyxel>=2.2,<3"
    assert calls[0][1]["check"] is True
    execute_student_program,
