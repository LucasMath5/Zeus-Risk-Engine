"""Synchronous first-use workflow for portfolio import and historical risk."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Never

from zeus_risk.core.analytics import (
    calculate_portfolio_return_series,
    calculate_return_table,
)
from zeus_risk.core.risk import calculate_historical_expected_shortfall
from zeus_risk.domain import (
    HistoricalExpectedShortfallResult,
    HistoricalVaRConfiguration,
    HistoricalVaRResult,
    Portfolio,
    ReturnMethod,
    ReturnSeries,
    ValidationIssue,
    ValidationSeverity,
)
from zeus_risk.domain.market_data import MarketDataLoadResult
from zeus_risk.exceptions import PortfolioImportError
from zeus_risk.importers import (
    CsvPortfolioImporter,
    ImportResult,
    XlsxPortfolioImporter,
)
from zeus_risk.market_data import (
    AlignmentPolicy,
    CsvMarketDataProvider,
    align_price_series,
)


@dataclass(frozen=True, slots=True)
class HistoricalRiskAnalysis:
    """Complete application result displayed by the first desktop workflow."""

    market_data: MarketDataLoadResult
    portfolio_returns: ReturnSeries
    expected_shortfall: HistoricalExpectedShortfallResult

    def __post_init__(self) -> None:
        if not isinstance(self.market_data, MarketDataLoadResult):
            raise TypeError("market_data must be a MarketDataLoadResult")
        if not isinstance(self.portfolio_returns, ReturnSeries):
            raise TypeError("portfolio_returns must be a ReturnSeries")
        if not isinstance(self.expected_shortfall, HistoricalExpectedShortfallResult):
            raise TypeError("expected_shortfall must be a HistoricalExpectedShortfallResult")
        historical_var = self.expected_shortfall.historical_var
        if (
            historical_var.key != self.portfolio_returns.key
            or historical_var.reference_date != self.portfolio_returns.end_date
            or historical_var.return_method is not self.portfolio_returns.method
        ):
            raise ValueError("risk result must reconcile with the portfolio return series")

    @property
    def historical_var(self) -> HistoricalVaRResult:
        """Return the VaR result associated with Expected Shortfall."""

        return self.expected_shortfall.historical_var


class PortfolioRiskWorkflow:
    """Coordinate existing import, market-data, analytics, and risk boundaries."""

    def __init__(self) -> None:
        self._csv_importer = CsvPortfolioImporter()
        self._xlsx_importer = XlsxPortfolioImporter()

    def list_worksheets(self, path: str | Path) -> tuple[str, ...]:
        """List XLSX worksheets or return an empty tuple for CSV."""

        source = Path(path)
        suffix = source.suffix.lower()
        if suffix == ".xlsx":
            return self._xlsx_importer.list_worksheets(source)
        if suffix == ".csv":
            return ()
        _raise_unsupported_portfolio_type(source)

    def import_portfolio(
        self,
        path: str | Path,
        *,
        worksheet_name: str | None = None,
    ) -> ImportResult:
        """Import one supported portfolio file through its validated adapter."""

        source = Path(path)
        suffix = source.suffix.lower()
        if suffix == ".csv":
            return self._csv_importer.import_file(source)
        if suffix == ".xlsx":
            return self._xlsx_importer.import_file(
                source,
                worksheet_name=worksheet_name,
            )
        _raise_unsupported_portfolio_type(source)

    def run_historical_risk(
        self,
        portfolio: Portfolio,
        market_data_path: str | Path,
        configuration: HistoricalVaRConfiguration,
        *,
        return_method: ReturnMethod = ReturnMethod.SIMPLE,
    ) -> HistoricalRiskAnalysis:
        """Run the local-price pipeline through portfolio VaR and Expected Shortfall."""

        if not isinstance(portfolio, Portfolio):
            raise TypeError("portfolio must be a Portfolio")
        if not isinstance(configuration, HistoricalVaRConfiguration):
            raise TypeError("configuration must be a HistoricalVaRConfiguration")
        if not isinstance(return_method, ReturnMethod):
            raise TypeError("return_method must be a ReturnMethod")

        market_data = CsvMarketDataProvider(market_data_path).load()
        prices = align_price_series(
            market_data.data.series,
            AlignmentPolicy.INTERSECTION,
        )
        returns = calculate_return_table(prices, return_method)
        portfolio_returns = calculate_portfolio_return_series(returns, portfolio)
        expected_shortfall = calculate_historical_expected_shortfall(
            portfolio_returns,
            configuration,
        )
        return HistoricalRiskAnalysis(
            market_data=market_data,
            portfolio_returns=portfolio_returns,
            expected_shortfall=expected_shortfall,
        )


def _raise_unsupported_portfolio_type(source: Path) -> Never:
    raise PortfolioImportError(
        ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code="UNSUPPORTED_PORTFOLIO_FILE_TYPE",
            message="Portfolio file must use CSV or XLSX format.",
            field="path",
            item=source.suffix or None,
        ),
        source_name=str(source),
    )
