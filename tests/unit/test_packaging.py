"""Packaging configuration tests for CLI importability."""

from __future__ import annotations

from pathlib import Path

import tomllib


def test_package_discovery_installs_src_namespace_for_console_scripts() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    package_find = pyproject["tool"]["setuptools"]["packages"]["find"]

    assert package_find["where"] == ["."]
    assert package_find["include"] == ["src*"]
    assert pyproject["project"]["scripts"]["uatp"] == "src.cli.main:main"
