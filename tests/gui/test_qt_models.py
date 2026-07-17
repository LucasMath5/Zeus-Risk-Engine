"""Tests for immutable domain-to-Qt table adapters."""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from zeus_risk.app.models import IssueTableModel, PositionTableModel
from zeus_risk.domain import (
    AssetClass,
    Currency,
    Instrument,
    Position,
    ValidationIssue,
    ValidationSeverity,
)
from zeus_risk.importers import LocatedValidationIssue


def test_position_model_presents_read_only_domain_values(
    qt_application: QApplication,
) -> None:
    position = Position(
        Instrument("ZEUS", AssetClass.EQUITY, Currency("BRL"), "Technology"),
        Decimal("2.5"),
        Decimal("40"),
    )
    model = PositionTableModel((position,))

    assert model.rowCount() == 1
    assert model.columnCount() == 7
    assert model.headerData(0, Qt.Orientation.Horizontal) == "Ticker"
    assert model.data(model.index(0, 0)) == "ZEUS"
    assert model.data(model.index(0, 4)) == "100.0"

    model.set_positions(())

    assert model.rowCount() == 0
    qt_application.processEvents()


def test_issue_model_preserves_code_line_and_severity_color(
    qt_application: QApplication,
) -> None:
    issue = LocatedValidationIssue(
        issue=ValidationIssue(
            ValidationSeverity.ERROR,
            "INVALID_PRICE",
            "Price is invalid.",
            field="price",
            item="0",
        ),
        line_number=4,
    )
    model = IssueTableModel((issue,))

    assert model.data(model.index(0, 1)) == "4"
    assert model.data(model.index(0, 2)) == "INVALID_PRICE"
    assert model.data(model.index(0, 5)) == "0"
    assert model.data(model.index(0, 0), int(Qt.ItemDataRole.ForegroundRole)) == QColor("#b91c1c")
    assert "INVALID_PRICE" in str(model.data(model.index(0, 3), int(Qt.ItemDataRole.ToolTipRole)))
    qt_application.processEvents()
