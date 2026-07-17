"""Unit and local integration tests for the first desktop application workflow."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest

from zeus_risk.application import PortfolioRiskWorkflow
from zeus_risk.domain import (
    AssetClass,
    Currency,
    HistoricalVaRConfiguration,
    Instrument,
    Portfolio,
    Position,
    ReturnMethod,
)
from zeus_risk.exceptions import PortfolioImportError

PROJECT_ROOT = Path(__file__).parents[3]


def _portfolio() -> Portfolio:
    return Portfolio(
        "Desktop Portfolio",
        (
            Position(
                Instrument("ZEUS_EQ1", AssetClass.EQUITY, Currency("BRL")),
                Decimal("1"),
                Decimal("100"),
            ),
            Position(
                Instrument("ZEUS_EQ2", AssetClass.EQUITY, Currency("BRL")),
                Decimal("2"),
                Decimal("50"),
            ),
        ),
    )


def test_imports_csv_portfolio_and_identifies_non_xlsx_worksheet_list() -> None:
    workflow = PortfolioRiskWorkflow()
    path = PROJECT_ROOT / "tests" / "fixtures" / "portfolios" / "valid_portfolio.csv"

    result = workflow.import_portfolio(path)

    assert result.portfolio is not None
    assert result.summary.accepted_rows == 2
    assert workflow.list_worksheets(path) == ()


def test_rejects_unsupported_portfolio_extension_with_structured_code() -> None:
    workflow = PortfolioRiskWorkflow()

    with pytest.raises(PortfolioImportError) as exc_info:
        workflow.import_portfolio("portfolio.json")

    assert exc_info.value.issue.code == "UNSUPPORTED_PORTFOLIO_FILE_TYPE"


def test_runs_complete_local_historical_risk_workflow() -> None:
    workflow = PortfolioRiskWorkflow()
    market_data_path = PROJECT_ROOT / "tests" / "fixtures" / "market_data" / "valid_prices.csv"
    configuration = HistoricalVaRConfiguration(Decimal("0.5"), window=2)

    result = workflow.run_historical_risk(
        _portfolio(),
        market_data_path,
        configuration,
    )

    assert result.market_data.data.metadata.source_name == str(market_data_path)
    assert result.portfolio_returns.key.ticker == "DESKTOP PORTFOLIO"
    assert result.historical_var.configuration is configuration
    assert result.historical_var.value_at_risk == Decimal("0")
    assert result.expected_shortfall.expected_shortfall > Decimal("0")


def test_rejects_invalid_workflow_boundary_types() -> None:
    workflow = PortfolioRiskWorkflow()
    configuration = HistoricalVaRConfiguration(Decimal("0.5"), window=2)

    with pytest.raises(TypeError, match="portfolio"):
        workflow.run_historical_risk(
            cast(Portfolio, object()),
            "prices.csv",
            configuration,
        )
    with pytest.raises(TypeError, match="return_method"):
        workflow.run_historical_risk(
            _portfolio(),
            "prices.csv",
            configuration,
            return_method=cast(ReturnMethod, "simple"),
        )
