import pytest

from pykim.testing import reset_world


@pytest.fixture(autouse=True)
def clean_world(monkeypatch):
    # Tests dürfen niemals den lokal konfigurierten Schülerkurs verändern.
    monkeypatch.setenv("PYKIM_PROGRESS_MODE", "disabled")
    reset_world()
