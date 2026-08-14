import pytest

from pykim.testing import reset_world


@pytest.fixture(autouse=True)
def clean_world():
    reset_world()
