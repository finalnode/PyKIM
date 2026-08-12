import pytest

from pykim.testing import reset_world


@pytest.fixture(autouse=True)
def clean_world(monkeypatch, tmp_path):
    # Tests dürfen niemals den lokal konfigurierten Schülerkurs verändern.
    monkeypatch.setenv("PYKIM_PROGRESS_MODE", "disabled")
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    reset_world()
