"""Unit tests for moments, covariance, and correlation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, localcontext
from typing import cast

import pytest

from zeus_risk.core.analytics import (
    calculate_correlation_matrix,
    calculate_covariance_matrix,
    calculate_descriptive_statistics,
)
from zeus_risk.domain import (
    Currency,
    DataFrequency,
    MatrixKind,
    PriceSeriesKey,
    ReturnMethod,
    ReturnObservation,
    ReturnRow,
    ReturnSeries,
    ReturnTable,
    VarianceEstimator,
)
from zeus_risk.exceptions import AnalyticsError


def _key(ticker: str) -> PriceSeriesKey:
    return PriceSeriesKey(ticker, Currency("BRL"))


def _series(values: tuple[str, ...]) -> ReturnSeries:
    return ReturnSeries(
        key=_key("AAA"),
        frequency=DataFrequency.DAILY,
        method=ReturnMethod.SIMPLE,
        initial_date=date(2026, 1, 1),
        observations=tuple(
            ReturnObservation(date(2026, 1, index + 2), Decimal(value))
            for index, value in enumerate(values)
        ),
    )


def _table(
    first: tuple[str, ...] = ("0.1", "0.2", "0.3"),
    second: tuple[str, ...] = ("0.3", "0.2", "0.1"),
) -> ReturnTable:
    return ReturnTable(
        keys=(_key("AAA"), _key("BBB")),
        frequency=DataFrequency.DAILY,
        method=ReturnMethod.SIMPLE,
        initial_date=date(2026, 1, 1),
        rows=tuple(
            ReturnRow(
                date(2026, 1, index + 2),
                (Decimal(left), Decimal(right)),
            )
            for index, (left, right) in enumerate(zip(first, second, strict=True))
        ),
    )


def test_sample_statistics_match_manual_reference() -> None:
    result = calculate_descriptive_statistics(_series(("0.01", "0.02", "0.03")))

    assert result.estimator is VarianceEstimator.SAMPLE
    assert result.mean == Decimal("0.02")
    assert result.variance == Decimal("0.0001")
    assert result.volatility == Decimal("0.01")
    assert result.annualization_factor == Decimal("252")
    with localcontext() as context:
        context.prec = 34
        expected_annualized = Decimal("0.01") * Decimal("252").sqrt()
    assert result.annualized_volatility == expected_annualized


def test_population_estimator_supports_one_observation() -> None:
    result = calculate_descriptive_statistics(
        _series(("0.02",)),
        VarianceEstimator.POPULATION,
        annualization_factor=Decimal("1"),
    )

    assert result.mean == Decimal("0.02")
    assert result.variance == Decimal("0")
    assert result.volatility == Decimal("0")


def test_covariance_and_correlation_matrices_are_symmetric() -> None:
    covariance = calculate_covariance_matrix(_table())
    correlation = calculate_correlation_matrix(_table())

    assert covariance.kind is MatrixKind.COVARIANCE
    assert covariance.values == (
        (Decimal("0.01"), Decimal("-0.01")),
        (Decimal("-0.01"), Decimal("0.01")),
    )
    assert correlation.kind is MatrixKind.CORRELATION
    assert correlation.values == (
        (Decimal("1"), Decimal("-1")),
        (Decimal("-1"), Decimal("1")),
    )


def test_population_covariance_uses_n_denominator() -> None:
    result = calculate_covariance_matrix(_table(), VarianceEstimator.POPULATION)

    with localcontext() as context:
        context.prec = 34
        expected = Decimal("0.02") / Decimal("3")
    assert result.values[0][0] == expected
    assert abs(result.values[0][1] + expected) < Decimal("1e-32")


def test_covariance_accepts_constant_series_but_correlation_rejects_it() -> None:
    table = _table(first=("0.1", "0.1", "0.1"))

    covariance = calculate_covariance_matrix(table)
    with pytest.raises(AnalyticsError) as exc_info:
        calculate_correlation_matrix(table)

    assert covariance.values[0][0] == Decimal("0")
    assert exc_info.value.primary_issue.code == "ZERO_RETURN_VARIANCE"
    assert exc_info.value.primary_issue.item == "AAA:BRL"


def test_rejects_insufficient_sample_and_invalid_configuration() -> None:
    one = _series(("0.1",))
    with pytest.raises(AnalyticsError) as sample_error:
        calculate_descriptive_statistics(one)
    with pytest.raises(AnalyticsError) as estimator_error:
        calculate_descriptive_statistics(one, cast(VarianceEstimator, "sample"))
    with pytest.raises(AnalyticsError) as annualization_error:
        calculate_descriptive_statistics(
            one,
            VarianceEstimator.POPULATION,
            annualization_factor=Decimal("0"),
        )

    assert sample_error.value.primary_issue.code == "INSUFFICIENT_RETURN_OBSERVATIONS"
    assert estimator_error.value.primary_issue.code == "INVALID_VARIANCE_ESTIMATOR"
    assert annualization_error.value.primary_issue.code == "INVALID_ANNUALIZATION_FACTOR"


def test_rejects_invalid_matrix_input_type() -> None:
    with pytest.raises(AnalyticsError) as exc_info:
        calculate_covariance_matrix(cast(ReturnTable, object()))

    assert exc_info.value.primary_issue.code == "INVALID_RETURN_TABLE"
