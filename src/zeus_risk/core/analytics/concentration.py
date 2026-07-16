"""Gross-weight position concentration analytics."""

from __future__ import annotations

from decimal import Decimal

from zeus_risk.core.analytics._decimal import analytics_context
from zeus_risk.domain import (
    ConcentrationResult,
    Currency,
    DomainValidationError,
    Portfolio,
    WeightBasis,
)
from zeus_risk.exceptions import AnalyticsError
from zeus_risk.exceptions.analytics import raise_analytics_error

_ZERO = Decimal("0")
_ONE = Decimal("1")


def calculate_position_concentration(
    portfolio: Portfolio,
    *,
    currency: Currency | None = None,
) -> ConcentrationResult:
    """Calculate gross-weight HHI and its reciprocal effective-position count."""

    if not isinstance(portfolio, Portfolio):
        raise_analytics_error(
            "INVALID_PORTFOLIO",
            "Concentration calculation requires a Portfolio.",
            field="portfolio",
        )
    if currency is not None and not isinstance(currency, Currency):
        raise_analytics_error(
            "INVALID_CONCENTRATION_CURRENCY",
            "Concentration currency must be a Currency value object.",
            field="currency",
            item=str(currency),
        )
    try:
        weights = portfolio.weights(WeightBasis.GROSS, currency=currency)
    except DomainValidationError as error:
        raise AnalyticsError(*error.issues) from error

    with analytics_context():
        herfindahl_index = sum((item.weight * item.weight for item in weights), _ZERO)
        effective_positions = _ONE / herfindahl_index
    return ConcentrationResult(
        currency=weights[0].currency,
        weights=weights,
        herfindahl_index=herfindahl_index,
        effective_positions=effective_positions,
    )
