"""Portfolio import, summary, positions, and validation page."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from zeus_risk.app.models import IssueTableModel, PositionTableModel
from zeus_risk.importers import ImportResult


class PortfolioPage(QWidget):
    """Present one reviewable portfolio import without altering domain data."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("portfolioPage")
        self.position_model = PositionTableModel()
        self.issue_model = IssueTableModel()

        root = QVBoxLayout(self)
        root.setContentsMargins(2, 8, 2, 8)
        root.setSpacing(14)

        heading = QHBoxLayout()
        heading_text = QVBoxLayout()
        title = QLabel("Carteira e validação")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Importe CSV ou XLSX, revise os códigos de validação e confirme as posições."
        )
        subtitle.setObjectName("pageSubtitle")
        heading_text.addWidget(title)
        heading_text.addWidget(subtitle)
        heading.addLayout(heading_text, 1)
        self.import_button = QPushButton("Importar carteira")
        self.import_button.setObjectName("primaryButton")
        self.import_button.setAccessibleName("Importar arquivo de carteira")
        heading.addWidget(self.import_button)
        root.addLayout(heading)

        self.source_label = QLabel("Nenhuma carteira carregada")
        self.source_label.setObjectName("mutedLabel")
        self.source_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self.source_label)

        self.error_banner = QLabel()
        self.error_banner.setObjectName("errorBanner")
        self.error_banner.setWordWrap(True)
        self.error_banner.hide()
        root.addWidget(self.error_banner)

        cards = QHBoxLayout()
        cards.setSpacing(10)
        total_card, self.total_value = _summary_card("LINHAS")
        accepted_card, self.accepted_value = _summary_card("ACEITAS")
        warning_card, self.warning_value = _summary_card("AVISOS")
        error_card, self.error_value = _summary_card("ERROS")
        for card in (total_card, accepted_card, warning_card, error_card):
            cards.addWidget(card)
        root.addLayout(cards)

        positions_group = QGroupBox("Posições aceitas")
        positions_layout = QVBoxLayout(positions_group)
        self.positions_table = QTableView()
        self.positions_table.setObjectName("positionsTable")
        self.positions_table.setModel(self.position_model)
        self.positions_table.setAlternatingRowColors(True)
        self.positions_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.positions_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.positions_table.verticalHeader().hide()
        position_header = self.positions_table.horizontalHeader()
        position_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        position_header.setStretchLastSection(True)
        positions_layout.addWidget(self.positions_table)
        root.addWidget(positions_group, 3)

        issues_group = QGroupBox("Problemas de validação")
        issues_layout = QVBoxLayout(issues_group)
        self.issue_count_label = QLabel("Nenhum problema registrado")
        self.issue_count_label.setObjectName("mutedLabel")
        issues_layout.addWidget(self.issue_count_label)
        self.issues_table = QTableView()
        self.issues_table.setObjectName("issuesTable")
        self.issues_table.setModel(self.issue_model)
        self.issues_table.setAlternatingRowColors(True)
        self.issues_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.issues_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.issues_table.verticalHeader().hide()
        issue_header = self.issues_table.horizontalHeader()
        issue_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        issue_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        issues_layout.addWidget(self.issues_table)
        root.addWidget(issues_group, 2)

    def set_result(self, result: ImportResult) -> None:
        """Render one immutable import result."""

        self.position_model.set_positions(result.positions)
        self.issue_model.set_issues(result.located_issues)
        self.source_label.setText(result.source_name)
        self.source_label.setToolTip(result.source_name)
        self.total_value.setText(str(result.summary.total_rows))
        self.accepted_value.setText(str(result.summary.accepted_rows))
        self.warning_value.setText(str(result.summary.warning_rows))
        self.error_value.setText(str(result.summary.error_rows))
        issue_count = len(result.located_issues)
        self.issue_count_label.setText(
            "Nenhum problema registrado"
            if issue_count == 0
            else f"{issue_count} problema(s) com código preservado"
        )
        self.error_banner.hide()

    def show_error(self, code: str, message: str) -> None:
        """Show a non-modal structured failure."""

        self.error_banner.setText(f"{code} — {message}")
        self.error_banner.show()


def _summary_card(title: str) -> tuple[QFrame, QLabel]:
    card = QFrame()
    card.setObjectName("summaryCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 10, 14, 10)
    title_label = QLabel(title)
    title_label.setObjectName("summaryTitle")
    value_label = QLabel("0")
    value_label.setObjectName("summaryValue")
    layout.addWidget(title_label)
    layout.addWidget(value_label)
    return card, value_label
