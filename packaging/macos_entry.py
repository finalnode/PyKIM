"""Einstiegspunkt der eigenständigen macOS-App."""

from __future__ import annotations

import multiprocessing
import faulthandler
import os
import runpy
import sys
import traceback
from datetime import datetime
from pathlib import Path


def restore_standard_streams() -> None:
    """Verbinde den windowed PyInstaller-Prozess wieder mit seinen Pipes."""
    if sys.stdout is None:
        sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
    if sys.stderr is None:
        sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)


def run_python(arguments: list[str]) -> int:
    """Führe Schülercode mit dem im App-Bundle enthaltenen Python aus."""
    args = list(arguments)
    if args and args[0] == "-u":
        args.pop(0)
    if len(args) >= 2 and args[0] == "-c":
        sys.argv = ["-c", *args[2:]]
        namespace = {"__name__": "__main__", "__package__": None}
        exec(compile(args[1], "<string>", "exec"), namespace, namespace)
        return 0
    if len(args) >= 2 and args[0] == "-m":
        sys.argv = [args[1], *args[2:]]
        runpy.run_module(args[1], run_name="__main__", alter_sys=True)
        return 0
    if args and Path(args[0]).suffix.lower() == ".py":
        script = Path(args[0]).expanduser().resolve()
        sys.argv = [str(script), *args[1:]]
        runpy.run_path(str(script), run_name="__main__")
        return 0
    raise SystemExit(
        "Der eingebettete Interpreter erwartet -c CODE, -m MODUL oder eine .py-Datei."
    )


if __name__ == "__main__":
    multiprocessing.freeze_support()
    if len(sys.argv) > 1 and sys.argv[1] == "--pykim-python":
        restore_standard_streams()
        status = run_python(sys.argv[2:])
        sys.stdout.flush()
        sys.stderr.flush()
        raise SystemExit(status)
    from pykim.guide.app import main

    log_directory = Path.home() / ".pykim" / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    with (log_directory / "macos-app.log").open("a", encoding="utf-8", buffering=1) as log:
        sys.stdout = log
        sys.stderr = log
        faulthandler.enable(log)
        print(f"\n[{datetime.now().isoformat()}] PyKIM Suite startet")
        try:
            # Finder kann eigene Kommandozeilenargumente ergänzen. Die Desktop-App
            # startet deshalb immer bewusst im nativen Modus ohne CLI-Auswertung.
            main(arguments=[], native=True)
        except BaseException:
            traceback.print_exc(file=log)
            raise
