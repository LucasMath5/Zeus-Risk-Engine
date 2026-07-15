"""Unit tests for immutable market-data domain contracts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import cast

import pytest

from zeus_risk.domain import (
    Currency,
    DataFrequency,
    DomainValidationError,
    MarketDataIssue,
    MarketDataLoadResult,
    MarketDataMetadata,
    MarketDataSet,
    MissingValuePolicy,
    PriceObservation,
    PriceSeries,
    PriceSeriesKey,
    ValidationIssue,
    ValidationSeverity,
)

HASH = "a" * 64


def _series(
    ticker: str = "ZEUS",
    dates: tuple[date, ...] = (date(2026, 1, 2), date(2026, 1, 5)),
) -> PriceSeries:
    return PriceSeries(
        key=PriceSeriesKey(ticker, Currency("BRL")),
        frequency=DataFrequency.DAILY,
        observations=tuple(
            PriceObservation(observed_on=value, price=Decimal(index + 10))
            for index, value in enumerate(dates)
        ),
    )


def _metadata(series: tuple[PriceSeries, ...]) -> MarketDataMetadata:
    return MarketDataMetadata(
        provider_name="test",
        source_name="synthetic.csv",
        frequency=DataFrequency.DAILY,
        loaded_at=datetime(2026, 1, 10, tzinfo=UTC),
        content_hash=HASH,
        start_date=min(item.start_date for item in series),
        end_date=max(item.end_date for item in series),
        observation_count=sum(len(item.observations) for item in series),
        series_count=len(series),
        missing_value_policy=MissingValuePolicy.ERROR,
    )


def test_normalizes_key_and_exposes_ordered_series_properties() -> None:
    series = _series(" zeus ")

    assert series.key == PriceSeriesKey("ZEUS", Currency("BRL"))
    assert series.start_date == date(2026, 1, 2)
    assert series.end_date == date(2026, 1, 5)
    assert series.prices == (Decimal("10"), Decimal("11"))


@pytest.mark.parametrize(
    ("factory", "expected_code"),
    [
        (lambda: PriceSeriesKey("", Currency("BRL")), "EMPTY_TICKER"),
        (
            lambda: PriceSeriesKey(cast(str, 2), Currency("BRL")),
            "INVALID_TICKER_TYPE",
        ),
        (
            lambda: PriceSeriesKey("ZEUS", cast(Currency, "BRL")),
            "INVALID_CURRENCY",
        ),
        (
            lambda: PriceObservation(cast(date, datetime(2026, 1, 2)), Decimal("10")),
            "INVALID_OBSERVATION_DATE",
        ),
        (
            lambda: PriceObservation(date(2026, 1, 2), Decimal("0")),
            "NON_POSITIVE_PRICE",
        ),
        (
            lambda: PriceObservation(date(2026, 1, 2), Decimal("NaN")),
            "NON_FINITE_PRICE",
        ),
    ],
)
def test_rejects_invalid_series_keys_and_observations(
    factory: Callable[[], object],
    expected_code: str,
) -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        factory()

    assert exc_info.value.primary_issue.code == expected_code


def test_rejects_empty_duplicate_and_unsorted_series() -> None:
    key = PriceSeriesKey("ZEUS", Currency("BRL"))
    first = PriceObservation(date(2026, 1, 2), Decimal("10"))
    second = PriceObservation(date(2026, 1, 5), Decimal("11"))

    with pytest.raises(DomainValidationError) as empty_error:
        PriceSeries(key, DataFrequency.DAILY, ())
    with pytest.raises(DomainValidationError) as duplicate_error:
        PriceSeries(key, DataFrequency.DAILY, (first, first))
    with pytest.raises(DomainValidationError) as unsorted_error:
        PriceSeries(key, DataFrequency.DAILY, (second, first))

    assert empty_error.value.primary_issue.code == "EMPTY_PRICE_SERIES"
    assert duplicate_error.value.primary_issue.code == "DUPLICATE_PRICE_DATE"
    assert unsorted_error.value.primary_issue.code == "UNSORTED_PRICE_DATES"


def test_reconciles_dataset_metadata_and_finds_series() -> None:
    first = _series("AAA")
    second = _series("BBB", (date(2026, 1, 3), date(2026, 1, 6)))
    metadata = _metadata((first, second))
    data = MarketDataSet(series=(first, second), metadata=metadata)

    assert data.get_series(first.key) is first
    assert data.metadata.observation_count == 4
    assert data.metadata.start_date == date(2026, 1, 2)
    assert data.metadata.end_date == date(2026, 1, 6)

    with pytest.raises(DomainValidationError) as missing_error:
        data.get_series(PriceSeriesKey("MISSING", Currency("BRL")))
    with pytest.raises(DomainValidationError) as invalid_key_error:
        data.get_series(cast(PriceSeriesKey, "ZEUS:BRL"))
    assert missing_error.value.primary_issue.code == "PRICE_SERIES_NOT_FOUND"
    assert invalid_key_error.value.primary_issue.code == "INVALID_PRICE_SERIES_KEY"


def test_rejects_duplicate_series_and_metadata_mismatch() -> None:
    series = _series()
    metadata = _metadata((series,))

    with pytest.raises(DomainValidationError) as duplicate_error:
        MarketDataSet(series=(series, series), metadata=metadata)

    inconsistent = MarketDataMetadata(
        provider_name="test",
        source_name="synthetic.csv",
        frequency=DataFrequency.DAILY,
        loaded_at=datetime(2026, 1, 10, tzinfo=UTC),
        content_hash=HASH,
        start_date=series.start_date,
        end_date=series.end_date,
        observation_count=3,
        series_count=1,
        missing_value_policy=MissingValuePolicy.ERROR,
    )
    with pytest.raises(DomainValidationError) as mismatch_error:
        MarketDataSet(series=(series,), metadata=inconsistent)

    assert duplicate_error.value.primary_issue.code == "DUPLICATE_PRICE_SERIES"
    assert mismatch_error.value.primary_issue.code == "MARKET_DATA_METADATA_MISMATCH"


def test_success_result_accepts_warnings_but_not_errors() -> None:
    series = _series()
    data = MarketDataSet((series,), _metadata((series,)))
    warning = MarketDataIssue(
        ValidationIssue(ValidationSeverity.WARNING, "SYNTHETIC_WARNING", "Synthetic warning")
    )
    result = MarketDataLoadResult(data=data, issues=(warning,))

    assert result.has_warnings

    error = MarketDataIssue(
        ValidationIssue(ValidationSeverity.ERROR, "SYNTHETIC_ERROR", "Synthetic error")
    )
    with pytest.raises(ValueError, match="cannot contain errors"):
        MarketDataLoadResult(data=data, issues=(error,))


@pytest.mark.parametrize(
    "field_name",
    [
        "provider_name",
        "loaded_at",
        "content_hash",
        "date_range",
        "observation_count",
        "series_count",
        "dropped_rows",
    ],
)
def test_rejects_invalid_metadata(field_name: str) -> None:
    valid = _metadata((_series(),))
    factories: dict[str, Callable[[], MarketDataMetadata]] = {
        "provider_name": lambda: replace(valid, provider_name=""),
        "loaded_at": lambda: replace(valid, loaded_at=datetime(2026, 1, 10)),
        "content_hash": lambda: replace(valid, content_hash="bad"),
        "date_range": lambda: replace(
            valid,
            start_date=date(2026, 1, 6),
            end_date=date(2026, 1, 2),
        ),
        "observation_count": lambda: replace(valid, observation_count=0),
        "series_count": lambda: replace(valid, series_count=0),
        "dropped_rows": lambda: replace(valid, dropped_rows=-1),
    }

    with pytest.raises(DomainValidationError):
        factories[field_name]()
