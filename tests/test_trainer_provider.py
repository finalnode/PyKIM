from dataclasses import dataclass

import pykim
from pykim import configure_trainer_provider
from pykim.trainer.models import WorldSetup


@dataclass
class ProviderRecorder:
    checked: tuple[str, str] | None = None

    def get_world_setup(self, exercise_name: str):
        assert exercise_name == "provider-test"
        return WorldSetup(
            background="dark_blue",
            start=(7, 9),
            cells=((3, 4, "yellow"),),
            obstacles=("red",),
        )

    def check_exercise(self, name, source, namespace=None):
        self.checked = (name, source)
        return object()


def test_prepare_uses_an_optional_host_provider():
    provider = ProviderRecorder()
    configure_trainer_provider(provider)
    try:
        pykim.prepare("provider-test")
        assert pykim.get_position() == (7, 9)
        assert pykim.world.background_color == "dark_blue"
        assert pykim.get_color(3, 4) == "yellow"
        assert pykim.world.obstacle_colors == ("red",)
    finally:
        configure_trainer_provider(None)


def test_run_delegates_only_the_check_to_the_host(monkeypatch):
    provider = ProviderRecorder()
    configure_trainer_provider(provider)
    monkeypatch.setenv("PYKIM_HEADLESS", "1")
    try:
        pykim.run(check="provider-test", _source="paint('red')")
        assert provider.checked == ("provider-test", "paint('red')")
    finally:
        configure_trainer_provider(None)
