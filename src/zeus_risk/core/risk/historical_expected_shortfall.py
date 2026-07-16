"""Historical Expected Shortfall reconciled with nearest-rank VaR."""

from __future__ import annotations

from decimal import Decimal

from zeus_risk.core.analytics._decimal import analytics_context
from zeus_risk.core.risk.historical_var import calculate_historical_var
from zeus_risk.domain import (
    HistoricalExpectedShortfallResult,
    HistoricalVaRConfiguration,
    ReturnSeries,
)
from zeus_risk.exceptions.risk import raise_risk_error

_ZERO = Decimal("0")


def calculate_historical_expected_shortfall(
    returns: ReturnSeries,
    configuration: HistoricalVaRConfiguration,
) -> HistoricalExpectedShortfallResult:
    """Average the ranked losses strictly beyond historical VaR's quantile rank."""

    historical_var = calculate_historical_var(returns, configuration)
    tail_losses = historical_var.ranked_losses[historical_var.quantile_rank :]
    if not tail_losses:
        raise_risk_error(
            "EMPTY_EXPECTED_SHORTFALL_TAIL",
            "Historical Expected Shortfall requires observations beyond the VaR rank.",
            field="returns",
        )

    with analytics_context():
        tail_mean_loss = sum((item.value for item in tail_losses), _ZERO) / Decimal(
            len(tail_losses)
        )
        expected_shortfall = max(tail_mean_loss, _ZERO)

    return HistoricalExpectedShortfallResult(
        historical_var=historical_var,
        tail_losses=tail_losses,
        tail_mean_loss=tail_mean_loss,
        expected_shortfall=expected_shortfall,
    )
