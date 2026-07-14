"""Unit tests for the minimal command-line interface."""

from __future__ import annotations

import pytest

from zeus_risk.cli import APPLICATION_NAME, create_parser, main


def test_parser_uses_stable_program_name() -> None:
    """Help output should use the installed console-script name."""

    assert create_parser().prog == "zeus-risk"


def test_main_displays_version(capsys: pytest.CaptureFixture[str]) -> None:
    """The version flag should display the application name and version."""

    exit_code = main(["--version"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == f"{APPLICATION_NAME} 0.1.0\n"
    assert captured.err == ""


def test_main_displays_help_without_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    """The foundation command should guide users instead of doing hidden work."""

    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "usage: zeus-risk" in captured.out
    assert "--version" in captured.out
    assert captured.err == ""
