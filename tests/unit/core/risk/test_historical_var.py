"""Unit tests for deterministic historical Value at Risk."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import cast

import pytest

from zeus_risk.core.risk import calculate_historical_var
from zeus_risk.domain import (
    Currency,
    DataFrequency,
    HistoricalVaRConfiguration,
    LossConvention,
    PriceSeriesKey,
    ReturnMethod,
    ReturnObservation,
    ReturnSeries,
    RiskMeasureUnit,
)
from zeus_risk.exceptions import RiskCalculationError


def _series(
    values: tuple[str, ...],
    *,
    method: ReturnMethod = ReturnMethod.SIMPLE,
) -> ReturnSeries:
    initial_date = date(2026, 1, 1)
    return ReturnSeries(
        key=PriceSeriesKey("ZEUS", Currency("BRL")),
        frequency=DataFrequency.DAILY,
        method=method,
        initial_date=initial_date,
        observations=tuple(
            ReturnObservation(initial_date + timedelta(days=index + 1), Decimal(value))
            for index, value in enumerate(values)
        ),
    )


def test_calculates_nearest_rank_var_with_auditable_loss_sample() -> None:
    returns = _series(("0.02", "-0.01", "-0.04", "0.03", "-0.10"))
    configuration = HistoricalVaRConfiguration(Decimal("0.8"), window=5)

    result = calculate_historical_var(returns, configuration)

    assert tuple(item.value for item in result.losses) == (
        Decimal("-0.02"),
        Decimal("0.01"),
        Decimal("0.04"),
        Decimal("-0.03"),
        Decimal("0.10"),
    )
    assert result.quantile_rank == 4
    assert result.quantile_loss == Decimal("0.04")
    assert result.value_at_risk == Decimal("0.04")
    assert result.observation_count == 5
    assert result.sample_start_date == date(2026, 1, 1)
    assert result.sample_end_date == date(2026, 1, 6)
    assert result.reference_date == date(2026, 1, 6)
    assert result.loss_convention is LossConvention.NEGATIVE_RETURN
    assert result.unit is RiskMeasureUnit.RELATIVE_RETURN


def test_window_selects_only_the_most_recent_historical_scenarios() -> None:
    returns = _series(("-0.90", "0.02", "-0.01", "-0.04", "0.03", "-0.10"))
    configuration = HistoricalVaRConfiguration(Decimal("0.8"), window=5)

    result = calculate_historical_var(returns, configuration)

    assert result.sample_start_date == date(2026, 1, 2)
    assert Decimal("0.90") not in tuple(item.value for item in result.losses)
    assert result.value_at_risk == Decimal("0.04")


def test_compounds_overlapping_simple_returns_for_multi_day_horizon() -> None:
    returns = _series(("0.10", "-0.10", "0.20", "-0.20", "0.05"))
    configuration = HistoricalVaRConfiguration(
        Decimal("0.5"),
        horizon_days=2,
        window=2,
    )

    result = calculate_historical_var(returns, configuration)

    assert tuple(item.value for item in result.losses) == (
        Decimal("0.04"),
        Decimal("0.160"),
    )
    assert result.losses[0].start_date == date(2026, 1, 3)
    assert result.losses[0].end_date == date(2026, 1, 5)
    assert result.quantile_rank == 1
    assert result.value_at_risk == Decimal("0.04")


def test_sums_log_returns_for_multi_day_horizon() -> None:
    returns = _series(("0.10", "-0.20", "0.30"), method=ReturnMethod.LOG)
    configuration = HistoricalVaRConfiguration(
        Decimal("0.5"),
        horizon_days=2,
        window=2,
    )

    result = calculate_historical_var(returns, configuration)

    assert tuple(item.value for item in result.losses) == (
        Decimal("0.10"),
        Decimal("-0.10"),
    )
    assert result.return_method is ReturnMethod.LOG
    assert result.quantile_loss == Decimal("-0.10")
    assert result.value_at_risk == Decimal("0")


def test_floors_a_gain_quantile_at_zero_instead_of_reporting_negative_risk() -> None:
    returns = _series(("0.01", "0.02"))
    configuration = HistoricalVaRConfiguration(Decimal("0.5"), window=2)

    result = calculate_historical_var(returns, configuration)

    assert result.quantile_loss == Decimal("-0.02")
    assert result.value_at_risk == Decimal("0")


def test_rejects_insufficient_history_for_window_and_horizon() -> None:
    returns = _series(("0.01", "-0.02", "0.03"))
    configuration = HistoricalVaRConfiguration(
        Decimal("0.5"),
        horizon_days=2,
        window=2,
    )
    short_returns = _series(("0.01", "-0.02"))

    result = calculate_historical_var(returns, configuration)

    assert result.observation_count == 2
    with pytest.raises(RiskCalculationError) as exc_info:
        calculate_historical_var(short_returns, configuration)
    assert exc_info.value.primary_issue.code == "INSUFFICIENT_HISTORICAL_OBSERVATIONS"
    assert exc_info.value.primary_issue.item == "required=3,actual=2"


def test_rejects_invalid_calculation_boundary_types() -> None:
    configuration = HistoricalVaRConfiguration(Decimal("0.5"), window=2)

    with pytest.raises(RiskCalculationError) as series_error:
        calculate_historical_var(cast(ReturnSeries, object()), configuration)
    with pytest.raises(RiskCalculationError) as configuration_error:
        calculate_historical_var(
            _series(("0.01", "-0.02")),
            cast(HistoricalVaRConfiguration, object()),
        )

    assert series_error.value.primary_issue.code == "INVALID_VAR_RETURN_SERIES"
    assert configuration_error.value.primary_issue.code == "INVALID_VAR_CONFIGURATION"
