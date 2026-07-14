"""Integration tests for the installed module entry point."""

from __future__ import annotations

import subprocess
import sys


def run_module(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the package with the interpreter executing the test suite."""

    return subprocess.run(
        [sys.executable, "-m", "zeus_risk", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def test_module_entrypoint_displays_version() -> None:
    """The installed module must expose the same version as the package."""

    result = run_module("--version")

    assert result.returncode == 0
    assert result.stdout == "Zeus Risk Engine 0.1.0\n"
    assert result.stderr == ""


def test_module_entrypoint_displays_help() -> None:
    """Running without arguments must be safe and informative."""

    result = run_module()

    assert result.returncode == 0
    assert "usage: zeus-risk" in result.stdout
    assert result.stderr == ""
