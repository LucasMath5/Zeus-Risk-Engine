"""Deterministic historical Value at Risk over validated return series."""

from __future__ import annotations

from decimal import Decimal

from zeus_risk.core.analytics._decimal import analytics_context
from zeus_risk.domain import (
    DataFrequency,
    HistoricalLossObservation,
    HistoricalVaRConfiguration,
    HistoricalVaRResult,
    LossConvention,
    ReturnMethod,
    ReturnSeries,
    RiskMeasureUnit,
)
from zeus_risk.exceptions.risk import raise_risk_error

_ZERO = Decimal("0")
_ONE = Decimal("1")


def calculate_historical_var(
    returns: ReturnSeries,
    configuration: HistoricalVaRConfiguration,
) -> HistoricalVaRResult:
    """Calculate nearest-rank historical VaR from recent rolling scenarios."""

    if not isinstance(returns, ReturnSeries):
        raise_risk_error(
            "INVALID_VAR_RETURN_SERIES",
            "Historical VaR calculation requires a ReturnSeries.",
            field="returns",
        )
    if not isinstance(configuration, HistoricalVaRConfiguration):
        raise_risk_error(
            "INVALID_VAR_CONFIGURATION",
            "Historical VaR calculation requires a validated configuration.",
            field="configuration",
        )
    if returns.frequency is not DataFrequency.DAILY:
        raise_risk_error(
            "UNSUPPORTED_VAR_FREQUENCY",
            "Historical VaR horizon_days currently requires daily return observations.",
            field="frequency",
            item=str(returns.frequency),
        )

    available_scenarios = len(returns.observations) - configuration.horizon_days + 1
    if available_scenarios < configuration.window:
        required_returns = configuration.window + configuration.horizon_days - 1
        raise_risk_error(
            "INSUFFICIENT_HISTORICAL_OBSERVATIONS",
            "Return series is too short for the configured window and horizon.",
            field="returns",
            item=f"required={required_returns},actual={len(returns.observations)}",
        )

    with analytics_context():
        scenarios = _rolling_loss_scenarios(returns, configuration.horizon_days)
        losses = scenarios[-configuration.window :]
        quantile_rank = configuration.rank_for(len(losses))
        quantile_loss = sorted(item.value for item in losses)[quantile_rank - 1]
        value_at_risk = max(quantile_loss, _ZERO)

    return HistoricalVaRResult(
        key=returns.key,
        frequency=returns.frequency,
        return_method=returns.method,
        configuration=configuration,
        losses=losses,
        quantile_rank=quantile_rank,
        quantile_loss=quantile_loss,
        value_at_risk=value_at_risk,
        reference_date=returns.end_date,
        loss_convention=LossConvention.NEGATIVE_RETURN,
        unit=RiskMeasureUnit.RELATIVE_RETURN,
    )


def _rolling_loss_scenarios(
    returns: ReturnSeries,
    horizon_days: int,
) -> tuple[HistoricalLossObservation, ...]:
    scenarios: list[HistoricalLossObservation] = []
    for end_index in range(horizon_days - 1, len(returns.observations)):
        start_index = end_index - horizon_days + 1
        horizon_values = tuple(
            item.value for item in returns.observations[start_index : end_index + 1]
        )
        horizon_return = _aggregate_returns(horizon_values, returns.method)
        start_date = (
            returns.initial_date
            if start_index == 0
            else returns.observations[start_index - 1].observed_on
        )
        scenarios.append(
            HistoricalLossObservation(
                start_date=start_date,
                end_date=returns.observations[end_index].observed_on,
                value=-horizon_return,
            )
        )
    return tuple(scenarios)


def _aggregate_returns(values: tuple[Decimal, ...], method: ReturnMethod) -> Decimal:
    if method is ReturnMethod.LOG:
        return sum(values, _ZERO)

    growth = _ONE
    for value in values:
        growth *= _ONE + value
    return growth - _ONE
