"""Desktop application bootstrap for Zeus Risk Engine."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from zeus_risk import __version__
from zeus_risk.app.main_window import MainWindow
from zeus_risk.app.styles import APPLICATION_STYLESHEET


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create or return the process-wide configured QApplication."""

    instance = QApplication.instance()
    if instance is not None:
        if not isinstance(instance, QApplication):
            raise RuntimeError("A non-GUI Qt application already exists")
        return instance

    application = QApplication(list(argv) if argv is not None else sys.argv)
    application.setApplicationName("Zeus Risk Engine")
    application.setApplicationDisplayName("Zeus Risk Engine")
    application.setApplicationVersion(__version__)
    application.setOrganizationName("Zeus Risk Engine")
    application.setStyle("Fusion")
    application.setStyleSheet(APPLICATION_STYLESHEET)
    return application


def main() -> int:
    """Run the desktop entry point."""

    application = create_application()
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
