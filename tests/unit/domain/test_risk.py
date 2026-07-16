"""Unit tests for immutable historical-risk contracts."""

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
    EmpiricalQuantileMethod,
    HistoricalLossObservation,
    HistoricalVaRConfiguration,
    HistoricalVaRResult,
    PriceSeriesKey,
    ReturnMethod,
)


def _configuration() -> HistoricalVaRConfiguration:
    return HistoricalVaRConfiguration(Decimal("0.5"), window=2)


def _result() -> HistoricalVaRResult:
    losses = (
        HistoricalLossObservation(date(2026, 1, 1), date(2026, 1, 2), Decimal("0.1")),
        HistoricalLossObservation(date(2026, 1, 2), date(2026, 1, 3), Decimal("0.2")),
    )
    return HistoricalVaRResult(
        key=PriceSeriesKey("ZEUS", Currency("BRL")),
        frequency=DataFrequency.DAILY,
        return_method=ReturnMethod.SIMPLE,
        configuration=_configuration(),
        losses=losses,
        quantile_rank=1,
        quantile_loss=Decimal("0.1"),
        value_at_risk=Decimal("0.1"),
        reference_date=date(2026, 1, 3),
    )


def test_configuration_exposes_exact_tail_resolution_and_rank() -> None:
    configuration = HistoricalVaRConfiguration(Decimal("0.95"), window=20)

    assert configuration.minimum_sample_size == 20
    assert configuration.rank_for(20) == 19
    assert configuration.quantile_method is EmpiricalQuantileMethod.NEAREST_RANK


@pytest.mark.parametrize(
    ("factory", "expected_code"),
    [
        (
            lambda: HistoricalVaRConfiguration(Decimal("0"), window=20),
            "INVALID_VAR_CONFIDENCE_LEVEL",
        ),
        (
            lambda: HistoricalVaRConfiguration(Decimal("NaN"), window=20),
            "NON_FINITE_VAR_VALUE",
        ),
        (
            lambda: HistoricalVaRConfiguration(Decimal("0.5"), horizon_days=0, window=2),
            "INVALID_VAR_HORIZON",
        ),
        (
            lambda: HistoricalVaRConfiguration(Decimal("0.5"), window=0),
            "INVALID_VAR_WINDOW",
        ),
        (
            lambda: HistoricalVaRConfiguration(Decimal("0.95"), window=19),
            "INSUFFICIENT_VAR_TAIL_OBSERVATIONS",
        ),
        (
            lambda: HistoricalVaRConfiguration(
                Decimal("0.5"),
                window=2,
                quantile_method=cast(EmpiricalQuantileMethod, "linear"),
            ),
            "INVALID_VAR_QUANTILE_METHOD",
        ),
    ],
)
def test_rejects_invalid_historical_var_configurations(
    factory: object,
    expected_code: str,
) -> None:
    assert callable(factory)
    with pytest.raises(DomainValidationError) as exc_info:
        factory()

    assert exc_info.value.primary_issue.code == expected_code


def test_loss_observation_requires_ordered_dates_and_finite_decimal() -> None:
    with pytest.raises(DomainValidationError) as date_error:
        HistoricalLossObservation(date(2026, 1, 2), date(2026, 1, 2), Decimal("0.1"))
    with pytest.raises(DomainValidationError) as value_error:
        HistoricalLossObservation(date(2026, 1, 1), date(2026, 1, 2), Decimal("Infinity"))

    assert date_error.value.primary_issue.code == "INVALID_VAR_SCENARIO_DATES"
    assert value_error.value.primary_issue.code == "NON_FINITE_VAR_VALUE"


def test_result_reconciles_sample_rank_quantile_value_and_reference_date() -> None:
    result = _result()

    assert result.observation_count == 2
    assert result.sample_start_date == date(2026, 1, 1)
    assert result.sample_end_date == date(2026, 1, 3)

    invalid_replacements = (
        ({"losses": result.losses[:1]}, "VAR_WINDOW_MISMATCH"),
        ({"quantile_rank": 2}, "VAR_QUANTILE_RANK_MISMATCH"),
        ({"quantile_loss": Decimal("0.2")}, "VAR_QUANTILE_MISMATCH"),
        ({"value_at_risk": Decimal("0.2")}, "VAR_VALUE_MISMATCH"),
        ({"reference_date": date(2026, 1, 4)}, "VAR_REFERENCE_DATE_MISMATCH"),
    )
    for values, expected_code in invalid_replacements:
        with pytest.raises(DomainValidationError) as exc_info:
            replace(result, **values)
        assert exc_info.value.primary_issue.code == expected_code
