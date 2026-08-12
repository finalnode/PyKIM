"""Python-Aufrufe innerhalb der normalen und der gebündelten Suite."""

from __future__ import annotations

import sys
from pathlib import Path


def command_for(executable: str) -> list[str]:
    """Ergänze bei der eingefrorenen Suite deren Interpreter-Schalter."""
    command = [executable]
    if (
        getattr(sys, "frozen", False)
        and executable == sys.executable
    ):
        executable_path = Path(sys.executable)
        runner = executable_path.with_name(f"PyKIM Python{executable_path.suffix}")
        command = [str(runner if runner.is_file() else Path(sys.executable))]
        command.append("--pykim-python")
    return command


def python_command() -> list[str]:
    """Liefere den Einstieg zum eingebetteten oder normalen Interpreter."""
    return command_for(sys.executable)
