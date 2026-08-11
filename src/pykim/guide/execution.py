"""Kontrollierte Schülerprozesse mit Stoppen und sauberem Aufräumen."""

import subprocess
import sys
import threading
import os
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from .interpreter import python_command


@dataclass(frozen=True)
class ExecutionResult:
    returncode: int
    stdout: str
    stderr: str
    stopped: bool = False


class ExecutionManager:
    def __init__(self) -> None:
        self._processes: dict[Path, subprocess.Popen[str]] = {}
        self._stopped: set[Path] = set()
        self._lock = threading.Lock()

    @staticmethod
    def _target(path: str | Path, course: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        root = Path(course).expanduser().resolve()
        if not target.is_relative_to(root):
            raise ValueError("Es dürfen nur Dateien aus dem Kursordner gestartet werden.")
        if not target.is_file() or target.suffix.lower() != ".py":
            raise ValueError("Die Aufgabe muss eine vorhandene Python-Datei sein.")
        return target

    def is_running(self, path: str | Path) -> bool:
        target = Path(path).expanduser().resolve()
        with self._lock:
            process = self._processes.get(target)
            return process is not None and process.poll() is None

    def execute(self, path: str | Path, course: str | Path) -> ExecutionResult:
        target = self._target(path, course)
        environment = os.environ.copy()
        environment["PYTHONUNBUFFERED"] = "1"
        existing_pythonpath = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = os.pathsep.join(
            part
            for part in (str(Path(course).expanduser().resolve()), existing_pythonpath)
            if part
        )
        with self._lock:
            previous = self._processes.get(target)
            if previous is not None and previous.poll() is None:
                raise RuntimeError("Diese Aufgabe läuft bereits.")
            process = subprocess.Popen(
                [*python_command(), str(target)],
                cwd=target.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
            )
            self._processes[target] = process
            self._stopped.discard(target)
        try:
            stdout, stderr = process.communicate()
            with self._lock:
                stopped = target in self._stopped
            return ExecutionResult(process.returncode, stdout, stderr, stopped)
        finally:
            with self._lock:
                self._processes.pop(target, None)
                self._stopped.discard(target)

    def stop(self, path: str | Path) -> bool:
        target = Path(path).expanduser().resolve()
        with self._lock:
            process = self._processes.get(target)
            if process is None or process.poll() is not None:
                return False
            self._stopped.add(target)
            process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
        return True

    def stop_all(self) -> None:
        with self._lock:
            targets = list(self._processes)
        for target in targets:
            self.stop(target)


execution_manager = ExecutionManager()


@dataclass
class ScriptExampleJob:
    process: subprocess.Popen[str]
    path: Path
    stdout: str = ""
    stderr: str = ""
    finished: bool = False


class ScriptExampleManager:
    """Starte Skriptbeispiele und sammle ihre Ausgabe bereits während des Laufs."""

    def __init__(self) -> None:
        self._jobs: dict[str, ScriptExampleJob] = {}
        self._lock = threading.Lock()

    def start(self, source: str) -> str:
        descriptor, filename = tempfile.mkstemp(prefix="pykim-script-", suffix=".py")
        path = Path(filename)
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            target.write(source.rstrip() + "\n")
        environment = os.environ.copy()
        environment["PYKIM_PROGRESS_MODE"] = "disabled"
        environment["PYTHONUNBUFFERED"] = "1"
        try:
            process = subprocess.Popen(
                [*python_command(), "-u", str(path)],
                cwd=path.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=environment,
            )
        except Exception:
            path.unlink(missing_ok=True)
            raise
        job_id = uuid.uuid4().hex
        job = ScriptExampleJob(process, path)
        with self._lock:
            self._jobs[job_id] = job

        def read_stream(stream, attribute: str) -> None:
            if stream is None:
                return
            for chunk in iter(stream.readline, ""):
                with self._lock:
                    setattr(job, attribute, getattr(job, attribute) + chunk)
            stream.close()

        stdout_reader = threading.Thread(
            target=read_stream, args=(process.stdout, "stdout"), daemon=True
        )
        stderr_reader = threading.Thread(
            target=read_stream, args=(process.stderr, "stderr"), daemon=True
        )

        def finish() -> None:
            process.wait()
            stdout_reader.join()
            stderr_reader.join()
            path.unlink(missing_ok=True)
            with self._lock:
                job.finished = True

        stdout_reader.start()
        stderr_reader.start()
        threading.Thread(target=finish, daemon=True).start()
        return job_id

    def status(self, job_id: str) -> dict[str, object] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            returncode = job.process.poll()
            return {
                "running": not job.finished,
                "returncode": returncode if job.finished else None,
                "stdout": job.stdout,
                "stderr": job.stderr,
            }

    def stop_all(self) -> None:
        with self._lock:
            jobs = tuple(self._jobs.values())
        for job in jobs:
            if job.process.poll() is None:
                job.process.terminate()


script_example_manager = ScriptExampleManager()
