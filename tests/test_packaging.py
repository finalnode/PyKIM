from pathlib import Path


PROJECT = Path(__file__).parents[1]


def test_desktop_workflow_covers_all_release_targets():
    workflow = (PROJECT / ".github/workflows/build-desktop.yml").read_text(
        encoding="utf-8"
    )

    for expected in (
        "windows-2025",
        "ubuntu-24.04",
        "macos-15-intel",
        "runner: macos-15",
        "tools/build_desktop_app.py",
        "tools/build_macos_dmg.py --rebuild-app",
        "tools/check_release_version.py",
        "gh release upload",
    ):
        assert expected in workflow


def test_pyinstaller_specs_are_valid_python_and_use_common_entrypoint():
    for relative in (
        "packaging/desktop/PyKIM.spec",
        "packaging/macos/PyKIM.spec",
    ):
        path = PROJECT / relative
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
        assert 'packaging" / "app_entry.py' in source
