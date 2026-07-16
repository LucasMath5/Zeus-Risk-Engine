"""Integration test for local prices through descriptive portfolio analytics."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from zeus_risk.core.analytics import (
    calculate_correlation_matrix,
    calculate_covariance_matrix,
    calculate_descriptive_statistics,
    calculate_drawdown,
    calculate_portfolio_return_series,
    calculate_position_concentration,
    calculate_return_table,
)
from zeus_risk.domain import AssetClass, Currency, Instrument, Portfolio, Position, ReturnMethod
from zeus_risk.market_data import AlignmentPolicy, CsvMarketDataProvider, align_price_series

PROJECT_ROOT = Path(__file__).parents[2]


def test_local_market_data_flows_through_basic_portfolio_analytics() -> None:
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
    statistics = calculate_descriptive_statistics(portfolio_returns)
    covariance = calculate_covariance_matrix(returns)
    correlation = calculate_correlation_matrix(returns)
    drawdown = calculate_drawdown(portfolio_returns)
    concentration = calculate_position_concentration(portfolio)

    assert returns.observation_count == 2
    assert portfolio_returns.key.ticker == "SYNTHETIC PORTFOLIO"
    assert statistics.observation_count == 2
    assert covariance.keys == prices.keys
    assert correlation.values[0][0] == Decimal("1")
    assert drawdown.observations[-1].cumulative_return > Decimal("-1")
    assert concentration.herfindahl_index == Decimal("0.5")
    assert concentration.effective_positions == Decimal("2")
