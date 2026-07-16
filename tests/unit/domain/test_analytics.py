"""Unit tests for immutable descriptive-analytics contracts."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import cast

import pytest

from zeus_risk.domain import (
    Currency,
    DataFrequency,
    DomainValidationError,
    DrawdownObservation,
    DrawdownResult,
    MatrixKind,
    PriceSeriesKey,
    ReturnMethod,
    ReturnObservation,
    ReturnRow,
    ReturnSeries,
    ReturnTable,
    StatisticMatrix,
    VarianceEstimator,
)


def _key(ticker: str = "ZEUS") -> PriceSeriesKey:
    return PriceSeriesKey(ticker, Currency("BRL"))


def _series(values: tuple[str, ...] = ("0.1", "-0.05")) -> ReturnSeries:
    return ReturnSeries(
        key=_key(),
        frequency=DataFrequency.DAILY,
        method=ReturnMethod.SIMPLE,
        initial_date=date(2026, 1, 1),
        observations=tuple(
            ReturnObservation(date(2026, 1, index + 2), Decimal(value))
            for index, value in enumerate(values)
        ),
    )


def test_return_series_exposes_ordered_values_and_dates() -> None:
    series = _series()

    assert series.values == (Decimal("0.1"), Decimal("-0.05"))
    assert series.start_date == date(2026, 1, 2)
    assert series.end_date == date(2026, 1, 3)


def test_return_table_extracts_one_series() -> None:
    first = _key("AAA")
    second = _key("BBB")
    table = ReturnTable(
        keys=(first, second),
        frequency=DataFrequency.DAILY,
        method=ReturnMethod.SIMPLE,
        initial_date=date(2026, 1, 1),
        rows=(
            ReturnRow(date(2026, 1, 2), (Decimal("0.1"), Decimal("0.2"))),
            ReturnRow(date(2026, 1, 3), (Decimal("0.2"), Decimal("0.1"))),
        ),
    )

    extracted = table.series(second)

    assert table.observation_count == 2
    assert extracted.key == second
    assert extracted.values == (Decimal("0.2"), Decimal("0.1"))

    with pytest.raises(DomainValidationError) as missing_error:
        table.series(_key("MISSING"))
    with pytest.raises(DomainValidationError) as type_error:
        table.series(cast(PriceSeriesKey, "AAA"))
    assert missing_error.value.primary_issue.code == "RETURN_SERIES_NOT_FOUND"
    assert type_error.value.primary_issue.code == "INVALID_RETURN_SERIES_KEY"


@pytest.mark.parametrize(
    ("factory", "expected_code"),
    [
        (
            lambda: ReturnObservation(date(2026, 1, 2), Decimal("NaN")),
            "NON_FINITE_ANALYTICS_VALUE",
        ),
        (
            lambda: ReturnSeries(
                _key(),
                DataFrequency.DAILY,
                ReturnMethod.SIMPLE,
                date(2026, 1, 2),
                (ReturnObservation(date(2026, 1, 2), Decimal("0.1")),),
            ),
            "INVALID_RETURN_INITIAL_DATE",
        ),
        (
            lambda: ReturnSeries(
                _key(),
                DataFrequency.DAILY,
                ReturnMethod.SIMPLE,
                date(2026, 1, 1),
                (ReturnObservation(date(2026, 1, 2), Decimal("-1")),),
            ),
            "NON_POSITIVE_RETURN_GROWTH",
        ),
        (
            lambda: ReturnSeries(
                _key(),
                DataFrequency.DAILY,
                ReturnMethod.SIMPLE,
                date(2026, 1, 1),
                (
                    ReturnObservation(date(2026, 1, 3), Decimal("0.1")),
                    ReturnObservation(date(2026, 1, 2), Decimal("0.2")),
                ),
            ),
            "UNSORTED_RETURN_DATES",
        ),
    ],
)
def test_rejects_invalid_return_contracts(factory: object, expected_code: str) -> None:
    assert callable(factory)
    with pytest.raises(DomainValidationError) as exc_info:
        factory()

    assert exc_info.value.primary_issue.code == expected_code


def test_statistic_matrix_requires_square_symmetric_values() -> None:
    keys = (_key("AAA"), _key("BBB"))
    valid = StatisticMatrix(
        kind=MatrixKind.COVARIANCE,
        keys=keys,
        values=((Decimal("1"), Decimal("0.5")), (Decimal("0.5"), Decimal("2"))),
        frequency=DataFrequency.DAILY,
        method=ReturnMethod.SIMPLE,
        estimator=VarianceEstimator.SAMPLE,
        observation_count=3,
    )

    with pytest.raises(DomainValidationError) as shape_error:
        replace(valid, values=((Decimal("1"),),))
    with pytest.raises(DomainValidationError) as symmetry_error:
        replace(
            valid,
            values=((Decimal("1"), Decimal("0.4")), (Decimal("0.5"), Decimal("2"))),
        )
    with pytest.raises(DomainValidationError) as range_error:
        replace(valid, kind=MatrixKind.CORRELATION, values=((Decimal("1.1"),) * 2,) * 2)
    with pytest.raises(DomainValidationError) as diagonal_error:
        replace(
            valid,
            kind=MatrixKind.CORRELATION,
            values=((Decimal("0.5"), Decimal("0")), (Decimal("0"), Decimal("0.5"))),
        )

    assert shape_error.value.primary_issue.code == "INVALID_STATISTIC_MATRIX_SHAPE"
    assert symmetry_error.value.primary_issue.code == "ASYMMETRIC_STATISTIC_MATRIX"
    assert range_error.value.primary_issue.code == "CORRELATION_OUT_OF_RANGE"
    assert diagonal_error.value.primary_issue.code == "INVALID_CORRELATION_DIAGONAL"


def test_drawdown_contract_reconciles_wealth_and_dates() -> None:
    observation = DrawdownObservation(
        date(2026, 1, 2),
        wealth_index=Decimal("0.9"),
        cumulative_return=Decimal("-0.1"),
        drawdown=Decimal("-0.1"),
    )
    result = DrawdownResult(
        key=_key(),
        method=ReturnMethod.SIMPLE,
        observations=(observation,),
        maximum_drawdown=Decimal("0.1"),
        peak_date=date(2026, 1, 1),
        trough_date=date(2026, 1, 2),
        recovery_date=None,
    )

    assert result.maximum_drawdown == Decimal("0.1")

    with pytest.raises(DomainValidationError) as mismatch_error:
        replace(observation, cumulative_return=Decimal("-0.2"))
    with pytest.raises(DomainValidationError) as date_error:
        replace(result, recovery_date=date(2026, 1, 2))
    with pytest.raises(DomainValidationError) as maximum_error:
        replace(result, maximum_drawdown=Decimal("0.2"))
    assert mismatch_error.value.primary_issue.code == "CUMULATIVE_RETURN_MISMATCH"
    assert date_error.value.primary_issue.code == "INVALID_RECOVERY_DATE"
    assert maximum_error.value.primary_issue.code == "MAXIMUM_DRAWDOWN_MISMATCH"
