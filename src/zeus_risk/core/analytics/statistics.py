"""Descriptive statistics, covariance, and correlation for aligned returns."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from zeus_risk.core.analytics._decimal import analytics_context
from zeus_risk.domain import (
    DescriptiveStatistics,
    MatrixKind,
    ReturnSeries,
    ReturnTable,
    StatisticMatrix,
    VarianceEstimator,
)
from zeus_risk.exceptions.analytics import raise_analytics_error

_ZERO = Decimal("0")
_ONE = Decimal("1")
_DEFAULT_ANNUALIZATION_FACTOR = Decimal("252")
_CORRELATION_TOLERANCE = Decimal("1e-28")


def calculate_descriptive_statistics(
    returns: ReturnSeries,
    estimator: VarianceEstimator = VarianceEstimator.SAMPLE,
    *,
    annualization_factor: Decimal = _DEFAULT_ANNUALIZATION_FACTOR,
) -> DescriptiveStatistics:
    """Calculate arithmetic mean, variance, and periodic/annualized volatility."""

    if not isinstance(returns, ReturnSeries):
        raise_analytics_error(
            "INVALID_RETURN_SERIES",
            "Descriptive statistics require a ReturnSeries.",
            field="returns",
        )
    _validate_estimator(estimator)
    _validate_sample_size(len(returns.observations), estimator)
    _validate_annualization_factor(annualization_factor)

    with analytics_context():
        mean = _mean(returns.values)
        variance = _covariance(returns.values, returns.values, mean, mean, estimator)
        volatility = variance.sqrt()
        annualized_volatility = volatility * annualization_factor.sqrt()
    return DescriptiveStatistics(
        key=returns.key,
        frequency=returns.frequency,
        method=returns.method,
        estimator=estimator,
        observation_count=len(returns.observations),
        mean=mean,
        variance=variance,
        volatility=volatility,
        annualization_factor=annualization_factor,
        annualized_volatility=annualized_volatility,
    )


def calculate_covariance_matrix(
    returns: ReturnTable,
    estimator: VarianceEstimator = VarianceEstimator.SAMPLE,
) -> StatisticMatrix:
    """Calculate a symmetric covariance matrix for aligned return columns."""

    _validate_table(returns)
    _validate_estimator(estimator)
    _validate_sample_size(returns.observation_count, estimator)
    columns = _columns(returns)

    with analytics_context():
        means = tuple(_mean(values) for values in columns)
        values = _symmetric_matrix(
            len(columns),
            lambda row, column: _covariance(
                columns[row],
                columns[column],
                means[row],
                means[column],
                estimator,
            ),
        )
    return StatisticMatrix(
        kind=MatrixKind.COVARIANCE,
        keys=returns.keys,
        values=values,
        frequency=returns.frequency,
        method=returns.method,
        estimator=estimator,
        observation_count=returns.observation_count,
    )


def calculate_correlation_matrix(
    returns: ReturnTable,
    estimator: VarianceEstimator = VarianceEstimator.SAMPLE,
) -> StatisticMatrix:
    """Calculate a symmetric correlation matrix or reject zero-variance columns."""

    covariance = calculate_covariance_matrix(returns, estimator)
    variances = tuple(covariance.values[index][index] for index in range(len(returns.keys)))
    for index, variance in enumerate(variances):
        if variance.is_zero():
            key = returns.keys[index]
            raise_analytics_error(
                "ZERO_RETURN_VARIANCE",
                "Correlation is undefined for a constant return series.",
                field="returns",
                item=f"{key.ticker}:{key.currency.code}",
            )

    with analytics_context():
        values = _symmetric_matrix(
            len(returns.keys),
            lambda row, column: (
                _ONE
                if row == column
                else _clamp_correlation(
                    covariance.values[row][column] / (variances[row] * variances[column]).sqrt()
                )
            ),
        )
    return StatisticMatrix(
        kind=MatrixKind.CORRELATION,
        keys=returns.keys,
        values=values,
        frequency=returns.frequency,
        method=returns.method,
        estimator=estimator,
        observation_count=returns.observation_count,
    )


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    return sum(values, _ZERO) / Decimal(len(values))


def _covariance(
    left: tuple[Decimal, ...],
    right: tuple[Decimal, ...],
    left_mean: Decimal,
    right_mean: Decimal,
    estimator: VarianceEstimator,
) -> Decimal:
    denominator = len(left) - 1 if estimator is VarianceEstimator.SAMPLE else len(left)
    numerator = sum(
        (
            (left_value - left_mean) * (right_value - right_mean)
            for left_value, right_value in zip(left, right, strict=True)
        ),
        _ZERO,
    )
    return numerator / Decimal(denominator)


def _columns(returns: ReturnTable) -> tuple[tuple[Decimal, ...], ...]:
    return tuple(
        tuple(row.values[index] for row in returns.rows) for index in range(len(returns.keys))
    )


def _symmetric_matrix(
    size: int,
    calculator: Callable[[int, int], Decimal],
) -> tuple[tuple[Decimal, ...], ...]:
    matrix = [[_ZERO for _ in range(size)] for _ in range(size)]
    for row in range(size):
        for column in range(row, size):
            value = calculator(row, column)
            matrix[row][column] = value
            matrix[column][row] = value
    return tuple(tuple(row) for row in matrix)


def _clamp_correlation(value: Decimal) -> Decimal:
    if value > _ONE and value - _ONE <= _CORRELATION_TOLERANCE:
        return _ONE
    if value < -_ONE and -_ONE - value <= _CORRELATION_TOLERANCE:
        return -_ONE
    return value


def _validate_table(returns: ReturnTable) -> None:
    if not isinstance(returns, ReturnTable):
        raise_analytics_error(
            "INVALID_RETURN_TABLE",
            "Matrix calculation requires a ReturnTable.",
            field="returns",
        )


def _validate_estimator(estimator: VarianceEstimator) -> None:
    if not isinstance(estimator, VarianceEstimator):
        raise_analytics_error(
            "INVALID_VARIANCE_ESTIMATOR",
            "Variance estimator must be sample or population.",
            field="estimator",
            item=str(estimator),
        )


def _validate_sample_size(count: int, estimator: VarianceEstimator) -> None:
    minimum = 2 if estimator is VarianceEstimator.SAMPLE else 1
    if count < minimum:
        raise_analytics_error(
            "INSUFFICIENT_RETURN_OBSERVATIONS",
            "The selected estimator does not have enough return observations.",
            field="returns",
            item=f"required={minimum}, actual={count}",
        )


def _validate_annualization_factor(value: Decimal) -> None:
    if not isinstance(value, Decimal) or not value.is_finite() or value <= _ZERO:
        raise_analytics_error(
            "INVALID_ANNUALIZATION_FACTOR",
            "Annualization factor must be a finite positive Decimal.",
            field="annualization_factor",
            item=str(value),
        )
