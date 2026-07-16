"""Unit tests for wealth paths and maximum drawdown episodes."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, localcontext
from typing import cast

import pytest

from zeus_risk.core.analytics import calculate_drawdown
from zeus_risk.domain import (
    Currency,
    DataFrequency,
    PriceSeriesKey,
    ReturnMethod,
    ReturnObservation,
    ReturnSeries,
)
from zeus_risk.exceptions import AnalyticsError


def _series(values: tuple[str, ...], method: ReturnMethod = ReturnMethod.SIMPLE) -> ReturnSeries:
    return ReturnSeries(
        key=PriceSeriesKey("ZEUS", Currency("BRL")),
        frequency=DataFrequency.DAILY,
        method=method,
        initial_date=date(2026, 1, 1),
        observations=tuple(
            ReturnObservation(date(2026, 1, index + 2), Decimal(value))
            for index, value in enumerate(values)
        ),
    )


def test_calculates_peak_trough_and_unrecovered_maximum_drawdown() -> None:
    result = calculate_drawdown(_series(("0.1", "-0.2", "-0.1", "0.3")))

    assert tuple(item.wealth_index for item in result.observations) == (
        Decimal("1.1"),
        Decimal("0.88"),
        Decimal("0.792"),
        Decimal("1.0296"),
    )
    assert result.maximum_drawdown == Decimal("0.28")
    assert result.peak_date == date(2026, 1, 2)
    assert result.trough_date == date(2026, 1, 4)
    assert result.recovery_date is None


def test_identifies_recovery_after_maximum_drawdown() -> None:
    result = calculate_drawdown(_series(("0.1", "-0.2", "-0.1", "0.4")))

    assert result.maximum_drawdown == Decimal("0.28")
    assert result.recovery_date == date(2026, 1, 5)
    assert result.observations[-1].wealth_index == Decimal("1.1088")


def test_increasing_path_has_zero_drawdown() -> None:
    result = calculate_drawdown(_series(("0.1", "0.2")))

    assert result.maximum_drawdown == Decimal("0")
    assert result.peak_date == date(2026, 1, 1)
    assert result.trough_date == date(2026, 1, 1)
    assert result.recovery_date is None
    assert all(item.drawdown == Decimal("0") for item in result.observations)


def test_log_and_simple_paths_produce_equivalent_wealth() -> None:
    simple = calculate_drawdown(_series(("0.1", "-0.2")))
    with localcontext() as context:
        context.prec = 34
        log_values = (Decimal("1.1").ln(), Decimal("0.8").ln())
    log = calculate_drawdown(
        ReturnSeries(
            key=simple.key,
            frequency=DataFrequency.DAILY,
            method=ReturnMethod.LOG,
            initial_date=date(2026, 1, 1),
            observations=(
                ReturnObservation(date(2026, 1, 2), log_values[0]),
                ReturnObservation(date(2026, 1, 3), log_values[1]),
            ),
        )
    )

    assert abs(log.observations[-1].wealth_index - simple.observations[-1].wealth_index) < Decimal(
        "1e-32"
    )
    assert abs(log.maximum_drawdown - simple.maximum_drawdown) < Decimal("1e-32")


def test_rejects_invalid_return_series_type() -> None:
    with pytest.raises(AnalyticsError) as exc_info:
        calculate_drawdown(cast(ReturnSeries, object()))

    assert exc_info.value.primary_issue.code == "INVALID_RETURN_SERIES"
