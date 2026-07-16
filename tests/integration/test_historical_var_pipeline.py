"""Integration test for local portfolio prices through historical VaR."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from zeus_risk.core.analytics import calculate_portfolio_return_series, calculate_return_table
from zeus_risk.core.risk import calculate_historical_var
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


def test_local_market_data_flows_into_historical_portfolio_var() -> None:
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

    result = calculate_historical_var(
        portfolio_returns,
        HistoricalVaRConfiguration(Decimal("0.5"), window=2),
    )

    assert result.key.ticker == "SYNTHETIC PORTFOLIO"
    assert result.observation_count == 2
    assert result.quantile_rank == 1
    assert result.reference_date == market_data.data.metadata.end_date
    assert result.value_at_risk == Decimal("0")
