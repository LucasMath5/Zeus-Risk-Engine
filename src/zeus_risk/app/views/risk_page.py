"""Historical-risk configuration and results page."""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from zeus_risk.application import HistoricalRiskAnalysis
from zeus_risk.domain import HistoricalVaRConfiguration


class RiskPage(QWidget):
    """Collect explicit historical-risk parameters and present structured results."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("riskPage")
        self._portfolio_ready = False
        self._market_data_ready = False
        self._running = False

        root = QVBoxLayout(self)
        root.setContentsMargins(2, 8, 2, 8)
        root.setSpacing(14)

        title = QLabel("Risco histórico")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Configure a amostra e execute VaR e Expected Shortfall sobre preços locais."
        )
        subtitle.setObjectName("pageSubtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        setup_group = QGroupBox("Dados e parâmetros")
        setup_layout = QVBoxLayout(setup_group)
        source_row = QHBoxLayout()
        source_row.addWidget(QLabel("Preços locais:"))
        self.market_data_label = QLabel("Nenhum arquivo selecionado")
        self.market_data_label.setObjectName("mutedLabel")
        self.market_data_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        source_row.addWidget(self.market_data_label, 1)
        self.market_data_button = QPushButton("Selecionar preços")
        self.market_data_button.setAccessibleName("Selecionar arquivo CSV de preços")
        source_row.addWidget(self.market_data_button)
        setup_layout.addLayout(source_row)

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setObjectName("confidenceInput")
        self.confidence_spin.setRange(50.0, 99.9)
        self.confidence_spin.setDecimals(1)
        self.confidence_spin.setSingleStep(0.5)
        self.confidence_spin.setValue(95.0)
        self.confidence_spin.setSuffix(" %")
        self.horizon_spin = QSpinBox()
        self.horizon_spin.setObjectName("horizonInput")
        self.horizon_spin.setRange(1, 60)
        self.horizon_spin.setValue(1)
        self.horizon_spin.setSuffix(" dia(s)")
        self.window_spin = QSpinBox()
        self.window_spin.setObjectName("windowInput")
        self.window_spin.setRange(2, 10_000)
        self.window_spin.setValue(252)
        self.window_spin.setSuffix(" cenários")
        form.addRow("Confiança", self.confidence_spin)
        form.addRow("Horizonte", self.horizon_spin)
        form.addRow("Janela", self.window_spin)
        setup_layout.addLayout(form)

        action_row = QHBoxLayout()
        self.readiness_label = QLabel("Importe uma carteira válida para continuar.")
        self.readiness_label.setObjectName("mutedLabel")
        self.readiness_label.setWordWrap(True)
        action_row.addWidget(self.readiness_label, 1)
        self.run_button = QPushButton("Executar análise")
        self.run_button.setObjectName("primaryButton")
        self.run_button.setAccessibleName("Executar VaR e Expected Shortfall")
        self.run_button.setEnabled(False)
        action_row.addWidget(self.run_button)
        setup_layout.addLayout(action_row)
        root.addWidget(setup_group)

        self.error_banner = QLabel()
        self.error_banner.setObjectName("errorBanner")
        self.error_banner.setWordWrap(True)
        self.error_banner.hide()
        root.addWidget(self.error_banner)

        self.success_banner = QLabel()
        self.success_banner.setObjectName("successBanner")
        self.success_banner.setWordWrap(True)
        self.success_banner.hide()
        root.addWidget(self.success_banner)

        metrics = QHBoxLayout()
        var_card, self.var_value = _metric_card("VALUE AT RISK")
        es_card, self.es_value = _metric_card("EXPECTED SHORTFALL")
        metrics.addWidget(var_card)
        metrics.addWidget(es_card)
        root.addLayout(metrics)

        details_group = QGroupBox("Evidência do resultado")
        details = QFormLayout(details_group)
        self.method_value = QLabel("—")
        self.configuration_value = QLabel("—")
        self.sample_value = QLabel("—")
        self.tail_value = QLabel("—")
        self.reference_value = QLabel("—")
        for label in (
            self.method_value,
            self.configuration_value,
            self.sample_value,
            self.tail_value,
            self.reference_value,
        ):
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        details.addRow("Método e unidade", self.method_value)
        details.addRow("Configuração", self.configuration_value)
        details.addRow("Amostra do VaR", self.sample_value)
        details.addRow("Cauda do ES", self.tail_value)
        details.addRow("Data de referência", self.reference_value)
        root.addWidget(details_group)
        root.addStretch(1)

    def configuration(self) -> HistoricalVaRConfiguration:
        """Build the validated domain configuration represented by the controls."""

        confidence = Decimal(str(self.confidence_spin.value())) / Decimal("100")
        return HistoricalVaRConfiguration(
            confidence_level=confidence,
            horizon_days=self.horizon_spin.value(),
            window=self.window_spin.value(),
        )

    def supports_configuration(self, configuration: HistoricalVaRConfiguration) -> bool:
        """Return whether the current controls can preserve a configuration exactly."""

        if not isinstance(configuration, HistoricalVaRConfiguration):
            raise TypeError("configuration must be a HistoricalVaRConfiguration")
        confidence_percentage = configuration.confidence_level * Decimal("100")
        displayed_confidence = Decimal(
            f"{confidence_percentage:.{self.confidence_spin.decimals()}f}"
        )
        return (
            Decimal(str(self.confidence_spin.minimum()))
            <= confidence_percentage
            <= Decimal(str(self.confidence_spin.maximum()))
            and confidence_percentage == displayed_confidence
            and self.horizon_spin.minimum()
            <= configuration.horizon_days
            <= self.horizon_spin.maximum()
            and self.window_spin.minimum() <= configuration.window <= self.window_spin.maximum()
        )

    def set_configuration(self, configuration: HistoricalVaRConfiguration) -> None:
        """Restore an exactly representable domain configuration into the controls."""

        if not self.supports_configuration(configuration):
            raise ValueError("risk configuration cannot be represented by the controls")
        confidence_percentage = configuration.confidence_level * Decimal("100")
        self.confidence_spin.setValue(float(confidence_percentage))
        self.horizon_spin.setValue(configuration.horizon_days)
        self.window_spin.setValue(configuration.window)

    def set_portfolio_ready(self, ready: bool) -> None:
        """Record whether a complete validated portfolio can be analyzed."""

        self._portfolio_ready = ready
        self._update_readiness()

    def set_market_data_path(self, path: str) -> None:
        """Present the selected local-price source."""

        self._market_data_ready = bool(path)
        self.market_data_label.setText(path or "Nenhum arquivo selecionado")
        self.market_data_label.setToolTip(path)
        self._update_readiness()

    def set_running(self, running: bool) -> None:
        """Prevent repeated synchronous execution while one call is active."""

        self._running = running
        self.run_button.setText("Executando…" if running else "Executar análise")
        self._update_readiness()

    def show_analysis(self, analysis: HistoricalRiskAnalysis) -> None:
        """Render VaR, ES, parameters, samples, and dates without recalculating them."""

        historical_var = analysis.historical_var
        expected_shortfall = analysis.expected_shortfall
        configuration = historical_var.configuration
        self.var_value.setText(_format_relative(historical_var.value_at_risk))
        self.es_value.setText(_format_relative(expected_shortfall.expected_shortfall))
        self.method_value.setText(
            f"{historical_var.return_method.value} · {historical_var.unit.value}"
        )
        self.configuration_value.setText(
            f"{configuration.confidence_level * Decimal('100')}% · "
            f"{configuration.horizon_days} dia(s) · janela {configuration.window}"
        )
        self.sample_value.setText(
            f"{historical_var.observation_count} cenários · "
            f"{historical_var.sample_start_date.isoformat()} a "
            f"{historical_var.sample_end_date.isoformat()}"
        )
        self.tail_value.setText(
            f"{expected_shortfall.tail_count} cenário(s) · média bruta "
            f"{_format_relative(expected_shortfall.tail_mean_loss)}"
        )
        self.reference_value.setText(historical_var.reference_date.isoformat())
        self.error_banner.hide()
        self.success_banner.setText(
            "Análise concluída com a configuração e as amostras exibidas abaixo."
        )
        self.success_banner.show()

    def show_error(self, code: str, message: str) -> None:
        """Show a non-modal structured failure while retaining the last inputs."""

        self.success_banner.hide()
        self.error_banner.setText(f"{code} — {message}")
        self.error_banner.show()

    def _update_readiness(self) -> None:
        can_run = self._portfolio_ready and self._market_data_ready and not self._running
        self.run_button.setEnabled(can_run)
        if self._running:
            message = "Executando o pipeline local síncrono."
        elif not self._portfolio_ready:
            message = "Importe uma carteira sem erros para continuar."
        elif not self._market_data_ready:
            message = "Selecione o CSV local de preços para continuar."
        else:
            message = "Pronto para executar com os parâmetros informados."
        self.readiness_label.setText(message)


def _metric_card(title: str) -> tuple[QFrame, QLabel]:
    card = QFrame()
    card.setObjectName("metricCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 15, 18, 15)
    title_label = QLabel(title)
    title_label.setObjectName("metricTitle")
    value_label = QLabel("—")
    value_label.setObjectName("metricValue")
    layout.addWidget(title_label)
    layout.addWidget(value_label)
    return card, value_label


def _format_relative(value: Decimal) -> str:
    percentage = value * Decimal("100")
    return f"{percentage:.4f}%"
