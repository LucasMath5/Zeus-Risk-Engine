"""Main window coordinating the first reviewable desktop workflow."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from zeus_risk import __version__
from zeus_risk.app.views import PortfolioPage, RiskPage
from zeus_risk.application import PortfolioRiskWorkflow, ProjectWorkflow
from zeus_risk.domain import (
    DesktopProject,
    DomainValidationError,
    Portfolio,
    ReturnMethod,
    ValidationIssue,
)
from zeus_risk.exceptions import (
    AnalyticsError,
    MarketDataError,
    PortfolioImportError,
    ProjectFileError,
    RiskCalculationError,
)
from zeus_risk.importers import ImportResult


class MainWindow(QMainWindow):
    """Connect Qt interactions to application services and immutable results."""

    def __init__(
        self,
        workflow: PortfolioRiskWorkflow | None = None,
        project_workflow: ProjectWorkflow | None = None,
    ) -> None:
        super().__init__()
        self._workflow = workflow or PortfolioRiskWorkflow()
        self._project_workflow = project_workflow or ProjectWorkflow()
        self._import_result: ImportResult | None = None
        self._market_data_path: Path | None = None
        self._project_path: Path | None = None
        self._project_name = "Projeto sem título"
        self._return_method = ReturnMethod.SIMPLE
        self._dirty = False
        self._restoring_project = False

        self.setObjectName("mainWindow")
        self._update_window_title()
        self.setMinimumSize(940, 700)
        self.resize(1180, 820)
        self._build_actions()
        self._build_content()
        self._connect_signals()
        self.statusBar().showMessage(
            f"Zeus Risk Engine {__version__} · cálculo local · uso educacional"
        )

    @property
    def import_result(self) -> ImportResult | None:
        """Return the latest reviewable import result."""

        return self._import_result

    @property
    def market_data_path(self) -> Path | None:
        """Return the selected local market-data path."""

        return self._market_data_path

    @property
    def project_path(self) -> Path | None:
        """Return the current project-file destination, when saved or opened."""

        return self._project_path

    @property
    def is_dirty(self) -> bool:
        """Return whether current restorable state differs from the last save."""

        return self._dirty

    def load_portfolio(
        self,
        path: str | Path,
        *,
        worksheet_name: str | None = None,
    ) -> bool:
        """Load a portfolio and return whether it is ready for risk analysis."""

        try:
            result = self._workflow.import_portfolio(
                path,
                worksheet_name=worksheet_name,
            )
        except PortfolioImportError as error:
            self.portfolio_page.show_error(error.issue.code, error.issue.message)
            self.risk_page.set_portfolio_ready(self._ready_portfolio() is not None)
            self.statusBar().showMessage("Falha ao importar a carteira")
            return False

        ready = self._apply_import_result(result)
        if not self._restoring_project:
            if self._project_path is None:
                self._project_name = Path(result.source_name).stem
            self._mark_dirty()
        if ready:
            self.statusBar().showMessage(
                f"Carteira carregada: {result.summary.accepted_rows} posição(ões)"
            )
        else:
            self.statusBar().showMessage("Carteira carregada com erros para revisão")
        return ready

    def set_market_data_path(self, path: str | Path) -> None:
        """Select one local CSV source without loading it eagerly."""

        self._market_data_path = Path(path)
        self.risk_page.set_market_data_path(str(self._market_data_path))
        self._mark_dirty()
        self.statusBar().showMessage("Fonte local de preços selecionada")

    def run_analysis(self) -> bool:
        """Execute the bounded synchronous application workflow."""

        portfolio = self._ready_portfolio()
        if portfolio is None or self._market_data_path is None:
            self.risk_page.show_error(
                "WORKFLOW_NOT_READY",
                "Importe uma carteira válida e selecione o CSV local de preços.",
            )
            return False

        self.risk_page.set_running(True)
        self.statusBar().showMessage("Executando análise histórica…")
        try:
            analysis = self._workflow.run_historical_risk(
                portfolio,
                self._market_data_path,
                self.risk_page.configuration(),
                return_method=self._return_method,
            )
        except DomainValidationError as error:
            self._show_risk_issue(error.primary_issue)
            return False
        except MarketDataError as error:
            self._show_risk_issue(error.primary_issue.issue)
            return False
        except AnalyticsError as error:
            self._show_risk_issue(error.primary_issue)
            return False
        except RiskCalculationError as error:
            self._show_risk_issue(error.primary_issue)
            return False
        finally:
            self.risk_page.set_running(False)

        self.risk_page.show_analysis(analysis)
        self.tabs.setCurrentWidget(self.risk_page)
        self.statusBar().showMessage("Análise histórica concluída")
        return True

    def save_project(self, path: str | Path) -> bool:
        """Save the current restorable state to one explicit JSON destination."""

        project = self._create_project_snapshot()
        if project is None:
            return False
        destination = Path(path)
        if destination.suffix.lower() != ".json":
            destination = destination.with_name(f"{destination.name}.zeus.json")
        try:
            saved_path = self._project_workflow.save_project(project, destination)
        except ProjectFileError as error:
            self._show_project_issue(error.primary_issue)
            return False

        self._project_path = saved_path
        self._project_name = project.name
        self._set_dirty(False)
        self.project_banner.hide()
        self.statusBar().showMessage(f"Projeto salvo: {saved_path}")
        return True

    def open_project(self, path: str | Path) -> bool:
        """Validate and restore one project without partially replacing current state."""

        try:
            project = self._project_workflow.load_project(path)
        except ProjectFileError as error:
            self._show_project_issue(error.primary_issue)
            return False
        if not self.risk_page.supports_configuration(project.risk_configuration):
            self._show_project_error(
                "PROJECT_CONFIGURATION_NOT_REPRESENTABLE",
                "A configuração do projeto excede os limites dos controles desta versão.",
            )
            return False
        try:
            result = self._workflow.import_portfolio(
                project.portfolio_path,
                worksheet_name=project.worksheet_name,
            )
        except PortfolioImportError as error:
            self._show_project_issue(error.issue)
            return False
        if result.portfolio is None or result.has_errors:
            first_code = next(
                (item.issue.code for item in result.located_issues),
                "UNKNOWN_VALIDATION_ERROR",
            )
            self._show_project_error(
                "PROJECT_PORTFOLIO_INVALID",
                f"A carteira referenciada agora possui erros de validação ({first_code}).",
            )
            return False

        self._restoring_project = True
        try:
            self._apply_import_result(result)
            self._market_data_path = project.market_data_path
            self.risk_page.set_market_data_path(str(project.market_data_path))
            self.risk_page.set_configuration(project.risk_configuration)
            self._return_method = project.return_method
        finally:
            self._restoring_project = False
        self._project_path = Path(path).resolve()
        self._project_name = project.name
        self._set_dirty(False)
        self.project_banner.hide()
        self.tabs.setCurrentWidget(self.risk_page)
        self.statusBar().showMessage(f"Projeto aberto: {self._project_path}")
        return True

    def closeEvent(self, event: QCloseEvent) -> None:
        """Accept normal close requests without hidden background work."""

        event.accept()

    def _build_actions(self) -> None:
        self.open_project_action = QAction("Abrir projeto…", self)
        self.open_project_action.setShortcut(QKeySequence.StandardKey.Open)
        self.save_project_action = QAction("Salvar projeto", self)
        self.save_project_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_project_as_action = QAction("Salvar projeto como…", self)
        self.save_project_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.import_action = QAction("Importar carteira…", self)
        self.import_action.setShortcut(QKeySequence("Ctrl+I"))
        self.market_data_action = QAction("Selecionar preços…", self)
        self.exit_action = QAction("Sair", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.about_action = QAction("Sobre o Zeus Risk Engine", self)

        file_menu = self.menuBar().addMenu("Arquivo")
        file_menu.addAction(self.open_project_action)
        file_menu.addAction(self.save_project_action)
        file_menu.addAction(self.save_project_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.import_action)
        file_menu.addAction(self.market_data_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        help_menu = self.menuBar().addMenu("Ajuda")
        help_menu.addAction(self.about_action)

    def _build_content(self) -> None:
        root = QWidget()
        root.setObjectName("applicationRoot")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("heroPanel")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(22, 17, 22, 17)
        mark = QLabel("Z")
        mark.setObjectName("brandMark")
        mark.setAccessibleName("Zeus")
        hero_layout.addWidget(mark)
        heading = QVBoxLayout()
        title = QLabel("Zeus Risk Engine")
        title.setObjectName("heroTitle")
        subtitle = QLabel(
            "Carteiras auditáveis, dados locais e risco histórico com parâmetros explícitos."
        )
        subtitle.setObjectName("heroSubtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        hero_layout.addLayout(heading, 1)
        phase = QLabel("FASE 10 · PROJETOS")
        phase.setObjectName("heroSubtitle")
        hero_layout.addWidget(phase, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(hero)

        self.project_banner = QLabel()
        self.project_banner.setObjectName("errorBanner")
        self.project_banner.setWordWrap(True)
        self.project_banner.hide()
        layout.addWidget(self.project_banner)

        self.portfolio_page = PortfolioPage()
        self.risk_page = RiskPage()
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self.portfolio_page, "1  Carteira")
        self.tabs.addTab(self.risk_page, "2  Risco histórico")
        layout.addWidget(self.tabs, 1)
        self.setCentralWidget(root)

    def _connect_signals(self) -> None:
        self.portfolio_page.import_button.clicked.connect(self._choose_portfolio)
        self.risk_page.market_data_button.clicked.connect(self._choose_market_data)
        self.risk_page.run_button.clicked.connect(self.run_analysis)
        self.import_action.triggered.connect(self._choose_portfolio)
        self.open_project_action.triggered.connect(self._choose_open_project)
        self.save_project_action.triggered.connect(self._save_current_project)
        self.save_project_as_action.triggered.connect(self._choose_save_project)
        self.market_data_action.triggered.connect(self._choose_market_data)
        self.exit_action.triggered.connect(self.close)
        self.about_action.triggered.connect(self._show_about)
        self.risk_page.confidence_spin.valueChanged.connect(self._mark_dirty)
        self.risk_page.horizon_spin.valueChanged.connect(self._mark_dirty)
        self.risk_page.window_spin.valueChanged.connect(self._mark_dirty)
        self._update_project_actions()

    def _choose_open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir projeto Zeus",
            "",
            "Projeto Zeus (*.zeus.json *.json)",
        )
        if path:
            self.open_project(path)

    def _save_current_project(self) -> None:
        if self._project_path is None:
            self._choose_save_project()
        else:
            self.save_project(self._project_path)

    def _choose_save_project(self) -> None:
        initial = str(self._project_path or Path("project.zeus.json"))
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar projeto Zeus",
            initial,
            "Projeto Zeus (*.zeus.json)",
        )
        if path:
            self.save_project(path)

    def _choose_portfolio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar carteira",
            "",
            "Carteiras (*.csv *.xlsx);;CSV (*.csv);;Excel (*.xlsx)",
        )
        if not path:
            return

        try:
            worksheets = self._workflow.list_worksheets(path)
        except PortfolioImportError as error:
            self.portfolio_page.show_error(error.issue.code, error.issue.message)
            return

        worksheet_name: str | None = None
        if len(worksheets) == 1:
            worksheet_name = worksheets[0]
        elif len(worksheets) > 1:
            worksheet_name, accepted = QInputDialog.getItem(
                self,
                "Selecionar planilha",
                "Planilha da carteira:",
                worksheets,
                editable=False,
            )
            if not accepted:
                return
        self.load_portfolio(path, worksheet_name=worksheet_name)

    def _choose_market_data(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar preços locais",
            "",
            "Preços em CSV (*.csv)",
        )
        if path:
            self.set_market_data_path(path)

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "Sobre o Zeus Risk Engine",
            f"Zeus Risk Engine {__version__}\n\n"
            "Motor de risco modular, educacional e auditável. "
            "Os resultados não constituem recomendação financeira.",
        )

    def _ready_portfolio(self) -> Portfolio | None:
        result = self._import_result
        if result is None or result.has_errors:
            return None
        return result.portfolio

    def _apply_import_result(self, result: ImportResult) -> bool:
        self._import_result = result
        self.portfolio_page.set_result(result)
        ready = result.portfolio is not None and not result.has_errors
        self.risk_page.set_portfolio_ready(ready)
        self.tabs.setCurrentWidget(self.portfolio_page)
        self._update_project_actions()
        return ready

    def _create_project_snapshot(self) -> DesktopProject | None:
        result = self._import_result
        if (
            result is None
            or result.portfolio is None
            or result.has_errors
            or self._market_data_path is None
        ):
            self._show_project_error(
                "PROJECT_NOT_READY",
                "Importe uma carteira válida e selecione os preços antes de salvar.",
            )
            return None
        try:
            return self._project_workflow.create_project(
                name=self._project_name,
                portfolio_path=result.source_name,
                market_data_path=self._market_data_path,
                risk_configuration=self.risk_page.configuration(),
                worksheet_name=result.worksheet_name,
                return_method=self._return_method,
            )
        except DomainValidationError as error:
            self._show_project_issue(error.primary_issue)
            return None

    def _mark_dirty(self, *_: object) -> None:
        if self._restoring_project:
            return
        self._set_dirty(True)

    def _set_dirty(self, dirty: bool) -> None:
        self._dirty = dirty
        self._update_window_title()
        self._update_project_actions()

    def _update_window_title(self) -> None:
        dirty_marker = " *" if self._dirty else ""
        self.setWindowTitle(f"Zeus Risk Engine — {self._project_name}{dirty_marker}")

    def _update_project_actions(self) -> None:
        if not hasattr(self, "save_project_action"):
            return
        can_save = self._ready_portfolio() is not None and self._market_data_path is not None
        self.save_project_as_action.setEnabled(can_save)
        self.save_project_action.setEnabled(can_save and self._project_path is not None)

    def _show_project_issue(self, issue: ValidationIssue) -> None:
        self._show_project_error(issue.code, issue.message)

    def _show_project_error(self, code: str, message: str) -> None:
        self.project_banner.setText(f"{code} — {message}")
        self.project_banner.show()
        self.statusBar().showMessage(f"Operação de projeto interrompida: {code}")

    def _show_risk_issue(self, issue: ValidationIssue) -> None:
        self.risk_page.show_error(issue.code, issue.message)
        self.tabs.setCurrentWidget(self.risk_page)
        self.statusBar().showMessage(f"Análise interrompida: {issue.code}")
