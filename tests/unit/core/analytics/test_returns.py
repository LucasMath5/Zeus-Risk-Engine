"""Unit tests for asset and constant-weight portfolio returns."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, localcontext
from typing import cast

import pytest

from zeus_risk.core.analytics import (
    calculate_portfolio_return_series,
    calculate_return_series,
    calculate_return_table,
)
from zeus_risk.domain import (
    AssetClass,
    Currency,
    DataFrequency,
    Instrument,
    Portfolio,
    Position,
    PriceObservation,
    PriceSeries,
    PriceSeriesKey,
    ReturnMethod,
    ReturnRow,
    ReturnTable,
)
from zeus_risk.exceptions import AnalyticsError
from zeus_risk.market_data import (
    AlignedPriceRow,
    AlignedPriceTable,
    AlignmentPolicy,
)


def _key(ticker: str, currency: str = "BRL") -> PriceSeriesKey:
    return PriceSeriesKey(ticker, Currency(currency))


def _price_series(values: tuple[str, ...] = ("100", "110", "99")) -> PriceSeries:
    return PriceSeries(
        key=_key("AAA"),
        frequency=DataFrequency.DAILY,
        observations=tuple(
            PriceObservation(date(2026, 1, index + 1), Decimal(value))
            for index, value in enumerate(values)
        ),
    )


def _portfolio(
    positions: tuple[tuple[str, str, str], ...] = (
        ("AAA", "6", "100"),
        ("BBB", "4", "100"),
    ),
) -> Portfolio:
    return Portfolio(
        "Test Portfolio",
        tuple(
            Position(
                Instrument(ticker, AssetClass.EQUITY, Currency("BRL")),
                Decimal(quantity),
                Decimal(price),
            )
            for ticker, quantity, price in positions
        ),
    )


def _return_table(
    *,
    method: ReturnMethod = ReturnMethod.SIMPLE,
    rows: tuple[tuple[str, str], ...] = (("0.1", "-0.05"), ("-0.1", "0.2")),
) -> ReturnTable:
    return ReturnTable(
        keys=(_key("AAA"), _key("BBB")),
        frequency=DataFrequency.DAILY,
        method=method,
        initial_date=date(2026, 1, 1),
        rows=tuple(
            ReturnRow(
                date(2026, 1, index + 2),
                tuple(Decimal(value) for value in values),
            )
            for index, values in enumerate(rows)
        ),
    )


def test_calculates_exact_simple_returns_for_one_series() -> None:
    result = calculate_return_series(_price_series(), ReturnMethod.SIMPLE)

    assert result.initial_date == date(2026, 1, 1)
    assert result.values == (Decimal("0.1"), Decimal("-0.1"))


def test_log_returns_reconcile_with_total_price_ratio() -> None:
    result = calculate_return_series(_price_series(), ReturnMethod.LOG)

    with localcontext() as context:
        context.prec = 34
        assert abs(sum(result.values) - (Decimal("99") / Decimal("100")).ln()) < Decimal("1e-32")


def test_calculates_return_table_and_preserves_key_order() -> None:
    prices = AlignedPriceTable(
        keys=(_key("AAA"), _key("BBB")),
        frequency=DataFrequency.DAILY,
        policy=AlignmentPolicy.INTERSECTION,
        rows=(
            AlignedPriceRow(date(2026, 1, 1), (Decimal("100"), Decimal("50"))),
            AlignedPriceRow(date(2026, 1, 2), (Decimal("110"), Decimal("55"))),
            AlignedPriceRow(date(2026, 1, 3), (Decimal("99"), Decimal("60.5"))),
        ),
    )

    result = calculate_return_table(prices, ReturnMethod.SIMPLE)

    assert result.keys == prices.keys
    assert tuple(row.values for row in result.rows) == (
        (Decimal("0.1"), Decimal("0.1")),
        (Decimal("-0.1"), Decimal("0.1")),
    )


def test_rejects_missing_aligned_prices_without_filling() -> None:
    prices = AlignedPriceTable(
        keys=(_key("AAA"), _key("BBB")),
        frequency=DataFrequency.DAILY,
        policy=AlignmentPolicy.UNION,
        rows=(
            AlignedPriceRow(date(2026, 1, 1), (Decimal("100"), None)),
            AlignedPriceRow(date(2026, 1, 2), (Decimal("110"), Decimal("50"))),
        ),
    )

    with pytest.raises(AnalyticsError) as exc_info:
        calculate_return_table(prices, ReturnMethod.SIMPLE)

    assert exc_info.value.primary_issue.code == "MISSING_ALIGNED_PRICE"
    assert exc_info.value.primary_issue.item == "BBB:BRL:2026-01-01"


def test_calculates_constant_net_weight_portfolio_returns() -> None:
    result = calculate_portfolio_return_series(_return_table(), _portfolio())

    assert result.key == _key("TEST PORTFOLIO")
    assert result.values == (Decimal("0.04"), Decimal("0.02"))


def test_long_short_portfolio_preserves_signed_net_exposure() -> None:
    portfolio = _portfolio((("AAA", "10", "100"), ("BBB", "-2", "100")))
    table = _return_table(rows=(("0.1", "0.2"), ("-0.1", "-0.2")))

    result = calculate_portfolio_return_series(table, portfolio)

    assert result.values == (Decimal("0.075"), Decimal("-0.075"))


def test_log_portfolio_return_uses_weighted_simple_growth() -> None:
    with localcontext() as context:
        context.prec = 34
        log_rows = (((Decimal("1.1").ln()), Decimal("1.2").ln()),)
    table = ReturnTable(
        keys=(_key("AAA"), _key("BBB")),
        frequency=DataFrequency.DAILY,
        method=ReturnMethod.LOG,
        initial_date=date(2026, 1, 1),
        rows=(ReturnRow(date(2026, 1, 2), log_rows[0]),),
    )

    result = calculate_portfolio_return_series(table, _portfolio())

    with localcontext() as context:
        context.prec = 34
        expected = Decimal("1.14").ln()
    assert abs(result.values[0] - expected) < Decimal("1e-32")


def test_rejects_insufficient_invalid_and_mismatched_inputs() -> None:
    with pytest.raises(AnalyticsError) as insufficient:
        calculate_return_series(_price_series(("100",)), ReturnMethod.SIMPLE)
    with pytest.raises(AnalyticsError) as invalid_method:
        calculate_return_series(_price_series(), cast(ReturnMethod, "simple"))

    mismatch = ReturnTable(
        keys=(_key("AAA"),),
        frequency=DataFrequency.DAILY,
        method=ReturnMethod.SIMPLE,
        initial_date=date(2026, 1, 1),
        rows=(ReturnRow(date(2026, 1, 2), (Decimal("0.1"),)),),
    )
    with pytest.raises(AnalyticsError) as mismatch_error:
        calculate_portfolio_return_series(mismatch, _portfolio())

    assert insufficient.value.primary_issue.code == "INSUFFICIENT_PRICE_OBSERVATIONS"
    assert invalid_method.value.primary_issue.code == "INVALID_RETURN_METHOD"
    assert mismatch_error.value.primary_issue.code == "PORTFOLIO_RETURN_SERIES_MISMATCH"


def test_rejects_currency_aggregation_and_zero_net_weights() -> None:
    mixed = ReturnTable(
        keys=(_key("AAA"), _key("BBB", "USD")),
        frequency=DataFrequency.DAILY,
        method=ReturnMethod.SIMPLE,
        initial_date=date(2026, 1, 1),
        rows=(ReturnRow(date(2026, 1, 2), (Decimal("0.1"), Decimal("0.2"))),),
    )
    with pytest.raises(AnalyticsError) as currency_error:
        calculate_portfolio_return_series(mixed, _portfolio())

    neutral = _portfolio((("AAA", "1", "100"), ("BBB", "-2", "50")))
    with pytest.raises(AnalyticsError) as neutral_error:
        calculate_portfolio_return_series(_return_table(), neutral)

    assert currency_error.value.primary_issue.code == "PORTFOLIO_RETURN_REQUIRES_SINGLE_CURRENCY"
    assert neutral_error.value.primary_issue.code == "ZERO_NET_MARKET_VALUE"


def test_rejects_non_positive_leveraged_portfolio_growth() -> None:
    portfolio = _portfolio((("AAA", "2", "100"), ("BBB", "-1", "100")))
    simple_table = _return_table(rows=(("-0.9", "10"),))
    with pytest.raises(AnalyticsError) as simple_error:
        calculate_portfolio_return_series(simple_table, portfolio)

    with localcontext() as context:
        context.prec = 34
        values = (Decimal("0.1").ln(), Decimal("11").ln())
    table = ReturnTable(
        keys=(_key("AAA"), _key("BBB")),
        frequency=DataFrequency.DAILY,
        method=ReturnMethod.LOG,
        initial_date=date(2026, 1, 1),
        rows=(ReturnRow(date(2026, 1, 2), values),),
    )

    with pytest.raises(AnalyticsError) as exc_info:
        calculate_portfolio_return_series(table, portfolio)

    assert simple_error.value.primary_issue.code == "NON_POSITIVE_PORTFOLIO_GROWTH"
    assert exc_info.value.primary_issue.code == "NON_POSITIVE_PORTFOLIO_GROWTH"
