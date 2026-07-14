"""Minimal command-line interface for repository and installation checks."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from zeus_risk import __version__

APPLICATION_NAME = "Zeus Risk Engine"


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line parser.

    The Phase 1 CLI deliberately exposes only help and version information. Risk
    calculations will be introduced through tested application use cases in later
    phases.
    """

    parser = argparse.ArgumentParser(
        prog="zeus-risk",
        description="Modular financial risk engine — foundation release.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="show the application version and exit",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return a process exit code."""

    parser = create_parser()
    arguments = parser.parse_args(argv)

    if arguments.version:
        print(f"{APPLICATION_NAME} {__version__}")
    else:
        parser.print_help()

    return 0
