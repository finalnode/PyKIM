"""Getrennte Updatekanäle für App-Bundles und Lerninhalte."""

from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import shutil
import stat
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pykim

from .course import _config_directory


REPOSITORY = "finalnode/PyKIM"
RELEASE_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
CONTENT_MANIFEST_URL = (
    f"https://raw.githubusercontent.com/{REPOSITORY}/main/content-manifest.json"
)
MAX_CONTENT_FILES = 500
MAX_CONTENT_SIZE = 20 * 1024 * 1024


@dataclass(frozen=True)
class AppUpdate:
    installed: str
    available: str
    newer: bool
    download_url: str
    release_url: str


@dataclass(frozen=True)
class ContentUpdate:
    installed: str
    available: str
    newer: bool
    compatible: bool
    manifest: dict[str, object]


@dataclass(frozen=True)
class UpdateStatus:
    app: AppUpdate | None
    content: ContentUpdate | None
    error: str = ""


def _version(value: str) -> tuple[int, ...]:
    parts = []
    for item in value.strip().lstrip("v").split("."):
        digits = "".join(character for character in item if character.isdigit())
        parts.append(int(digits or 0))
    return tuple(parts)


def _json_url(url: str, timeout: float) -> dict[str, object]:
    request = Request(url, headers={"User-Agent": f"PyKIM/{pykim.__version__}"})
    with urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Die Updateantwort ist kein JSON-Objekt.")
    return data


def content_directory() -> Path:
    return _config_directory() / "content"


def _bundled_content_version(packaged_root: Path) -> str:
    manifest = packaged_root / "content-manifest.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return str(data.get("content_version", "0"))
    except (OSError, ValueError, TypeError):
        return "0"


def active_content_root(packaged_root: Path) -> Path:
    """Liefere ein geprüft aktiviertes Overlay oder die eingebauten Inhalte."""
    configured = os.environ.get("PYKIM_CONTENT_DIR")
    if configured:
        root = Path(configured).expanduser().resolve()
        return root if root.is_dir() else packaged_root
    marker = content_directory() / "active.json"
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
        version = str(data["content_version"])
        root = content_directory() / "versions" / version
        manifest = json.loads(
            (root / "content-manifest.json").read_text(encoding="utf-8")
        )
        if root.is_dir() and isinstance(manifest, dict):
            _validate_content(root, manifest)
            return root
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return packaged_root


def installed_content_version(packaged_root: Path) -> str:
    root = active_content_root(packaged_root)
    return _bundled_content_version(root)


def check_app_update(timeout: float = 5.0) -> AppUpdate:
    data = _json_url(RELEASE_URL, timeout)
    available = str(data.get("tag_name", "0")).lstrip("v")
    architecture = platform.machine().lower()
    assets = data.get("assets", [])
    download = ""
    if isinstance(assets, list):
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            name = str(asset.get("name", "")).lower()
            if name.endswith(".dmg") and architecture in name:
                download = str(asset.get("browser_download_url", ""))
                break
    return AppUpdate(
        pykim.__version__,
        available,
        _version(available) > _version(pykim.__version__),
        download,
        str(data.get("html_url", f"https://github.com/{REPOSITORY}/releases")),
    )


def check_content_update(packaged_root: Path, timeout: float = 5.0) -> ContentUpdate:
    manifest = _json_url(CONTENT_MANIFEST_URL, timeout)
    available = str(manifest.get("content_version", "0"))
    installed = installed_content_version(packaged_root)
    minimum = str(manifest.get("minimum_app_version", "0"))
    return ContentUpdate(
        installed,
        available,
        _version(available) > _version(installed),
        _version(pykim.__version__) >= _version(minimum),
        manifest,
    )


def check_updates(packaged_root: Path, timeout: float = 5.0) -> UpdateStatus:
    app = content = None
    errors = []
    try:
        app = check_app_update(timeout)
    except HTTPError as error:
        if error.code == 404:
            app = AppUpdate(
                pykim.__version__,
                pykim.__version__,
                False,
                "",
                f"https://github.com/{REPOSITORY}/releases",
            )
        else:
            errors.append(f"App: {error}")
    except (OSError, ValueError, KeyError) as error:
        errors.append(f"App: {error}")
    try:
        content = check_content_update(packaged_root, timeout)
    except HTTPError as error:
        if error.code == 404:
            installed = installed_content_version(packaged_root)
            content = ContentUpdate(installed, installed, False, True, {})
        else:
            errors.append(f"Inhalte: {error}")
    except (OSError, ValueError, KeyError) as error:
        errors.append(f"Inhalte: {error}")
    status = UpdateStatus(app, content, " · ".join(errors))
    cache = content_directory() / "update-status.json"
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(
            json.dumps(asdict(status), ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:
        pass
    return status


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def _validate_content(root: Path, manifest: dict[str, object]) -> None:
    expected = manifest.get("files")
    if not isinstance(expected, dict) or not expected:
        raise ValueError("Das Inhaltsmanifest enthält keine Dateien.")
    for name, digest in expected.items():
        if not isinstance(name, str) or not _safe_member(name):
            raise ValueError(f"Unsicherer Inhaltspfad: {name!r}")
        target = root / name
        if not target.is_file():
            raise ValueError(f"Inhaltsdatei fehlt: {name}")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != str(digest).removeprefix("sha256:"):
            raise ValueError(f"Prüfsumme stimmt nicht: {name}")


def install_content_update(manifest: dict[str, object], timeout: float = 30.0) -> Path:
    """Lade, prüfe und aktiviere ein Inhaltspaket atomar."""
    version = str(manifest.get("content_version", "")).strip()
    package_url = str(manifest.get("package_url", "")).strip()
    package_hash = str(manifest.get("package_sha256", "")).removeprefix("sha256:")
    if not version or not package_url or len(package_hash) != 64:
        raise ValueError("Das Inhaltsmanifest ist unvollständig.")
    request = Request(package_url, headers={"User-Agent": f"PyKIM/{pykim.__version__}"})
    with urlopen(request, timeout=timeout) as response:
        archive = response.read()
    if hashlib.sha256(archive).hexdigest() != package_hash:
        raise ValueError("Die Prüfsumme des Inhaltspakets stimmt nicht.")

    base = content_directory()
    versions = base / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    target = versions / version
    with tempfile.TemporaryDirectory(prefix="pykim-content-", dir=base) as temporary:
        extracted = Path(temporary) / "content"
        extracted.mkdir()
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            members = bundle.infolist()
            if len(members) > MAX_CONTENT_FILES:
                raise ValueError("Das Inhaltspaket enthält zu viele Dateien.")
            if sum(item.file_size for item in members) > MAX_CONTENT_SIZE:
                raise ValueError("Das Inhaltspaket ist entpackt zu groß.")
            for item in members:
                mode = item.external_attr >> 16
                if not _safe_member(item.filename) or stat.S_ISLNK(mode):
                    raise ValueError("Das Inhaltspaket enthält unsichere Pfade.")
                destination = extracted / PurePosixPath(item.filename)
                if item.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(item) as source, destination.open("wb") as output:
                    shutil.copyfileobj(source, output)
        _validate_content(extracted, manifest)
        (extracted / "content-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if target.exists():
            shutil.rmtree(target)
        os.replace(extracted, target)

    marker = base / "active.json"
    temporary_marker = base / "active.json.tmp"
    temporary_marker.write_text(
        json.dumps({"content_version": version}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary_marker, marker)
    return target
