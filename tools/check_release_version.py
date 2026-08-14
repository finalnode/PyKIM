"""Prüfe den gemeinsamen Release-Tag gegen PyKIM und in:si."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def source_version(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    raise ValueError(f"Keine __version__ in {path} gefunden.")


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PyKIM-Releaseversion prüfen")
    parser.add_argument("tag", help="Git-Tag, beispielsweise v0.5.2")
    options = parser.parse_args(arguments)
    project = Path(__file__).resolve().parents[1]
    versions = {}
    for name, metadata, runtime in (
        ("PyKIM", project / "pyproject.toml", project / "src" / "pykim" / "__init__.py"),
        ("in:si", project / "insi" / "pyproject.toml", project / "insi" / "src" / "insi" / "__init__.py"),
    ):
        with metadata.open("rb") as source:
            versions[f"{name} metadata"] = str(tomllib.load(source)["project"]["version"])
        versions[f"{name} runtime"] = source_version(runtime)
    tag_version = options.tag.removeprefix("v")
    if len({*versions.values(), tag_version}) != 1:
        raise SystemExit(
            "Versionskonflikt: " + ", ".join(
                [f"Tag={tag_version}", *(f"{key}={value}" for key, value in versions.items())]
            )
        )
    print(f"Releaseversion {tag_version} ist konsistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
