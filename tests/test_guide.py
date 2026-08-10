import json

import pykim
import pytest
from pykim.guide.app import parse_arguments
from pykim.guide.course import (
    create_course,
    exercise_file,
    get_course_directory,
    get_ide_preference,
    get_student_name,
    set_ide_preference,
)
from pykim.guide.progress import (
    load_progress,
    record_attempt,
    remove_packaged_example_attempts,
    save_journal_entry,
)
from pykim.guide.examples import copy_example_to_course, example_programs, launch_example
from pykim.guide.system import (
    execute_student_program,
    github_version,
    install_or_repair_pyxel,
    launch_pyxel_editor,
    launch_pyxel_example,
    pyxel_examples,
    read_student_source,
    run_student_program,
    save_student_source,
    system_status,
    system_user_name,
)
from pykim.trainer.assignments import ASSIGNMENTS, get_assignment
from pykim.trainer.models import CheckReport, CheckResult, OptimizationResult


def test_guide_starts_as_desktop_by_default_and_supports_browser_fallback():
    assert not parse_arguments([]).browser
    assert parse_arguments(["--browser"]).browser


def test_every_exercise_has_a_complete_assignment():
    from pykim.trainer.exercises import exercise_names

    assert set(ASSIGNMENTS) == set(exercise_names())
    assert get_assignment("quadrat-5").requirements


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
    square = course / "01_grundlagen" / "quadrat_5.py"
    square.write_text("# meine Lösung", encoding="utf-8")
    second = create_course(course, "Ada")

    assert len(first["created"]) == 12
    assert square.read_text(encoding="utf-8") == "# meine Lösung"
    assert "01_grundlagen/quadrat_5.py" in second["existing"]
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

    assert exercise_file("treppe-5") == course / "02_schleifen" / "treppe_5.py"
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
        "pykim.guide.system.subprocess.Popen", lambda command: calls.append(command)
    )
    resource = tmp_path / "assets" / "game.pyxres"

    assert launch_pyxel_editor(resource) == resource
    assert resource.parent.exists()
    assert calls == [["/usr/local/bin/pyxel", "edit", str(resource)]]


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
        lambda command, cwd=None: calls.append((command, cwd)),
    )

    assert run_student_program(task, course) == task
    assert calls[0][0][1] == str(task)
    assert calls[0][1] == task.parent

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
