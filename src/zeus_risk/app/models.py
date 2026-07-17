"""Qt model/view adapters for portfolio positions and validation issues."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QColor

from zeus_risk.domain import Position, ValidationSeverity
from zeus_risk.importers import LocatedValidationIssue

_DISPLAY_ROLE = int(Qt.ItemDataRole.DisplayRole)
_TOOLTIP_ROLE = int(Qt.ItemDataRole.ToolTipRole)
_FOREGROUND_ROLE = int(Qt.ItemDataRole.ForegroundRole)
_ALIGNMENT_ROLE = int(Qt.ItemDataRole.TextAlignmentRole)


class PositionTableModel(QAbstractTableModel):
    """Read-only position table backed by immutable domain objects."""

    HEADERS = (
        "Ticker",
        "Classe",
        "Quantidade",
        "Preço",
        "Valor de mercado",
        "Moeda",
        "Setor",
    )

    def __init__(self, positions: tuple[Position, ...] = ()) -> None:
        super().__init__()
        self._positions = positions

    @property
    def positions(self) -> tuple[Position, ...]:
        """Return the immutable rows currently presented."""

        return self._positions

    def set_positions(self, positions: tuple[Position, ...]) -> None:
        """Replace all rows through the model reset protocol."""

        if not isinstance(positions, tuple) or any(
            not isinstance(position, Position) for position in positions
        ):
            raise TypeError("positions must be a tuple of Position values")
        self.beginResetModel()
        self._positions = positions
        self.endResetModel()

    def rowCount(
        self,
        parent: QModelIndex | QPersistentModelIndex | None = None,
    ) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self._positions)

    def columnCount(
        self,
        parent: QModelIndex | QPersistentModelIndex | None = None,
    ) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = _DISPLAY_ROLE,
    ) -> object | None:
        if not index.isValid() or not 0 <= index.row() < len(self._positions):
            return None
        if role == _ALIGNMENT_ROLE and index.column() in (2, 3, 4):
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        if role not in (_DISPLAY_ROLE, _TOOLTIP_ROLE):
            return None

        position = self._positions[index.row()]
        values = (
            position.instrument.ticker,
            position.instrument.asset_class.value,
            format(position.quantity, "f"),
            format(position.price, "f"),
            format(position.market_value, "f"),
            position.instrument.currency.code,
            position.instrument.sector or "—",
        )
        return values[index.column()]

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = _DISPLAY_ROLE,
    ) -> object | None:
        if (
            role == _DISPLAY_ROLE
            and orientation is Qt.Orientation.Horizontal
            and 0 <= section < len(self.HEADERS)
        ):
            return self.HEADERS[section]
        return None


class IssueTableModel(QAbstractTableModel):
    """Read-only table retaining validation codes and physical source lines."""

    HEADERS = ("Severidade", "Linha", "Código", "Mensagem", "Campo", "Item")
    _COLORS = {
        ValidationSeverity.INFO: QColor("#2563eb"),
        ValidationSeverity.WARNING: QColor("#b45309"),
        ValidationSeverity.ERROR: QColor("#b91c1c"),
    }

    def __init__(self, issues: tuple[LocatedValidationIssue, ...] = ()) -> None:
        super().__init__()
        self._issues = issues

    @property
    def issues(self) -> tuple[LocatedValidationIssue, ...]:
        """Return the located issues currently presented."""

        return self._issues

    def set_issues(self, issues: tuple[LocatedValidationIssue, ...]) -> None:
        """Replace all rows through the model reset protocol."""

        if not isinstance(issues, tuple) or any(
            not isinstance(item, LocatedValidationIssue) for item in issues
        ):
            raise TypeError("issues must be a tuple of LocatedValidationIssue values")
        self.beginResetModel()
        self._issues = issues
        self.endResetModel()

    def rowCount(
        self,
        parent: QModelIndex | QPersistentModelIndex | None = None,
    ) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self._issues)

    def columnCount(
        self,
        parent: QModelIndex | QPersistentModelIndex | None = None,
    ) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = _DISPLAY_ROLE,
    ) -> object | None:
        if not index.isValid() or not 0 <= index.row() < len(self._issues):
            return None
        located = self._issues[index.row()]
        issue = located.issue
        if role == _FOREGROUND_ROLE:
            return self._COLORS[issue.severity]
        if role == _TOOLTIP_ROLE:
            details = [f"{issue.code}: {issue.message}"]
            if issue.item:
                details.append(f"Item: {issue.item}")
            return "\n".join(details)
        if role != _DISPLAY_ROLE:
            return None
        values = (
            issue.severity.value,
            str(located.line_number) if located.line_number is not None else "—",
            issue.code,
            issue.message,
            issue.field or "—",
            issue.item or "—",
        )
        return values[index.column()]

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = _DISPLAY_ROLE,
    ) -> object | None:
        if (
            role == _DISPLAY_ROLE
            and orientation is Qt.Orientation.Horizontal
            and 0 <= section < len(self.HEADERS)
        ):
            return self.HEADERS[section]
        return None
