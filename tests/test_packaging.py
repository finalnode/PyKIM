import zipfile

import pytest

from tools.build_package import validate_wheel


def _wheel(tmp_path, *members):
    path = tmp_path / "PyKIM-0.6.0-py3-none-any.whl"
    with zipfile.ZipFile(path, "w") as archive:
        for member in members:
            archive.writestr(member, "test")
    return path


def test_wheel_validator_accepts_only_pykim_and_metadata(tmp_path):
    wheel = _wheel(
        tmp_path,
        "pykim/__init__.py",
        "PyKIM-0.6.0.dist-info/METADATA",
    )

    assert validate_wheel(wheel) == (
        "PyKIM-0.6.0.dist-info/METADATA",
        "pykim/__init__.py",
    )


@pytest.mark.parametrize("member", ["insi/app.py", "pykim/guide/app.py"])
def test_wheel_validator_rejects_application_modules(tmp_path, member):
    wheel = _wheel(tmp_path, "pykim/__init__.py", member)

    with pytest.raises(ValueError):
        validate_wheel(wheel)


def test_wheel_validator_rejects_moved_trainer_modules(tmp_path):
    wheel = _wheel(
        tmp_path,
        "pykim/__init__.py",
        "pykim/trainer/activities.py",
    )

    with pytest.raises(ValueError, match="Ausgelagerter Paketinhalt"):
        validate_wheel(wheel)

