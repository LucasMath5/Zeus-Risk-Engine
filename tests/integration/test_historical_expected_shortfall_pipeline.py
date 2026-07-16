"""Integration test for local portfolio prices through historical ES."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from zeus_risk.core.analytics import calculate_portfolio_return_series, calculate_return_table
from zeus_risk.core.risk import calculate_historical_expected_shortfall
from zeus_risk.domain import (
    AssetClass,
    Currency,
    HistoricalVaRConfiguration,
    Instrument,
    Portfolio,
    Position,
    ReturnMethod,
)
from zeus_risk.market_data import AlignmentPolicy, CsvMarketDataProvider, align_price_series

PROJECT_ROOT = Path(__file__).parents[2]


def test_local_market_data_flows_into_historical_portfolio_expected_shortfall() -> None:
    market_data = CsvMarketDataProvider(
        PROJECT_ROOT / "tests" / "fixtures" / "market_data" / "valid_prices.csv"
    ).load()
    prices = align_price_series(market_data.data.series, AlignmentPolicy.INTERSECTION)
    returns = calculate_return_table(prices, ReturnMethod.SIMPLE)
    portfolio = Portfolio(
        "Synthetic Portfolio",
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
    portfolio_returns = calculate_portfolio_return_series(returns, portfolio)

    result = calculate_historical_expected_shortfall(
        portfolio_returns,
        HistoricalVaRConfiguration(Decimal("0.5"), window=2),
    )

    assert result.historical_var.key.ticker == "SYNTHETIC PORTFOLIO"
    assert result.historical_var.reference_date == market_data.data.metadata.end_date
    assert result.tail_count == 1
    assert result.expected_shortfall > Decimal("0")
    assert result.expected_shortfall >= result.historical_var.value_at_risk
