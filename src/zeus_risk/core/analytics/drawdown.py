"""Wealth paths, drawdowns, and maximum drawdown episodes."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from zeus_risk.core.analytics._decimal import analytics_context
from zeus_risk.domain import (
    DrawdownObservation,
    DrawdownResult,
    ReturnMethod,
    ReturnSeries,
)
from zeus_risk.exceptions.analytics import raise_analytics_error

_ZERO = Decimal("0")
_ONE = Decimal("1")


def calculate_drawdown(returns: ReturnSeries) -> DrawdownResult:
    """Build a wealth index and identify the largest peak-to-trough loss."""

    if not isinstance(returns, ReturnSeries):
        raise_analytics_error(
            "INVALID_RETURN_SERIES",
            "Drawdown calculation requires a ReturnSeries.",
            field="returns",
        )

    wealth = _ONE
    peak_wealth = _ONE
    peak_date = returns.initial_date
    maximum_drawdown = _ZERO
    maximum_peak_date = returns.initial_date
    maximum_peak_wealth = _ONE
    trough_date = returns.initial_date
    path: list[DrawdownObservation] = []

    with analytics_context():
        for observation in returns.observations:
            wealth *= _growth_factor(observation.value, returns.method)
            if wealth > peak_wealth:
                peak_wealth = wealth
                peak_date = observation.observed_on
            drawdown = wealth / peak_wealth - _ONE
            path.append(
                DrawdownObservation(
                    observed_on=observation.observed_on,
                    wealth_index=wealth,
                    cumulative_return=wealth - _ONE,
                    drawdown=drawdown,
                )
            )
            magnitude = -drawdown
            if magnitude > maximum_drawdown:
                maximum_drawdown = magnitude
                maximum_peak_date = peak_date
                maximum_peak_wealth = peak_wealth
                trough_date = observation.observed_on

    recovery_date = _find_recovery(
        tuple(path),
        trough_date=trough_date,
        peak_wealth=maximum_peak_wealth,
        has_drawdown=maximum_drawdown > _ZERO,
    )
    return DrawdownResult(
        key=returns.key,
        method=returns.method,
        observations=tuple(path),
        maximum_drawdown=maximum_drawdown,
        peak_date=maximum_peak_date,
        trough_date=trough_date,
        recovery_date=recovery_date,
    )


def _growth_factor(value: Decimal, method: ReturnMethod) -> Decimal:
    if method is ReturnMethod.SIMPLE:
        return _ONE + value
    return value.exp()


def _find_recovery(
    path: tuple[DrawdownObservation, ...],
    *,
    trough_date: date,
    peak_wealth: Decimal,
    has_drawdown: bool,
) -> date | None:
    if not has_drawdown:
        return None
    return next(
        (
            observation.observed_on
            for observation in path
            if observation.observed_on > trough_date and observation.wealth_index >= peak_wealth
        ),
        None,
    )
