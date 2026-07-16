"""Immutable contracts for historical market-risk measures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from enum import StrEnum

from zeus_risk.domain.analytics import ReturnMethod
from zeus_risk.domain.market_data import DataFrequency, PriceSeriesKey
from zeus_risk.domain.validation import raise_validation_error

_ZERO = Decimal("0")
_ONE = Decimal("1")
_RISK_PRECISION = 34


class EmpiricalQuantileMethod(StrEnum):
    """Supported empirical-quantile convention."""

    NEAREST_RANK = "nearest_rank"


class LossConvention(StrEnum):
    """Sign convention applied to historical scenarios."""

    NEGATIVE_RETURN = "loss_equals_negative_return"


class RiskMeasureUnit(StrEnum):
    """Unit attached to a risk-measure value."""

    RELATIVE_RETURN = "relative_return"


@dataclass(frozen=True, slots=True)
class HistoricalVaRConfiguration:
    """Validated parameters for deterministic historical VaR."""

    confidence_level: Decimal
    horizon_days: int = 1
    window: int = 252
    quantile_method: EmpiricalQuantileMethod = EmpiricalQuantileMethod.NEAREST_RANK

    def __post_init__(self) -> None:
        _validate_finite_decimal(self.confidence_level, field="confidence_level")
        if not (_ZERO < self.confidence_level < _ONE):
            raise_validation_error(
                "INVALID_VAR_CONFIDENCE_LEVEL",
                "Historical VaR confidence level must be strictly between 0 and 1.",
                field="confidence_level",
                item=str(self.confidence_level),
            )
        _validate_positive_int(
            self.horizon_days,
            field="horizon_days",
            code="INVALID_VAR_HORIZON",
        )
        _validate_positive_int(
            self.window,
            field="window",
            code="INVALID_VAR_WINDOW",
        )
        if not isinstance(self.quantile_method, EmpiricalQuantileMethod):
            raise_validation_error(
                "INVALID_VAR_QUANTILE_METHOD",
                "Historical VaR requires a supported empirical quantile method.",
                field="quantile_method",
                item=str(self.quantile_method),
            )
        if self.window < self.minimum_sample_size:
            raise_validation_error(
                "INSUFFICIENT_VAR_TAIL_OBSERVATIONS",
                "Historical window is too short to resolve the requested confidence tail.",
                field="window",
                item=f"required={self.minimum_sample_size},actual={self.window}",
            )

    @property
    def minimum_sample_size(self) -> int:
        """Return the minimum sample with at least one observation beyond the quantile."""

        numerator, denominator = self.confidence_level.as_integer_ratio()
        tail_numerator = denominator - numerator
        return (denominator + tail_numerator - 1) // tail_numerator

    def rank_for(self, observation_count: int) -> int:
        """Return the one-based nearest rank for a valid sample size."""

        _validate_positive_int(
            observation_count,
            field="observation_count",
            code="INVALID_VAR_SAMPLE_SIZE",
        )
        numerator, denominator = self.confidence_level.as_integer_ratio()
        return (numerator * observation_count + denominator - 1) // denominator


@dataclass(frozen=True, slots=True)
class HistoricalLossObservation:
    """One horizon scenario expressed using the positive-loss convention."""

    start_date: date
    end_date: date
    value: Decimal

    def __post_init__(self) -> None:
        _validate_date(self.start_date, field="start_date")
        _validate_date(self.end_date, field="end_date")
        if self.start_date >= self.end_date:
            raise_validation_error(
                "INVALID_VAR_SCENARIO_DATES",
                "Historical loss scenario start date must precede its end date.",
                field="start_date",
            )
        _validate_finite_decimal(self.value, field="value")


@dataclass(frozen=True, slots=True)
class HistoricalVaRResult:
    """Auditable historical VaR threshold and the effective scenario sample."""

    key: PriceSeriesKey
    frequency: DataFrequency
    return_method: ReturnMethod
    configuration: HistoricalVaRConfiguration
    losses: tuple[HistoricalLossObservation, ...]
    quantile_rank: int
    quantile_loss: Decimal
    value_at_risk: Decimal
    reference_date: date
    loss_convention: LossConvention = LossConvention.NEGATIVE_RETURN
    unit: RiskMeasureUnit = RiskMeasureUnit.RELATIVE_RETURN

    def __post_init__(self) -> None:
        if not isinstance(self.key, PriceSeriesKey):
            raise_validation_error(
                "INVALID_VAR_KEY",
                "Historical VaR result requires a PriceSeriesKey.",
                field="key",
            )
        if not isinstance(self.frequency, DataFrequency):
            raise_validation_error(
                "INVALID_VAR_FREQUENCY",
                "Historical VaR result requires a supported frequency.",
                field="frequency",
            )
        if not isinstance(self.return_method, ReturnMethod):
            raise_validation_error(
                "INVALID_VAR_RETURN_METHOD",
                "Historical VaR result requires a supported return method.",
                field="return_method",
            )
        if not isinstance(self.configuration, HistoricalVaRConfiguration):
            raise_validation_error(
                "INVALID_VAR_CONFIGURATION",
                "Historical VaR result requires a validated configuration.",
                field="configuration",
            )
        if (
            not isinstance(self.losses, tuple)
            or not self.losses
            or any(not isinstance(item, HistoricalLossObservation) for item in self.losses)
        ):
            raise_validation_error(
                "INVALID_VAR_LOSS_SAMPLE",
                "Historical VaR result requires a non-empty loss sample.",
                field="losses",
            )
        if len(self.losses) != self.configuration.window:
            raise_validation_error(
                "VAR_WINDOW_MISMATCH",
                "Historical VaR sample size must equal the configured window.",
                field="losses",
            )
        end_dates = tuple(item.end_date for item in self.losses)
        start_dates = tuple(item.start_date for item in self.losses)
        if end_dates != tuple(sorted(set(end_dates))) or start_dates != tuple(
            sorted(set(start_dates))
        ):
            raise_validation_error(
                "UNSORTED_VAR_SCENARIOS",
                "Historical loss scenarios must be unique and chronological.",
                field="losses",
            )
        _validate_positive_int(
            self.quantile_rank,
            field="quantile_rank",
            code="INVALID_VAR_QUANTILE_RANK",
        )
        expected_rank = self.configuration.rank_for(len(self.losses))
        if self.quantile_rank != expected_rank:
            raise_validation_error(
                "VAR_QUANTILE_RANK_MISMATCH",
                "Historical VaR quantile rank does not match its configuration.",
                field="quantile_rank",
            )
        _validate_finite_decimal(self.quantile_loss, field="quantile_loss")
        _validate_finite_decimal(self.value_at_risk, field="value_at_risk")
        expected_quantile = self.ranked_losses[self.quantile_rank - 1].value
        if self.quantile_loss != expected_quantile:
            raise_validation_error(
                "VAR_QUANTILE_MISMATCH",
                "Historical VaR quantile must reconcile with the effective loss sample.",
                field="quantile_loss",
            )
        expected_var = max(self.quantile_loss, _ZERO)
        if self.value_at_risk != expected_var:
            raise_validation_error(
                "VAR_VALUE_MISMATCH",
                "Historical VaR must be the non-negative reported loss threshold.",
                field="value_at_risk",
            )
        _validate_date(self.reference_date, field="reference_date")
        if self.reference_date != self.losses[-1].end_date:
            raise_validation_error(
                "VAR_REFERENCE_DATE_MISMATCH",
                "Historical VaR reference date must equal the last scenario end date.",
                field="reference_date",
            )
        if self.loss_convention is not LossConvention.NEGATIVE_RETURN:
            raise_validation_error(
                "INVALID_VAR_LOSS_CONVENTION",
                "Historical VaR uses loss equal to negative return.",
                field="loss_convention",
            )
        if self.unit is not RiskMeasureUnit.RELATIVE_RETURN:
            raise_validation_error(
                "INVALID_VAR_UNIT",
                "Phase 7 historical VaR supports relative-return units only.",
                field="unit",
            )

    @property
    def observation_count(self) -> int:
        """Return the number of horizon scenarios in the effective sample."""

        return len(self.losses)

    @property
    def sample_start_date(self) -> date:
        """Return the start boundary of the earliest included horizon scenario."""

        return self.losses[0].start_date

    @property
    def sample_end_date(self) -> date:
        """Return the end boundary of the latest included horizon scenario."""

        return self.losses[-1].end_date

    @property
    def ranked_losses(self) -> tuple[HistoricalLossObservation, ...]:
        """Return losses by ascending value with chronological tie-breaking."""

        return tuple(
            sorted(
                self.losses,
                key=lambda item: (item.value, item.end_date, item.start_date),
            )
        )


@dataclass(frozen=True, slots=True)
class HistoricalExpectedShortfallResult:
    """Historical tail mean reconciled with one effective VaR result."""

    historical_var: HistoricalVaRResult
    tail_losses: tuple[HistoricalLossObservation, ...]
    tail_mean_loss: Decimal
    expected_shortfall: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.historical_var, HistoricalVaRResult):
            raise_validation_error(
                "INVALID_EXPECTED_SHORTFALL_VAR_RESULT",
                "Historical Expected Shortfall requires a HistoricalVaRResult.",
                field="historical_var",
            )
        if (
            not isinstance(self.tail_losses, tuple)
            or not self.tail_losses
            or any(not isinstance(item, HistoricalLossObservation) for item in self.tail_losses)
        ):
            raise_validation_error(
                "INVALID_EXPECTED_SHORTFALL_TAIL",
                "Historical Expected Shortfall requires a non-empty loss tail.",
                field="tail_losses",
            )
        expected_tail = self.historical_var.ranked_losses[self.historical_var.quantile_rank :]
        if not expected_tail:
            raise_validation_error(
                "EMPTY_EXPECTED_SHORTFALL_TAIL",
                "Historical VaR result does not contain observations beyond its rank.",
                field="tail_losses",
            )
        if self.tail_losses != expected_tail:
            raise_validation_error(
                "EXPECTED_SHORTFALL_TAIL_MISMATCH",
                "Expected Shortfall tail must contain exactly the ranks beyond VaR.",
                field="tail_losses",
            )
        _validate_finite_decimal(self.tail_mean_loss, field="tail_mean_loss")
        _validate_finite_decimal(self.expected_shortfall, field="expected_shortfall")
        with localcontext() as context:
            context.prec = _RISK_PRECISION
            context.rounding = ROUND_HALF_EVEN
            expected_mean = sum((item.value for item in self.tail_losses), _ZERO) / Decimal(
                len(self.tail_losses)
            )
        if self.tail_mean_loss != expected_mean:
            raise_validation_error(
                "EXPECTED_SHORTFALL_MEAN_MISMATCH",
                "Expected Shortfall mean must reconcile with the effective loss tail.",
                field="tail_mean_loss",
            )
        expected_value = max(self.tail_mean_loss, _ZERO)
        if self.expected_shortfall != expected_value:
            raise_validation_error(
                "EXPECTED_SHORTFALL_VALUE_MISMATCH",
                "Expected Shortfall must be the non-negative reported tail mean.",
                field="expected_shortfall",
            )
        if self.expected_shortfall < self.historical_var.value_at_risk:
            raise_validation_error(
                "EXPECTED_SHORTFALL_BELOW_VAR",
                "Expected Shortfall must not be lower than its associated VaR.",
                field="expected_shortfall",
            )

    @property
    def tail_count(self) -> int:
        """Return the number of ranked losses strictly beyond the VaR rank."""

        return len(self.tail_losses)

    @property
    def tail_start_date(self) -> date:
        """Return the earliest scenario start represented in the tail."""

        return min(item.start_date for item in self.tail_losses)

    @property
    def tail_end_date(self) -> date:
        """Return the latest scenario end represented in the tail."""

        return max(item.end_date for item in self.tail_losses)


def _validate_date(value: object, *, field: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise_validation_error(
            "INVALID_VAR_DATE",
            "Historical risk dates must be dates without time components.",
            field=field,
            item=str(value),
        )


def _validate_finite_decimal(value: object, *, field: str) -> None:
    if not isinstance(value, Decimal):
        raise_validation_error(
            "INVALID_VAR_DECIMAL",
            "Historical risk numeric values must be Decimal instances.",
            field=field,
            item=str(value),
        )
    if not value.is_finite():
        raise_validation_error(
            "NON_FINITE_VAR_VALUE",
            "Historical risk numeric values must be finite.",
            field=field,
            item=str(value),
        )


def _validate_positive_int(value: object, *, field: str, code: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise_validation_error(
            code,
            "Historical VaR counts must be positive integers.",
            field=field,
            item=str(value),
        )
