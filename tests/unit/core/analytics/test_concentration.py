"""Unit tests for gross-weight Herfindahl concentration."""

from __future__ import annotations

from decimal import Decimal
from typing import cast

import pytest

from zeus_risk.core.analytics import calculate_position_concentration
from zeus_risk.domain import AssetClass, Currency, Instrument, Portfolio, Position
from zeus_risk.exceptions import AnalyticsError


def _position(
    ticker: str,
    quantity: str,
    price: str,
    currency: str = "BRL",
) -> Position:
    return Position(
        Instrument(ticker, AssetClass.EQUITY, Currency(currency)),
        Decimal(quantity),
        Decimal(price),
    )


def test_equal_four_position_portfolio_has_hhi_one_quarter() -> None:
    portfolio = Portfolio(
        "Equal",
        tuple(_position(f"A{index}", "1", "100") for index in range(4)),
    )

    result = calculate_position_concentration(portfolio)

    assert result.herfindahl_index == Decimal("0.25")
    assert result.effective_positions == Decimal("4")


def test_long_short_concentration_uses_gross_magnitudes() -> None:
    portfolio = Portfolio(
        "Long short",
        (
            _position("LONG", "1", "100"),
            _position("SHORT", "-2", "50"),
        ),
    )

    result = calculate_position_concentration(portfolio)

    assert tuple(item.weight for item in result.weights) == (Decimal("0.5"), Decimal("0.5"))
    assert result.herfindahl_index == Decimal("0.5")
    assert result.effective_positions == Decimal("2")


def test_multi_currency_concentration_requires_explicit_currency() -> None:
    portfolio = Portfolio(
        "Global",
        (
            _position("BRL1", "1", "100", "BRL"),
            _position("USD1", "1", "100", "USD"),
        ),
    )

    with pytest.raises(AnalyticsError) as exc_info:
        calculate_position_concentration(portfolio)
    usd = calculate_position_concentration(portfolio, currency=Currency("USD"))

    assert exc_info.value.primary_issue.code == "CURRENCY_CONVERSION_REQUIRED"
    assert usd.currency == Currency("USD")
    assert usd.herfindahl_index == Decimal("1")


def test_rejects_invalid_portfolio_and_currency_types() -> None:
    portfolio = Portfolio("One", (_position("AAA", "1", "100"),))
    with pytest.raises(AnalyticsError) as portfolio_error:
        calculate_position_concentration(cast(Portfolio, object()))
    with pytest.raises(AnalyticsError) as currency_error:
        calculate_position_concentration(portfolio, currency=cast(Currency, "BRL"))

    assert portfolio_error.value.primary_issue.code == "INVALID_PORTFOLIO"
    assert currency_error.value.primary_issue.code == "INVALID_CONCENTRATION_CURRENCY"
