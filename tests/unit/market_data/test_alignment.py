"""Unit tests for deterministic price-series alignment."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import cast

import pytest

from zeus_risk.domain import Currency, DataFrequency, PriceObservation, PriceSeries, PriceSeriesKey
from zeus_risk.exceptions import MarketDataError
from zeus_risk.market_data import AlignmentPolicy, align_price_series


def _series(ticker: str, values: tuple[tuple[date, str], ...]) -> PriceSeries:
    return PriceSeries(
        key=PriceSeriesKey(ticker, Currency("BRL")),
        frequency=DataFrequency.DAILY,
        observations=tuple(
            PriceObservation(observed_on=observed_on, price=Decimal(price))
            for observed_on, price in values
        ),
    )


def test_intersection_keeps_only_common_dates() -> None:
    first = _series(
        "AAA",
        ((date(2026, 1, 2), "10"), (date(2026, 1, 3), "11")),
    )
    second = _series(
        "BBB",
        ((date(2026, 1, 3), "20"), (date(2026, 1, 4), "21")),
    )

    table = align_price_series((first, second), AlignmentPolicy.INTERSECTION)

    assert table.keys == (first.key, second.key)
    assert table.policy is AlignmentPolicy.INTERSECTION
    assert len(table.rows) == 1
    assert table.rows[0].observed_on == date(2026, 1, 3)
    assert table.rows[0].prices == (Decimal("11"), Decimal("20"))


def test_union_keeps_all_dates_and_uses_none_without_filling() -> None:
    first = _series(
        "AAA",
        ((date(2026, 1, 2), "10"), (date(2026, 1, 3), "11")),
    )
    second = _series(
        "BBB",
        ((date(2026, 1, 3), "20"), (date(2026, 1, 4), "21")),
    )

    table = align_price_series((first, second), AlignmentPolicy.UNION)

    assert tuple(row.observed_on for row in table.rows) == (
        date(2026, 1, 2),
        date(2026, 1, 3),
        date(2026, 1, 4),
    )
    assert tuple(row.prices for row in table.rows) == (
        (Decimal("10"), None),
        (Decimal("11"), Decimal("20")),
        (None, Decimal("21")),
    )


def test_single_series_alignment_preserves_observations() -> None:
    series = _series(
        "AAA",
        ((date(2026, 1, 2), "10"), (date(2026, 1, 3), "11")),
    )

    table = align_price_series((series,), AlignmentPolicy.INTERSECTION)

    assert tuple(row.prices for row in table.rows) == ((Decimal("10"),), (Decimal("11"),))


def test_intersection_without_common_dates_is_explicit_error() -> None:
    first = _series("AAA", ((date(2026, 1, 2), "10"),))
    second = _series("BBB", ((date(2026, 1, 3), "20"),))

    with pytest.raises(MarketDataError) as exc_info:
        align_price_series((first, second), AlignmentPolicy.INTERSECTION)

    assert exc_info.value.primary_issue.issue.code == "NO_COMMON_PRICE_DATES"


def test_rejects_empty_duplicate_and_invalid_policy_inputs() -> None:
    series = _series("AAA", ((date(2026, 1, 2), "10"),))

    with pytest.raises(MarketDataError) as empty_error:
        align_price_series((), AlignmentPolicy.UNION)
    with pytest.raises(MarketDataError) as duplicate_error:
        align_price_series((series, series), AlignmentPolicy.UNION)
    with pytest.raises(MarketDataError) as policy_error:
        align_price_series((series,), cast(AlignmentPolicy, "outer"))

    assert empty_error.value.primary_issue.issue.code == "EMPTY_ALIGNMENT_INPUT"
    assert duplicate_error.value.primary_issue.issue.code == "DUPLICATE_ALIGNMENT_SERIES"
    assert policy_error.value.primary_issue.issue.code == "INVALID_ALIGNMENT_POLICY"
