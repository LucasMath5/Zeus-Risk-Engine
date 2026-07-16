"""Regression tests for a manually reconcilable descriptive-analytics dataset."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, localcontext

from zeus_risk.core.analytics import (
    calculate_covariance_matrix,
    calculate_descriptive_statistics,
    calculate_drawdown,
    calculate_return_table,
)
from zeus_risk.domain import Currency, DataFrequency, PriceSeriesKey, ReturnMethod
from zeus_risk.market_data import (
    AlignedPriceRow,
    AlignedPriceTable,
    AlignmentPolicy,
)


def test_reference_prices_reconcile_returns_variance_covariance_and_drawdown() -> None:
    keys = (
        PriceSeriesKey("AAA", Currency("BRL")),
        PriceSeriesKey("BBB", Currency("BRL")),
    )
    prices = AlignedPriceTable(
        keys=keys,
        frequency=DataFrequency.DAILY,
        policy=AlignmentPolicy.INTERSECTION,
        rows=(
            AlignedPriceRow(date(2026, 1, 1), (Decimal("100"), Decimal("100"))),
            AlignedPriceRow(date(2026, 1, 2), (Decimal("110"), Decimal("120"))),
            AlignedPriceRow(date(2026, 1, 3), (Decimal("99"), Decimal("120"))),
            AlignedPriceRow(date(2026, 1, 4), (Decimal("108.9"), Decimal("144"))),
        ),
    )

    returns = calculate_return_table(prices, ReturnMethod.SIMPLE)
    first = returns.series(keys[0])
    statistics = calculate_descriptive_statistics(first, annualization_factor=Decimal("1"))
    covariance = calculate_covariance_matrix(returns)
    drawdown = calculate_drawdown(first)

    with localcontext() as context:
        context.prec = 34
        one_thirtieth = Decimal("1") / Decimal("30")
        one_seventy_fifth = Decimal("1") / Decimal("75")
    assert first.values == (Decimal("0.1"), Decimal("-0.1"), Decimal("0.1"))
    assert statistics.mean == one_thirtieth
    assert statistics.variance == one_seventy_fifth
    assert abs(covariance.values[0][1] - one_seventy_fifth) < Decimal("1e-32")
    assert drawdown.maximum_drawdown == Decimal("0.1")
    assert drawdown.peak_date == date(2026, 1, 2)
    assert drawdown.trough_date == date(2026, 1, 3)
    assert drawdown.recovery_date is None
