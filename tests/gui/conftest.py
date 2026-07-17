"""Headless Qt setup shared by desktop-interface tests."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from zeus_risk.app import create_application  # noqa: E402


@pytest.fixture(scope="session")
def qt_application() -> Iterator[QApplication]:
    """Provide the unique QApplication without entering its event loop."""

    application = create_application(["pytest"])
    yield application
    application.processEvents()
