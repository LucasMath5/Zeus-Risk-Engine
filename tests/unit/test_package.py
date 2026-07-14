"""Tests for package metadata and import boundaries."""

from __future__ import annotations

import subprocess
import sys
from importlib import metadata

import zeus_risk


def test_package_exposes_expected_version() -> None:
    """The public and installed versions must remain synchronized."""

    assert zeus_risk.__version__ == "0.1.0"
    assert metadata.version("zeus-risk-engine") == zeus_risk.__version__


def test_importing_package_does_not_import_qt() -> None:
    """The package foundation must stay independent from the future GUI."""

    import_check = (
        "import sys; import zeus_risk; "
        "qt_loaded = any(name == 'PySide6' or name.startswith('PySide6.') "
        "for name in sys.modules); raise SystemExit(qt_loaded)"
    )
    result = subprocess.run(
        [sys.executable, "-c", import_check],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
