"""Immutable contracts for descriptive portfolio analytics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from zeus_risk.domain.currency import Currency
from zeus_risk.domain.enums import WeightBasis
from zeus_risk.domain.market_data import DataFrequency, PriceSeriesKey
from zeus_risk.domain.portfolio import PositionWeight
from zeus_risk.domain.validation import raise_validation_error

_ZERO = Decimal("0")
_ONE = Decimal("1")
_WEIGHT_TOLERANCE = Decimal("1e-28")


class ReturnMethod(StrEnum):
    """Price-to-return transformation convention."""

    SIMPLE = "simple"
    LOG = "log"


class VarianceEstimator(StrEnum):
    """Denominator convention for variance and covariance."""

    SAMPLE = "sample"
    POPULATION = "population"


class MatrixKind(StrEnum):
    """Statistic represented by a square analytics matrix."""

    COVARIANCE = "covariance"
    CORRELATION = "correlation"


@dataclass(frozen=True, slots=True)
class ReturnObservation:
    """One finite return associated with its period-end date."""

    observed_on: date
    value: Decimal

    def __post_init__(self) -> None:
        _validate_date(self.observed_on, field="observed_on")
        _validate_finite_decimal(self.value, field="value")


@dataclass(frozen=True, slots=True)
class ReturnSeries:
    """Chronological returns for one market series or portfolio."""

    key: PriceSeriesKey
    frequency: DataFrequency
    method: ReturnMethod
    initial_date: date
    observations: tuple[ReturnObservation, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.key, PriceSeriesKey):
            raise_validation_error(
                "INVALID_RETURN_SERIES_KEY",
                "Return series requires a PriceSeriesKey.",
                field="key",
            )
        if not isinstance(self.frequency, DataFrequency):
            raise_validation_error(
                "INVALID_RETURN_FREQUENCY",
                "Return series requires a supported data frequency.",
                field="frequency",
            )
        if not isinstance(self.method, ReturnMethod):
            raise_validation_error(
                "INVALID_RETURN_METHOD",
                "Return series requires a supported return method.",
                field="method",
            )
        _validate_date(self.initial_date, field="initial_date")
        if not isinstance(self.observations, tuple) or not self.observations:
            raise_validation_error(
                "EMPTY_RETURN_SERIES",
                "Return series requires at least one observation.",
                field="observations",
            )
        if any(not isinstance(item, ReturnObservation) for item in self.observations):
            raise_validation_error(
                "INVALID_RETURN_OBSERVATION",
                "Return series accepts only ReturnObservation values.",
                field="observations",
            )

        dates = tuple(item.observed_on for item in self.observations)
        if dates != tuple(sorted(set(dates))):
            raise_validation_error(
                "UNSORTED_RETURN_DATES",
                "Return dates must be unique and strictly increasing.",
                field="observed_on",
            )
        if self.initial_date >= dates[0]:
            raise_validation_error(
                "INVALID_RETURN_INITIAL_DATE",
                "Return initial date must precede the first period-end date.",
                field="initial_date",
            )
        if self.method is ReturnMethod.SIMPLE and any(
            item.value <= -_ONE for item in self.observations
        ):
            raise_validation_error(
                "NON_POSITIVE_RETURN_GROWTH",
                "A simple return must be greater than -1.",
                field="value",
            )

    @property
    def values(self) -> tuple[Decimal, ...]:
        """Return the chronological numeric observations."""

        return tuple(item.value for item in self.observations)

    @property
    def start_date(self) -> date:
        """Return the first period-end date."""

        return self.observations[0].observed_on

    @property
    def end_date(self) -> date:
        """Return the last period-end date."""

        return self.observations[-1].observed_on


@dataclass(frozen=True, slots=True)
class ReturnRow:
    """One aligned period-end date and its finite returns."""

    observed_on: date
    values: tuple[Decimal, ...]

    def __post_init__(self) -> None:
        _validate_date(self.observed_on, field="observed_on")
        if not isinstance(self.values, tuple) or not self.values:
            raise_validation_error(
                "EMPTY_RETURN_ROW",
                "Return row requires at least one value.",
                field="values",
            )
        for value in self.values:
            _validate_finite_decimal(value, field="values")


@dataclass(frozen=True, slots=True)
class ReturnTable:
    """Rectangular returns with columns identified by market-series keys."""

    keys: tuple[PriceSeriesKey, ...]
    frequency: DataFrequency
    method: ReturnMethod
    initial_date: date
    rows: tuple[ReturnRow, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.keys, tuple) or not self.keys:
            raise_validation_error(
                "EMPTY_RETURN_KEYS",
                "Return table requires at least one series key.",
                field="keys",
            )
        if any(not isinstance(key, PriceSeriesKey) for key in self.keys):
            raise_validation_error(
                "INVALID_RETURN_SERIES_KEY",
                "Return table accepts only PriceSeriesKey values.",
                field="keys",
            )
        if len(set(self.keys)) != len(self.keys):
            raise_validation_error(
                "DUPLICATE_RETURN_SERIES",
                "Return table contains duplicate series keys.",
                field="keys",
            )
        if not isinstance(self.frequency, DataFrequency):
            raise_validation_error(
                "INVALID_RETURN_FREQUENCY",
                "Return table requires a supported data frequency.",
                field="frequency",
            )
        if not isinstance(self.method, ReturnMethod):
            raise_validation_error(
                "INVALID_RETURN_METHOD",
                "Return table requires a supported return method.",
                field="method",
            )
        _validate_date(self.initial_date, field="initial_date")
        if not isinstance(self.rows, tuple) or not self.rows:
            raise_validation_error(
                "EMPTY_RETURN_TABLE",
                "Return table requires at least one row.",
                field="rows",
            )
        if any(not isinstance(row, ReturnRow) for row in self.rows):
            raise_validation_error(
                "INVALID_RETURN_ROW",
                "Return table accepts only ReturnRow values.",
                field="rows",
            )
        if any(len(row.values) != len(self.keys) for row in self.rows):
            raise_validation_error(
                "RETURN_TABLE_WIDTH_MISMATCH",
                "Every return row must match the number of series keys.",
                field="rows",
            )

        dates = tuple(row.observed_on for row in self.rows)
        if dates != tuple(sorted(set(dates))):
            raise_validation_error(
                "UNSORTED_RETURN_DATES",
                "Return-table dates must be unique and strictly increasing.",
                field="observed_on",
            )
        if self.initial_date >= dates[0]:
            raise_validation_error(
                "INVALID_RETURN_INITIAL_DATE",
                "Return initial date must precede the first period-end date.",
                field="initial_date",
            )
        if self.method is ReturnMethod.SIMPLE and any(
            value <= -_ONE for row in self.rows for value in row.values
        ):
            raise_validation_error(
                "NON_POSITIVE_RETURN_GROWTH",
                "A simple return must be greater than -1.",
                field="values",
            )

    @property
    def observation_count(self) -> int:
        """Return the number of common return periods."""

        return len(self.rows)

    def series(self, key: PriceSeriesKey) -> ReturnSeries:
        """Extract one column as a return series."""

        if not isinstance(key, PriceSeriesKey):
            raise_validation_error(
                "INVALID_RETURN_SERIES_KEY",
                "Return-table lookup requires a PriceSeriesKey.",
                field="key",
            )
        if key not in self.keys:
            raise_validation_error(
                "RETURN_SERIES_NOT_FOUND",
                "Requested return series is not present in the table.",
                field="key",
                item=f"{key.ticker}:{key.currency.code}",
            )
        index = self.keys.index(key)
        return ReturnSeries(
            key=key,
            frequency=self.frequency,
            method=self.method,
            initial_date=self.initial_date,
            observations=tuple(
                ReturnObservation(row.observed_on, row.values[index]) for row in self.rows
            ),
        )


@dataclass(frozen=True, slots=True)
class DescriptiveStatistics:
    """Moments and volatility for one return series."""

    key: PriceSeriesKey
    frequency: DataFrequency
    method: ReturnMethod
    estimator: VarianceEstimator
    observation_count: int
    mean: Decimal
    variance: Decimal
    volatility: Decimal
    annualization_factor: Decimal
    annualized_volatility: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.key, PriceSeriesKey):
            raise_validation_error(
                "INVALID_STATISTICS_KEY",
                "Statistics require a PriceSeriesKey.",
                field="key",
            )
        if not isinstance(self.frequency, DataFrequency):
            raise_validation_error(
                "INVALID_RETURN_FREQUENCY",
                "Statistics require a supported data frequency.",
                field="frequency",
            )
        if not isinstance(self.method, ReturnMethod):
            raise_validation_error(
                "INVALID_RETURN_METHOD",
                "Statistics require a supported return method.",
                field="method",
            )
        if not isinstance(self.estimator, VarianceEstimator):
            raise_validation_error(
                "INVALID_VARIANCE_ESTIMATOR",
                "Statistics require a supported variance estimator.",
                field="estimator",
            )
        _validate_positive_int(self.observation_count, field="observation_count")
        for field_name in (
            "mean",
            "variance",
            "volatility",
            "annualization_factor",
            "annualized_volatility",
        ):
            _validate_finite_decimal(getattr(self, field_name), field=field_name)
        if self.variance < _ZERO or self.volatility < _ZERO:
            raise_validation_error(
                "NEGATIVE_DISPERSION",
                "Variance and volatility must be non-negative.",
                field="variance",
            )
        if self.annualization_factor <= _ZERO or self.annualized_volatility < _ZERO:
            raise_validation_error(
                "INVALID_ANNUALIZATION",
                "Annualization factor must be positive and volatility non-negative.",
                field="annualization_factor",
            )


@dataclass(frozen=True, slots=True)
class StatisticMatrix:
    """Square covariance or correlation matrix with effective conventions."""

    kind: MatrixKind
    keys: tuple[PriceSeriesKey, ...]
    values: tuple[tuple[Decimal, ...], ...]
    frequency: DataFrequency
    method: ReturnMethod
    estimator: VarianceEstimator
    observation_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MatrixKind):
            raise_validation_error(
                "INVALID_MATRIX_KIND",
                "Statistic matrix requires a supported kind.",
                field="kind",
            )
        if not isinstance(self.keys, tuple) or not self.keys:
            raise_validation_error(
                "EMPTY_STATISTIC_MATRIX",
                "Statistic matrix requires at least one key.",
                field="keys",
            )
        if any(not isinstance(key, PriceSeriesKey) for key in self.keys) or len(
            set(self.keys)
        ) != len(self.keys):
            raise_validation_error(
                "INVALID_STATISTIC_MATRIX_KEYS",
                "Statistic matrix keys must be unique PriceSeriesKey values.",
                field="keys",
            )
        if (
            not isinstance(self.values, tuple)
            or len(self.values) != len(self.keys)
            or any(not isinstance(row, tuple) or len(row) != len(self.keys) for row in self.values)
        ):
            raise_validation_error(
                "INVALID_STATISTIC_MATRIX_SHAPE",
                "Statistic matrix must be square and match its keys.",
                field="values",
            )
        for row in self.values:
            for value in row:
                _validate_finite_decimal(value, field="values")
        if any(
            self.values[row][column] != self.values[column][row]
            for row in range(len(self.keys))
            for column in range(len(self.keys))
        ):
            raise_validation_error(
                "ASYMMETRIC_STATISTIC_MATRIX",
                "Covariance and correlation matrices must be symmetric.",
                field="values",
            )
        if self.kind is MatrixKind.CORRELATION and any(
            value < -_ONE or value > _ONE for row in self.values for value in row
        ):
            raise_validation_error(
                "CORRELATION_OUT_OF_RANGE",
                "Correlation values must be between -1 and 1.",
                field="values",
            )
        diagonal = tuple(self.values[index][index] for index in range(len(self.keys)))
        if self.kind is MatrixKind.COVARIANCE and any(value < _ZERO for value in diagonal):
            raise_validation_error(
                "NEGATIVE_MATRIX_VARIANCE",
                "Covariance-matrix diagonal values must be non-negative.",
                field="values",
            )
        if self.kind is MatrixKind.CORRELATION and any(value != _ONE for value in diagonal):
            raise_validation_error(
                "INVALID_CORRELATION_DIAGONAL",
                "Correlation-matrix diagonal values must equal one.",
                field="values",
            )
        if not isinstance(self.frequency, DataFrequency):
            raise_validation_error(
                "INVALID_RETURN_FREQUENCY",
                "Statistic matrix requires a supported data frequency.",
                field="frequency",
            )
        if not isinstance(self.method, ReturnMethod):
            raise_validation_error(
                "INVALID_RETURN_METHOD",
                "Statistic matrix requires a supported return method.",
                field="method",
            )
        if not isinstance(self.estimator, VarianceEstimator):
            raise_validation_error(
                "INVALID_VARIANCE_ESTIMATOR",
                "Statistic matrix requires a supported estimator.",
                field="estimator",
            )
        _validate_positive_int(self.observation_count, field="observation_count")


@dataclass(frozen=True, slots=True)
class DrawdownObservation:
    """Wealth path and drawdown at one period end."""

    observed_on: date
    wealth_index: Decimal
    cumulative_return: Decimal
    drawdown: Decimal

    def __post_init__(self) -> None:
        _validate_date(self.observed_on, field="observed_on")
        for field_name in ("wealth_index", "cumulative_return", "drawdown"):
            _validate_finite_decimal(getattr(self, field_name), field=field_name)
        if self.wealth_index <= _ZERO:
            raise_validation_error(
                "NON_POSITIVE_WEALTH_INDEX",
                "Wealth index must remain strictly positive.",
                field="wealth_index",
            )
        if self.cumulative_return != self.wealth_index - _ONE:
            raise_validation_error(
                "CUMULATIVE_RETURN_MISMATCH",
                "Cumulative return must equal wealth index minus one.",
                field="cumulative_return",
            )
        if self.drawdown < -_ONE or self.drawdown > _ZERO:
            raise_validation_error(
                "DRAWDOWN_OUT_OF_RANGE",
                "Drawdown must be between -1 and 0.",
                field="drawdown",
            )


@dataclass(frozen=True, slots=True)
class DrawdownResult:
    """Complete wealth path and the largest peak-to-trough loss magnitude."""

    key: PriceSeriesKey
    method: ReturnMethod
    observations: tuple[DrawdownObservation, ...]
    maximum_drawdown: Decimal
    peak_date: date
    trough_date: date
    recovery_date: date | None

    def __post_init__(self) -> None:
        if not isinstance(self.key, PriceSeriesKey):
            raise_validation_error(
                "INVALID_DRAWDOWN_KEY",
                "Drawdown result requires a PriceSeriesKey.",
                field="key",
            )
        if not isinstance(self.method, ReturnMethod):
            raise_validation_error(
                "INVALID_RETURN_METHOD",
                "Drawdown result requires a supported return method.",
                field="method",
            )
        if (
            not isinstance(self.observations, tuple)
            or not self.observations
            or any(not isinstance(item, DrawdownObservation) for item in self.observations)
        ):
            raise_validation_error(
                "INVALID_DRAWDOWN_OBSERVATIONS",
                "Drawdown result requires non-empty DrawdownObservation values.",
                field="observations",
            )
        dates = tuple(item.observed_on for item in self.observations)
        if dates != tuple(sorted(set(dates))):
            raise_validation_error(
                "UNSORTED_DRAWDOWN_DATES",
                "Drawdown observation dates must be unique and increasing.",
                field="observations",
            )
        _validate_finite_decimal(self.maximum_drawdown, field="maximum_drawdown")
        if self.maximum_drawdown < _ZERO or self.maximum_drawdown >= _ONE:
            raise_validation_error(
                "MAXIMUM_DRAWDOWN_OUT_OF_RANGE",
                "Maximum drawdown must be a magnitude between 0 and 1.",
                field="maximum_drawdown",
            )
        observed_maximum = max(item.drawdown.copy_negate() for item in self.observations)
        if self.maximum_drawdown != observed_maximum:
            raise_validation_error(
                "MAXIMUM_DRAWDOWN_MISMATCH",
                "Maximum drawdown must reconcile with the observed path.",
                field="maximum_drawdown",
            )
        _validate_date(self.peak_date, field="peak_date")
        _validate_date(self.trough_date, field="trough_date")
        if self.peak_date > self.trough_date:
            raise_validation_error(
                "INVALID_DRAWDOWN_DATES",
                "Drawdown peak must not follow its trough.",
                field="peak_date",
            )
        if self.recovery_date is not None:
            _validate_date(self.recovery_date, field="recovery_date")
            if self.recovery_date <= self.trough_date:
                raise_validation_error(
                    "INVALID_RECOVERY_DATE",
                    "Recovery date must follow the drawdown trough.",
                    field="recovery_date",
                )


@dataclass(frozen=True, slots=True)
class ConcentrationResult:
    """Gross-weight Herfindahl concentration for one portfolio currency."""

    currency: Currency
    weights: tuple[PositionWeight, ...]
    herfindahl_index: Decimal
    effective_positions: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.currency, Currency):
            raise_validation_error(
                "INVALID_CONCENTRATION_CURRENCY",
                "Concentration result requires a Currency.",
                field="currency",
            )
        if (
            not isinstance(self.weights, tuple)
            or not self.weights
            or any(not isinstance(item, PositionWeight) for item in self.weights)
        ):
            raise_validation_error(
                "INVALID_CONCENTRATION_WEIGHTS",
                "Concentration result requires position weights.",
                field="weights",
            )
        if any(
            item.currency != self.currency or item.basis is not WeightBasis.GROSS
            for item in self.weights
        ):
            raise_validation_error(
                "CONCENTRATION_REQUIRES_GROSS_WEIGHTS",
                "Concentration requires gross weights in one currency.",
                field="weights",
            )
        weight_sum = sum((item.weight for item in self.weights), _ZERO)
        if abs(weight_sum - _ONE) > _WEIGHT_TOLERANCE:
            raise_validation_error(
                "INVALID_CONCENTRATION_WEIGHT_SUM",
                "Gross concentration weights must sum to one.",
                field="weights",
            )
        for field_name in ("herfindahl_index", "effective_positions"):
            _validate_finite_decimal(getattr(self, field_name), field=field_name)
        if not (_ZERO < self.herfindahl_index <= _ONE) or self.effective_positions < _ONE:
            raise_validation_error(
                "INVALID_CONCENTRATION_RESULT",
                "Concentration must satisfy 0 < HHI <= 1 and effective positions >= 1.",
                field="herfindahl_index",
            )


def _validate_date(value: object, *, field: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise_validation_error(
            "INVALID_ANALYTICS_DATE",
            "Analytics dates must be dates without time components.",
            field=field,
            item=str(value),
        )


def _validate_finite_decimal(value: object, *, field: str) -> None:
    if not isinstance(value, Decimal):
        raise_validation_error(
            "INVALID_ANALYTICS_DECIMAL",
            "Analytics numeric values must be Decimal instances.",
            field=field,
            item=str(value),
        )
    if not value.is_finite():
        raise_validation_error(
            "NON_FINITE_ANALYTICS_VALUE",
            "Analytics numeric values must be finite.",
            field=field,
            item=str(value),
        )


def _validate_positive_int(value: object, *, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise_validation_error(
            "INVALID_ANALYTICS_COUNT",
            "Analytics counts must be positive integers.",
            field=field,
            item=str(value),
        )
