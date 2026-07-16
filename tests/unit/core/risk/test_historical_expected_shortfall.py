"""Unit tests for historical Expected Shortfall."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import cast

import pytest

from zeus_risk.core.risk import calculate_historical_expected_shortfall
from zeus_risk.domain import (
    Currency,
    DataFrequency,
    HistoricalVaRConfiguration,
    PriceSeriesKey,
    ReturnMethod,
    ReturnObservation,
    ReturnSeries,
)
from zeus_risk.exceptions import RiskCalculationError


def _series(values: tuple[str, ...]) -> ReturnSeries:
    initial_date = date(2026, 1, 1)
    return ReturnSeries(
        key=PriceSeriesKey("ZEUS", Currency("BRL")),
        frequency=DataFrequency.DAILY,
        method=ReturnMethod.SIMPLE,
        initial_date=initial_date,
        observations=tuple(
            ReturnObservation(initial_date + timedelta(days=index + 1), Decimal(value))
            for index, value in enumerate(values)
        ),
    )


def test_averages_losses_strictly_beyond_the_var_rank() -> None:
    returns = _series(("0.02", "-0.01", "-0.04", "0.03", "-0.10"))
    configuration = HistoricalVaRConfiguration(Decimal("0.8"), window=5)

    result = calculate_historical_expected_shortfall(returns, configuration)

    assert result.historical_var.quantile_loss == Decimal("0.04")
    assert tuple(item.value for item in result.tail_losses) == (Decimal("0.10"),)
    assert result.tail_mean_loss == Decimal("0.10")
    assert result.expected_shortfall == Decimal("0.10")
    assert result.expected_shortfall >= result.historical_var.value_at_risk
    assert result.tail_count == 1


def test_uses_the_arithmetic_mean_when_the_tail_has_multiple_ranks() -> None:
    returns = _series(("0.02", "-0.01", "-0.04", "-0.10"))
    configuration = HistoricalVaRConfiguration(Decimal("0.5"), window=4)

    result = calculate_historical_expected_shortfall(returns, configuration)

    assert result.historical_var.quantile_rank == 2
    assert result.historical_var.quantile_loss == Decimal("0.01")
    assert tuple(item.value for item in result.tail_losses) == (
        Decimal("0.04"),
        Decimal("0.10"),
    )
    assert result.tail_mean_loss == Decimal("0.07")
    assert result.expected_shortfall == Decimal("0.07")


def test_breaks_boundary_ties_chronologically_without_expanding_the_tail() -> None:
    returns = _series(("-0.01", "-0.04", "-0.04", "-0.04"))
    configuration = HistoricalVaRConfiguration(Decimal("0.5"), window=4)

    result = calculate_historical_expected_shortfall(returns, configuration)

    assert result.historical_var.quantile_loss == Decimal("0.04")
    assert result.tail_count == 2
    assert tuple(item.end_date for item in result.tail_losses) == (
        date(2026, 1, 4),
        date(2026, 1, 5),
    )
    assert result.tail_mean_loss == Decimal("0.04")
    assert result.expected_shortfall == result.historical_var.value_at_risk


def test_floors_a_gain_tail_at_zero_and_preserves_the_raw_mean() -> None:
    returns = _series(("0.01", "0.02"))
    configuration = HistoricalVaRConfiguration(Decimal("0.5"), window=2)

    result = calculate_historical_expected_shortfall(returns, configuration)

    assert result.historical_var.value_at_risk == Decimal("0")
    assert result.tail_mean_loss == Decimal("-0.01")
    assert result.expected_shortfall == Decimal("0")


def test_preserves_var_configuration_sample_and_tail_dates() -> None:
    returns = _series(("0.02", "-0.01", "-0.04", "-0.10"))
    configuration = HistoricalVaRConfiguration(Decimal("0.5"), window=4)

    result = calculate_historical_expected_shortfall(returns, configuration)

    assert result.historical_var.configuration is configuration
    assert result.historical_var.losses[0].start_date == date(2026, 1, 1)
    assert result.tail_start_date == date(2026, 1, 3)
    assert result.tail_end_date == date(2026, 1, 5)


def test_propagates_var_boundary_and_insufficient_history_failures() -> None:
    configuration = HistoricalVaRConfiguration(Decimal("0.5"), window=2)

    with pytest.raises(RiskCalculationError) as type_error:
        calculate_historical_expected_shortfall(cast(ReturnSeries, object()), configuration)
    with pytest.raises(RiskCalculationError) as history_error:
        calculate_historical_expected_shortfall(_series(("0.01",)), configuration)

    assert type_error.value.primary_issue.code == "INVALID_VAR_RETURN_SERIES"
    assert history_error.value.primary_issue.code == "INSUFFICIENT_HISTORICAL_OBSERVATIONS"
