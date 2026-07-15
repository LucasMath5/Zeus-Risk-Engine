"""Immutable market-data value objects and result contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from zeus_risk.domain.currency import Currency
from zeus_risk.domain.position import validate_price
from zeus_risk.domain.validation import ValidationIssue, ValidationSeverity, raise_validation_error

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class DataFrequency(StrEnum):
    """Observation frequency supported by the current market-data domain."""

    DAILY = "daily"


class MissingValuePolicy(StrEnum):
    """Explicit treatment for absent prices at an ingestion boundary."""

    ERROR = "error"
    DROP = "drop"


@dataclass(frozen=True, order=True, slots=True)
class PriceSeriesKey:
    """Identity of one price series without requiring an asset taxonomy."""

    ticker: str
    currency: Currency

    def __post_init__(self) -> None:
        if not isinstance(self.ticker, str):
            raise_validation_error(
                "INVALID_TICKER_TYPE",
                "Price-series ticker must be a string.",
                field="ticker",
            )
        ticker = self.ticker.strip().upper()
        if not ticker:
            raise_validation_error(
                "EMPTY_TICKER",
                "Price-series ticker must not be empty.",
                field="ticker",
            )
        if not isinstance(self.currency, Currency):
            raise_validation_error(
                "INVALID_CURRENCY",
                "Price-series currency must be a Currency value object.",
                field="currency",
                item=str(self.currency),
            )
        object.__setattr__(self, "ticker", ticker)


@dataclass(frozen=True, order=True, slots=True)
class PriceObservation:
    """A strictly positive closing price observed on one calendar date."""

    observed_on: date
    price: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.observed_on, date) or isinstance(self.observed_on, datetime):
            raise_validation_error(
                "INVALID_OBSERVATION_DATE",
                "Observation date must be a date without a time component.",
                field="date",
                item=str(self.observed_on),
            )
        validate_price(self.price)


@dataclass(frozen=True, slots=True)
class PriceSeries:
    """Chronologically ordered prices for one ticker and currency."""

    key: PriceSeriesKey
    frequency: DataFrequency
    observations: tuple[PriceObservation, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.key, PriceSeriesKey):
            raise_validation_error(
                "INVALID_PRICE_SERIES_KEY",
                "Price series requires a PriceSeriesKey.",
                field="key",
            )
        if not isinstance(self.frequency, DataFrequency):
            raise_validation_error(
                "INVALID_DATA_FREQUENCY",
                "Price series frequency is not supported.",
                field="frequency",
                item=str(self.frequency),
            )
        if not isinstance(self.observations, tuple) or not self.observations:
            raise_validation_error(
                "EMPTY_PRICE_SERIES",
                "Price series requires at least one observation.",
                field="observations",
                item=self.key.ticker,
            )
        if any(not isinstance(item, PriceObservation) for item in self.observations):
            raise_validation_error(
                "INVALID_PRICE_OBSERVATION",
                "Price series accepts only PriceObservation values.",
                field="observations",
                item=self.key.ticker,
            )

        dates = tuple(item.observed_on for item in self.observations)
        if len(set(dates)) != len(dates):
            raise_validation_error(
                "DUPLICATE_PRICE_DATE",
                "Price series contains a duplicate observation date.",
                field="date",
                item=self.key.ticker,
            )
        if dates != tuple(sorted(dates)):
            raise_validation_error(
                "UNSORTED_PRICE_DATES",
                "Price-series dates must be strictly increasing.",
                field="date",
                item=self.key.ticker,
            )

    @property
    def start_date(self) -> date:
        """Return the first observation date."""

        return self.observations[0].observed_on

    @property
    def end_date(self) -> date:
        """Return the last observation date."""

        return self.observations[-1].observed_on

    @property
    def prices(self) -> tuple[Decimal, ...]:
        """Return prices in chronological order."""

        return tuple(item.price for item in self.observations)


@dataclass(frozen=True, slots=True)
class MarketDataMetadata:
    """Provenance and effective ingestion policy for a market-data set."""

    provider_name: str
    source_name: str
    frequency: DataFrequency
    loaded_at: datetime
    content_hash: str
    start_date: date
    end_date: date
    observation_count: int
    series_count: int
    missing_value_policy: MissingValuePolicy
    dropped_rows: int = 0

    def __post_init__(self) -> None:
        for field_name in ("provider_name", "source_name"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise_validation_error(
                    "INVALID_MARKET_DATA_METADATA",
                    "Market-data metadata text fields must not be empty.",
                    field=field_name,
                )
            object.__setattr__(self, field_name, value.strip())

        if not isinstance(self.frequency, DataFrequency):
            raise_validation_error(
                "INVALID_DATA_FREQUENCY",
                "Metadata frequency is not supported.",
                field="frequency",
            )
        if not isinstance(self.loaded_at, datetime) or self.loaded_at.tzinfo is None:
            raise_validation_error(
                "NAIVE_LOADED_AT",
                "Market-data load time must include a timezone.",
                field="loaded_at",
            )
        if not isinstance(self.content_hash, str) or not _SHA256_PATTERN.fullmatch(
            self.content_hash
        ):
            raise_validation_error(
                "INVALID_CONTENT_HASH",
                "Market-data content hash must be a lowercase SHA-256 digest.",
                field="content_hash",
            )
        if (
            not isinstance(self.start_date, date)
            or isinstance(self.start_date, datetime)
            or not isinstance(self.end_date, date)
            or isinstance(self.end_date, datetime)
            or self.start_date > self.end_date
        ):
            raise_validation_error(
                "INVALID_MARKET_DATA_RANGE",
                "Market-data date range must contain valid ordered dates.",
                field="date",
            )
        if (
            isinstance(self.observation_count, bool)
            or not isinstance(self.observation_count, int)
            or self.observation_count <= 0
            or isinstance(self.series_count, bool)
            or not isinstance(self.series_count, int)
            or self.series_count <= 0
            or isinstance(self.dropped_rows, bool)
            or not isinstance(self.dropped_rows, int)
            or self.dropped_rows < 0
        ):
            raise_validation_error(
                "INVALID_MARKET_DATA_COUNTS",
                "Market-data counts must be positive, with non-negative dropped rows.",
                field="counts",
            )
        if not isinstance(self.missing_value_policy, MissingValuePolicy):
            raise_validation_error(
                "INVALID_MISSING_VALUE_POLICY",
                "Metadata requires a supported missing-value policy.",
                field="missing_value_policy",
            )


@dataclass(frozen=True, slots=True)
class MarketDataIssue:
    """A validation issue optionally located at a physical source line."""

    issue: ValidationIssue
    line_number: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.issue, ValidationIssue):
            raise TypeError("issue must be a ValidationIssue")
        if self.line_number is not None and (
            isinstance(self.line_number, bool)
            or not isinstance(self.line_number, int)
            or self.line_number <= 0
        ):
            raise ValueError("line_number must be a positive integer or None")


@dataclass(frozen=True, slots=True)
class MarketDataSet:
    """Validated price series accompanied by reconciled source metadata."""

    series: tuple[PriceSeries, ...]
    metadata: MarketDataMetadata

    def __post_init__(self) -> None:
        if not isinstance(self.series, tuple) or not self.series:
            raise_validation_error(
                "EMPTY_MARKET_DATA_SET",
                "Market-data set requires at least one price series.",
                field="series",
            )
        if any(not isinstance(item, PriceSeries) for item in self.series):
            raise_validation_error(
                "INVALID_PRICE_SERIES",
                "Market-data set accepts only PriceSeries values.",
                field="series",
            )
        if not isinstance(self.metadata, MarketDataMetadata):
            raise_validation_error(
                "INVALID_MARKET_DATA_METADATA",
                "Market-data set requires MarketDataMetadata.",
                field="metadata",
            )

        keys = tuple(item.key for item in self.series)
        if len(set(keys)) != len(keys):
            raise_validation_error(
                "DUPLICATE_PRICE_SERIES",
                "Market-data set contains duplicate series keys.",
                field="series",
            )
        if any(item.frequency is not self.metadata.frequency for item in self.series):
            raise_validation_error(
                "MIXED_DATA_FREQUENCY",
                "All series must match the metadata frequency.",
                field="frequency",
            )

        observation_count = sum(len(item.observations) for item in self.series)
        start_date = min(item.start_date for item in self.series)
        end_date = max(item.end_date for item in self.series)
        if (
            self.metadata.observation_count != observation_count
            or self.metadata.series_count != len(self.series)
            or self.metadata.start_date != start_date
            or self.metadata.end_date != end_date
        ):
            raise_validation_error(
                "MARKET_DATA_METADATA_MISMATCH",
                "Metadata counts or date range do not match the contained series.",
                field="metadata",
            )

    def get_series(self, key: PriceSeriesKey) -> PriceSeries:
        """Return a series by key or raise a stable domain failure."""

        if not isinstance(key, PriceSeriesKey):
            raise_validation_error(
                "INVALID_PRICE_SERIES_KEY",
                "Market-data lookup requires a PriceSeriesKey.",
                field="key",
            )
        for item in self.series:
            if item.key == key:
                return item
        raise_validation_error(
            "PRICE_SERIES_NOT_FOUND",
            "Requested price series is not present in the data set.",
            field="series",
            item=f"{key.ticker}:{key.currency.code}",
        )


@dataclass(frozen=True, slots=True)
class MarketDataLoadResult:
    """Successful provider output with non-fatal ingestion issues."""

    data: MarketDataSet
    issues: tuple[MarketDataIssue, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.data, MarketDataSet):
            raise TypeError("data must be a MarketDataSet")
        if not isinstance(self.issues, tuple) or any(
            not isinstance(item, MarketDataIssue) for item in self.issues
        ):
            raise TypeError("issues must be a tuple of MarketDataIssue values")
        if any(item.issue.severity is ValidationSeverity.ERROR for item in self.issues):
            raise ValueError("successful market-data results cannot contain errors")

    @property
    def has_warnings(self) -> bool:
        """Return whether ingestion produced any warning."""

        return any(item.issue.severity is ValidationSeverity.WARNING for item in self.issues)
