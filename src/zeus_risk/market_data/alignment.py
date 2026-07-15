"""Deterministic alignment of validated price series."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from zeus_risk.domain import (
    DataFrequency,
    MarketDataIssue,
    PriceSeries,
    PriceSeriesKey,
    ValidationIssue,
    ValidationSeverity,
)
from zeus_risk.domain.position import validate_price
from zeus_risk.exceptions import MarketDataError


class AlignmentPolicy(StrEnum):
    """Date-index policy used to align multiple series."""

    INTERSECTION = "intersection"
    UNION = "union"


@dataclass(frozen=True, slots=True)
class AlignedPriceRow:
    """One aligned date and prices ordered by the table's series keys."""

    observed_on: date
    prices: tuple[Decimal | None, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.observed_on, date) or isinstance(self.observed_on, datetime):
            raise TypeError("observed_on must be a date without time")
        if not isinstance(self.prices, tuple) or not self.prices:
            raise ValueError("prices must be a non-empty tuple")
        for price in self.prices:
            if price is not None:
                validate_price(price)


@dataclass(frozen=True, slots=True)
class AlignedPriceTable:
    """Rectangular date-indexed view of one or more price series."""

    keys: tuple[PriceSeriesKey, ...]
    frequency: DataFrequency
    policy: AlignmentPolicy
    rows: tuple[AlignedPriceRow, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.keys, tuple) or not self.keys:
            raise ValueError("keys must be a non-empty tuple")
        if any(not isinstance(key, PriceSeriesKey) for key in self.keys):
            raise TypeError("keys must contain PriceSeriesKey values")
        if len(set(self.keys)) != len(self.keys):
            raise ValueError("keys must be unique")
        if not isinstance(self.frequency, DataFrequency):
            raise TypeError("frequency must be a DataFrequency")
        if not isinstance(self.policy, AlignmentPolicy):
            raise TypeError("policy must be an AlignmentPolicy")
        if not isinstance(self.rows, tuple) or not self.rows:
            raise ValueError("rows must be a non-empty tuple")
        if any(not isinstance(row, AlignedPriceRow) for row in self.rows):
            raise TypeError("rows must contain AlignedPriceRow values")
        if any(len(row.prices) != len(self.keys) for row in self.rows):
            raise ValueError("each aligned row must match the number of keys")
        dates = tuple(row.observed_on for row in self.rows)
        if dates != tuple(sorted(set(dates))):
            raise ValueError("aligned dates must be unique and increasing")
        if self.policy is AlignmentPolicy.INTERSECTION and any(
            price is None for row in self.rows for price in row.prices
        ):
            raise ValueError("intersection alignment cannot contain missing prices")


def align_price_series(
    series: tuple[PriceSeries, ...],
    policy: AlignmentPolicy,
) -> AlignedPriceTable:
    """Align series without forward-filling or otherwise inventing prices."""

    if not isinstance(series, tuple) or not series:
        raise _alignment_error(
            "EMPTY_ALIGNMENT_INPUT",
            "At least one price series is required for alignment.",
            field="series",
        )
    if any(not isinstance(item, PriceSeries) for item in series):
        raise _alignment_error(
            "INVALID_ALIGNMENT_SERIES",
            "Alignment accepts only PriceSeries values.",
            field="series",
        )
    if not isinstance(policy, AlignmentPolicy):
        raise _alignment_error(
            "INVALID_ALIGNMENT_POLICY",
            "Alignment policy must be intersection or union.",
            field="policy",
        )

    keys = tuple(item.key for item in series)
    if len(set(keys)) != len(keys):
        raise _alignment_error(
            "DUPLICATE_ALIGNMENT_SERIES",
            "Alignment input contains duplicate series keys.",
            field="series",
        )
    frequencies = {item.frequency for item in series}
    if len(frequencies) != 1:
        raise _alignment_error(
            "MIXED_ALIGNMENT_FREQUENCY",
            "All aligned series must use the same frequency.",
            field="frequency",
        )

    date_sets = [set(item.observed_on for item in value.observations) for value in series]
    if policy is AlignmentPolicy.INTERSECTION:
        aligned_dates = set.intersection(*date_sets)
        if not aligned_dates:
            raise _alignment_error(
                "NO_COMMON_PRICE_DATES",
                "Price series do not share an observation date.",
                field="date",
            )
    else:
        aligned_dates = set.union(*date_sets)

    lookups = [
        {observation.observed_on: observation.price for observation in item.observations}
        for item in series
    ]
    rows = tuple(
        AlignedPriceRow(
            observed_on=observed_on,
            prices=tuple(lookup.get(observed_on) for lookup in lookups),
        )
        for observed_on in sorted(aligned_dates)
    )
    return AlignedPriceTable(
        keys=keys,
        frequency=series[0].frequency,
        policy=policy,
        rows=rows,
    )


def _alignment_error(
    code: str,
    message: str,
    *,
    field: str | None = None,
) -> MarketDataError:
    return MarketDataError(
        MarketDataIssue(
            issue=ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code=code,
                message=message,
                field=field,
            )
        )
    )
