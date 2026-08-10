"""Lokale Werkzeuge für IDE, Updates und Pyxel-Ressourcen."""

import getpass
import platform
import shutil
import subprocess
import sys
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen

import pykim

GITHUB_REPOSITORY = "finalnode/PyKIM"


def system_user_name() -> str:
    """Liefere möglichst den Anzeigenamen, sonst den lokalen Kontonamen."""
    login = getpass.getuser().strip()
    if platform.system() != "Windows":
        try:
            import pwd

            full_name = pwd.getpwnam(login).pw_gecos.split(",", 1)[0].strip()
            if full_name:
                return full_name
        except (ImportError, KeyError, OSError):
            pass
    return login or "Schüler/in"


@dataclass(frozen=True)
class SystemStatus:
    python: str
    python_supported: bool
    pykim: str
    pyxel: bool
    thonny: bool
    vscode: bool
    platform: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ProgramResult:
    returncode: int
    stdout: str
    stderr: str


def _application_exists(name: str) -> bool:
    if platform.system() != "Darwin":
        return False
    return (Path("/Applications") / f"{name}.app").exists() or (
        Path.home() / "Applications" / f"{name}.app"
    ).exists()


def detected_ides() -> dict[str, str]:
    """Finde für den Unterricht typische IDEs samt startbarem Pfad."""
    found: dict[str, str] = {}
    candidates = {
        "thonny": ("thonny", "Thonny"),
        "vscode": ("code", "Visual Studio Code"),
        "pycharm": ("pycharm", "PyCharm"),
    }
    for key, (command, application) in candidates.items():
        executable = shutil.which(command)
        if executable:
            found[key] = executable
            continue
        if platform.system() == "Darwin":
            for root in (Path("/Applications"), Path.home() / "Applications"):
                app = root / f"{application}.app"
                if app.exists():
                    found[key] = str(app)
                    break
    return found


def system_status() -> SystemStatus:
    return SystemStatus(
        python=platform.python_version(),
        python_supported=sys.version_info >= (3, 10),
        pykim=pykim.__version__,
        pyxel=shutil.which("pyxel") is not None,
        thonny=shutil.which("thonny") is not None or _application_exists("Thonny"),
        vscode=(
            shutil.which("code") is not None
            or _application_exists("Visual Studio Code")
        ),
        platform=platform.system(),
    )


def open_path(
    path: str | Path,
    ide: str = "system",
    custom_executable: str | Path | None = None,
) -> None:
    """Öffne eine Datei oder einen Ordner mit einer bewusst gewählten Anwendung."""
    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"{target} wurde nicht gefunden.")
    system = platform.system()
    if ide == "custom":
        if custom_executable is None:
            raise RuntimeError("Für die eigene IDE wurde kein Programmpfad festgelegt.")
        executable = Path(custom_executable).expanduser().resolve()
        if not executable.exists():
            raise FileNotFoundError(f"Die eingestellte IDE {executable} wurde nicht gefunden.")
        command = (
            ["open", "-a", str(executable), str(target)]
            if system == "Darwin" and executable.suffix == ".app"
            else [str(executable), str(target)]
        )
    elif ide in {"thonny", "vscode", "pycharm"}:
        installed = detected_ides().get(ide)
        if installed is None:
            raise RuntimeError(f"Die ausgewählte IDE {ide} wurde nicht gefunden.")
        executable = Path(installed)
        command = (
            ["open", "-a", str(executable), str(target)]
            if system == "Darwin" and executable.suffix == ".app"
            else [installed, str(target)]
        )
    elif system == "Darwin":
        command = ["open", str(target)]
    elif system == "Windows":
        command = ["explorer", str(target)]
    else:
        command = ["xdg-open", str(target)]
    subprocess.Popen(command)


def open_in_preferred_ide(path: str | Path) -> None:
    """Öffne einen Pfad mit der im Lernstudio gespeicherten IDE."""
    from .course import get_ide_preference

    preference = get_ide_preference()
    open_path(path, preference["ide"], preference["path"] or None)


def launch_pyxel_editor(resource: str | Path) -> Path:
    """Starte den offiziellen Editor für Sprites, Tilemaps, Sounds und Musik."""
    command = shutil.which("pyxel")
    if command is None:
        raise RuntimeError("Der Befehl pyxel wurde nicht gefunden.")
    target = Path(resource).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.Popen([command, "edit", str(target)])
    return target


def pyxel_examples() -> tuple[Path, ...]:
    """Liefere die Python-Beispiele der tatsächlich installierten Pyxel-Version."""
    try:
        import pyxel
    except ImportError:
        return ()
    directory = Path(pyxel.__file__).resolve().parent / "examples"
    try:
        return tuple(sorted(directory.glob("*.py"), key=lambda path: path.name))
    except OSError:
        return ()


def launch_pyxel_example(example: str | Path) -> Path:
    """Starte ausschließlich ein offizielles Beispiel der Pyxel-Installation."""
    command = shutil.which("pyxel")
    if command is None:
        raise RuntimeError("Der Befehl pyxel wurde nicht gefunden.")
    available = {path.resolve() for path in pyxel_examples()}
    target = Path(example).expanduser().resolve()
    if target not in available:
        raise ValueError("Es dürfen nur mitgelieferte Pyxel-Beispiele gestartet werden.")
    subprocess.Popen([command, "run", str(target)], cwd=target.parent)
    return target


def _course_file(path: str | Path, course: str | Path) -> Path:
    """Erlaube ausführbare Dateien ausschließlich innerhalb des Kursordners."""
    target = Path(path).expanduser().resolve()
    root = Path(course).expanduser().resolve()
    if not target.is_relative_to(root):
        raise ValueError("Es dürfen nur Dateien aus dem Kursordner gestartet werden.")
    if not target.is_file():
        raise FileNotFoundError(f"{target} wurde nicht gefunden.")
    return target


def run_student_program(path: str | Path, course: str | Path) -> Path:
    """Starte eine Python-Aufgabe mit derselben Installation wie die Suite."""
    target = _course_file(path, course)
    if target.suffix.lower() != ".py":
        raise ValueError("Nur Python-Dateien mit der Endung .py können gestartet werden.")
    subprocess.Popen([sys.executable, str(target)], cwd=target.parent)
    return target


def execute_student_program(path: str | Path, course: str | Path) -> ProgramResult:
    """Führe eine Aufgabe aus und sammle ihre vollständige Konsolenausgabe."""
    target = _course_file(path, course)
    if target.suffix.lower() != ".py":
        raise ValueError("Nur Python-Dateien mit der Endung .py können gestartet werden.")
    completed = subprocess.run(
        [sys.executable, str(target)],
        cwd=target.parent,
        capture_output=True,
        text=True,
    )
    return ProgramResult(completed.returncode, completed.stdout, completed.stderr)


def read_student_source(path: str | Path, course: str | Path) -> str:
    """Lese eine Python-Aufgabe ausschließlich innerhalb des Kursordners."""
    target = _course_file(path, course)
    if target.suffix.lower() != ".py":
        raise ValueError("Nur Python-Dateien mit der Endung .py können bearbeitet werden.")
    return target.read_text(encoding="utf-8")


def save_student_source(path: str | Path, source: str, course: str | Path) -> Path:
    """Speichere eine Schülerdatei atomar, ohne andere lokale Dateien freizugeben."""
    target = _course_file(path, course)
    if target.suffix.lower() != ".py":
        raise ValueError("Nur Python-Dateien mit der Endung .py können bearbeitet werden.")
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(source)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, target)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return target


def install_or_repair_pyxel() -> subprocess.CompletedProcess[str]:
    """Installiere die von PyKIM unterstützte Pyxel-Version nach Bestätigung."""
    return subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pyxel>=2.2,<3"],
        check=True,
        capture_output=True,
        text=True,
    )


def github_version(timeout: float = 5.0) -> dict[str, object]:
    """Lies die Version des main-Branches ohne etwas zu installieren."""
    url = f"https://raw.githubusercontent.com/{GITHUB_REPOSITORY}/main/pyproject.toml"
    request = Request(url, headers={"User-Agent": "PyKIM-Guide"})
    with urlopen(request, timeout=timeout) as response:
        text = response.read().decode("utf-8")
    try:
        import tomllib
    except ImportError:  # Python 3.10
        import tomli as tomllib
    remote = tomllib.loads(text)["project"]["version"]
    return {
        "installed": pykim.__version__,
        "github": remote,
        "different": remote != pykim.__version__,
        "url": f"https://github.com/{GITHUB_REPOSITORY}",
    }


def update_from_github() -> subprocess.CompletedProcess[str]:
    """Installiere nach expliziter Bestätigung den aktuellen main-Branch."""
    url = f"git+https://github.com/{GITHUB_REPOSITORY}.git"
    return subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", url],
        check=True,
        capture_output=True,
        text=True,
    )
