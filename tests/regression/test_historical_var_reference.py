"""Regression test for a manually reconcilable historical VaR sample."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from zeus_risk.core.risk import calculate_historical_var
from zeus_risk.domain import (
    Currency,
    DataFrequency,
    HistoricalVaRConfiguration,
    PriceSeriesKey,
    ReturnMethod,
    ReturnObservation,
    ReturnSeries,
)


def test_ninety_percent_nearest_rank_reference_value_is_stable() -> None:
    initial_date = date(2026, 1, 1)
    values = (
        "0.04",
        "-0.02",
        "0.01",
        "-0.08",
        "0.03",
        "-0.01",
        "-0.12",
        "0.02",
        "-0.04",
        "0.05",
    )
    returns = ReturnSeries(
        key=PriceSeriesKey("REFERENCE", Currency("BRL")),
        frequency=DataFrequency.DAILY,
        method=ReturnMethod.SIMPLE,
        initial_date=initial_date,
        observations=tuple(
            ReturnObservation(initial_date + timedelta(days=index + 1), Decimal(value))
            for index, value in enumerate(values)
        ),
    )

    result = calculate_historical_var(
        returns,
        HistoricalVaRConfiguration(Decimal("0.9"), window=10),
    )

    assert tuple(sorted(item.value for item in result.losses)) == (
        Decimal("-0.05"),
        Decimal("-0.04"),
        Decimal("-0.03"),
        Decimal("-0.02"),
        Decimal("-0.01"),
        Decimal("0.01"),
        Decimal("0.02"),
        Decimal("0.04"),
        Decimal("0.08"),
        Decimal("0.12"),
    )
    assert result.quantile_rank == 9
    assert result.quantile_loss == Decimal("0.08")
    assert result.value_at_risk == Decimal("0.08")
