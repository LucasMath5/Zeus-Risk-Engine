"""Tests for portfolio aggregation, currencies, and weight conventions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from typing import cast

import pytest

from zeus_risk.domain import (
    AssetClass,
    Currency,
    DomainValidationError,
    Instrument,
    Portfolio,
    Position,
    WeightBasis,
)


def make_position(
    ticker: str,
    quantity: str,
    price: str,
    currency: str = "BRL",
) -> Position:
    instrument = Instrument(ticker, AssetClass.EQUITY, Currency(currency))
    return Position(instrument, Decimal(quantity), Decimal(price))


def test_portfolio_calculates_net_and_gross_market_value() -> None:
    portfolio = Portfolio(
        " Brazil Equity ",
        (
            make_position("PETR4", "10", "25"),
            make_position("VALE3", "5", "70"),
        ),
        reference_date=date(2026, 7, 13),
    )

    assert portfolio.name == "Brazil Equity"
    assert portfolio.currency == Currency("BRL")
    assert portfolio.market_value == Decimal("600")
    assert portfolio.gross_market_value == Decimal("600")
    assert portfolio.reference_date == date(2026, 7, 13)


def test_portfolio_calculates_net_weights_for_long_positions() -> None:
    portfolio = Portfolio(
        "Long only",
        (
            make_position("PETR4", "10", "25"),
            make_position("VALE3", "5", "70"),
        ),
    )

    weights = portfolio.weights()

    assert weights[0].ticker == "PETR4"
    assert weights[0].market_value == Decimal("250")
    assert weights[0].weight == Decimal("250") / Decimal("600")
    assert weights[1].weight == Decimal("350") / Decimal("600")
    assert abs(sum((item.weight for item in weights), Decimal("0")) - Decimal("1")) < Decimal(
        "1e-26"
    )


def test_long_short_weights_use_explicit_net_and_gross_bases() -> None:
    portfolio = Portfolio(
        "Long short",
        (
            make_position("LONG3", "10", "100"),
            make_position("SHORT3", "-2", "100"),
        ),
    )

    net_weights = portfolio.weights(WeightBasis.NET)
    gross_weights = portfolio.weights(WeightBasis.GROSS)

    assert portfolio.market_value == Decimal("800")
    assert portfolio.gross_market_value == Decimal("1200")
    assert tuple(item.weight for item in net_weights) == (Decimal("1.25"), Decimal("-0.25"))
    assert tuple(item.weight for item in gross_weights) == (
        Decimal("1000") / Decimal("1200"),
        Decimal("200") / Decimal("1200"),
    )
    assert abs(sum((item.weight for item in gross_weights), Decimal("0")) - Decimal("1")) < Decimal(
        "1e-26"
    )


def test_zero_net_portfolio_rejects_net_weights_but_supports_gross_weights() -> None:
    portfolio = Portfolio(
        "Market neutral",
        (
            make_position("LONG3", "1", "100"),
            make_position("SHORT3", "-2", "50"),
        ),
    )

    with pytest.raises(DomainValidationError) as exc_info:
        portfolio.weights(WeightBasis.NET)

    assert exc_info.value.primary_issue.code == "ZERO_NET_MARKET_VALUE"
    assert tuple(item.weight for item in portfolio.weights(WeightBasis.GROSS)) == (
        Decimal("0.5"),
        Decimal("0.5"),
    )


def test_multi_currency_portfolio_returns_separate_valuations() -> None:
    portfolio = Portfolio(
        "Global",
        (
            make_position("PETR4", "10", "25", "BRL"),
            make_position("AAPL", "2", "200", "USD"),
        ),
    )

    valuations = portfolio.valuations()

    assert tuple(item.currency.code for item in valuations) == ("BRL", "USD")
    assert tuple(item.net_market_value for item in valuations) == (
        Decimal("250"),
        Decimal("400"),
    )


def test_multi_currency_portfolio_requires_explicit_currency_for_aggregation() -> None:
    portfolio = Portfolio(
        "Global",
        (
            make_position("PETR4", "10", "25", "BRL"),
            make_position("AAPL", "2", "200", "USD"),
        ),
    )

    with pytest.raises(DomainValidationError) as exc_info:
        _ = portfolio.market_value

    assert exc_info.value.primary_issue.code == "CURRENCY_CONVERSION_REQUIRED"
    assert portfolio.valuation(Currency("USD")).net_market_value == Decimal("400")
    assert portfolio.weights(currency=Currency("USD"))[0].weight == Decimal("1")


def test_portfolio_rejects_duplicate_ticker_and_currency() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        Portfolio(
            "Duplicates",
            (
                make_position(" petr4 ", "10", "25", "brl"),
                make_position("PETR4", "5", "26", "BRL"),
            ),
        )

    assert exc_info.value.primary_issue.code == "DUPLICATE_POSITION"
    assert exc_info.value.primary_issue.item == "PETR4:BRL"


def test_same_ticker_in_different_currencies_is_not_implicitly_merged() -> None:
    portfolio = Portfolio(
        "Different listings",
        (
            make_position("ABC", "1", "10", "BRL"),
            make_position("ABC", "1", "2", "USD"),
        ),
    )

    assert portfolio.currencies == (Currency("BRL"), Currency("USD"))


def test_portfolio_rejects_missing_requested_currency() -> None:
    portfolio = Portfolio("Brazil", (make_position("PETR4", "10", "25"),))

    with pytest.raises(DomainValidationError) as exc_info:
        portfolio.valuation(Currency("USD"))

    assert exc_info.value.primary_issue.code == "CURRENCY_NOT_FOUND"


def test_portfolio_rejects_invalid_currency_filter() -> None:
    portfolio = Portfolio("Brazil", (make_position("PETR4", "10", "25"),))

    with pytest.raises(DomainValidationError) as exc_info:
        portfolio.valuation(cast(Currency, "BRL"))

    assert exc_info.value.primary_issue.code == "INVALID_CURRENCY"


@pytest.mark.parametrize(
    ("name", "positions", "expected_code"),
    [
        ("   ", (make_position("PETR4", "1", "10"),), "EMPTY_PORTFOLIO_NAME"),
        ("Empty", (), "EMPTY_PORTFOLIO"),
    ],
)
def test_portfolio_rejects_invalid_core_fields(
    name: str,
    positions: tuple[Position, ...],
    expected_code: str,
) -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        Portfolio(name, positions)

    assert exc_info.value.primary_issue.code == expected_code


def test_portfolio_requires_immutable_position_tuple() -> None:
    positions = [make_position("PETR4", "1", "10")]

    with pytest.raises(DomainValidationError) as exc_info:
        Portfolio("Mutable input", cast(tuple[Position, ...], positions))

    assert exc_info.value.primary_issue.code == "INVALID_POSITIONS_TYPE"


def test_portfolio_rejects_invalid_name_type_and_position_item() -> None:
    valid_position = make_position("PETR4", "1", "10")
    with pytest.raises(DomainValidationError) as name_error:
        Portfolio(cast(str, 123), (valid_position,))
    with pytest.raises(DomainValidationError) as position_error:
        Portfolio("Invalid item", (cast(Position, object()),))

    assert name_error.value.primary_issue.code == "INVALID_PORTFOLIO_NAME_TYPE"
    assert position_error.value.primary_issue.code == "INVALID_POSITION"
    assert position_error.value.primary_issue.item == "0"


def test_portfolio_rejects_datetime_as_reference_date() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        Portfolio(
            "Datetime",
            (make_position("PETR4", "1", "10"),),
            reference_date=cast(date, datetime(2026, 7, 13, 12, 0)),
        )

    assert exc_info.value.primary_issue.code == "INVALID_REFERENCE_DATE"


def test_portfolio_rejects_invalid_weight_basis() -> None:
    portfolio = Portfolio("Brazil", (make_position("PETR4", "1", "10"),))

    with pytest.raises(DomainValidationError) as exc_info:
        portfolio.weights(cast(WeightBasis, "net"))

    assert exc_info.value.primary_issue.code == "INVALID_WEIGHT_BASIS"


def test_portfolio_is_immutable() -> None:
    portfolio = Portfolio("Brazil", (make_position("PETR4", "1", "10"),))

    attribute = "name"
    with pytest.raises(FrozenInstanceError):
        setattr(portfolio, attribute, "Changed")
