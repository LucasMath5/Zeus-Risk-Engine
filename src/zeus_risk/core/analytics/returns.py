"""Simple, logarithmic, and constant-weight portfolio returns."""

from __future__ import annotations

from decimal import Decimal
from itertools import pairwise

from zeus_risk.core.analytics._decimal import analytics_context
from zeus_risk.domain import (
    DomainValidationError,
    Portfolio,
    PriceSeries,
    PriceSeriesKey,
    ReturnMethod,
    ReturnObservation,
    ReturnRow,
    ReturnSeries,
    ReturnTable,
    WeightBasis,
)
from zeus_risk.exceptions import AnalyticsError
from zeus_risk.exceptions.analytics import raise_analytics_error
from zeus_risk.market_data import AlignedPriceTable

_ZERO = Decimal("0")
_ONE = Decimal("1")
_WEIGHT_TOLERANCE = Decimal("1e-28")


def calculate_return_series(
    prices: PriceSeries,
    method: ReturnMethod,
) -> ReturnSeries:
    """Calculate period-to-period returns for one validated price series."""

    if not isinstance(prices, PriceSeries):
        raise_analytics_error(
            "INVALID_PRICE_SERIES",
            "Return calculation requires a PriceSeries.",
            field="prices",
        )
    _validate_method(method)
    if len(prices.observations) < 2:
        raise_analytics_error(
            "INSUFFICIENT_PRICE_OBSERVATIONS",
            "At least two prices are required to calculate returns.",
            field="prices",
            item=prices.key.ticker,
        )

    with analytics_context():
        observations = tuple(
            ReturnObservation(
                observed_on=current.observed_on,
                value=_price_return(previous.price, current.price, method),
            )
            for previous, current in pairwise(prices.observations)
        )
    return ReturnSeries(
        key=prices.key,
        frequency=prices.frequency,
        method=method,
        initial_date=prices.start_date,
        observations=observations,
    )


def calculate_return_table(
    prices: AlignedPriceTable,
    method: ReturnMethod,
) -> ReturnTable:
    """Calculate aligned returns, rejecting missing prices instead of filling them."""

    if not isinstance(prices, AlignedPriceTable):
        raise_analytics_error(
            "INVALID_ALIGNED_PRICES",
            "Return-table calculation requires an AlignedPriceTable.",
            field="prices",
        )
    _validate_method(method)
    if len(prices.rows) < 2:
        raise_analytics_error(
            "INSUFFICIENT_PRICE_OBSERVATIONS",
            "At least two aligned price rows are required to calculate returns.",
            field="prices",
        )

    complete_rows = _complete_price_rows(prices)
    with analytics_context():
        rows = tuple(
            ReturnRow(
                observed_on=prices.rows[index].observed_on,
                values=tuple(
                    _price_return(previous, current, method)
                    for previous, current in zip(
                        complete_rows[index - 1],
                        complete_rows[index],
                        strict=True,
                    )
                ),
            )
            for index in range(1, len(complete_rows))
        )
    return ReturnTable(
        keys=prices.keys,
        frequency=prices.frequency,
        method=method,
        initial_date=prices.rows[0].observed_on,
        rows=rows,
    )


def calculate_portfolio_return_series(
    returns: ReturnTable,
    portfolio: Portfolio,
) -> ReturnSeries:
    """Calculate returns using constant signed net weights from a portfolio snapshot."""

    if not isinstance(returns, ReturnTable):
        raise_analytics_error(
            "INVALID_RETURN_TABLE",
            "Portfolio-return calculation requires a ReturnTable.",
            field="returns",
        )
    if not isinstance(portfolio, Portfolio):
        raise_analytics_error(
            "INVALID_PORTFOLIO",
            "Portfolio-return calculation requires a Portfolio.",
            field="portfolio",
        )

    currencies = {key.currency for key in returns.keys}
    if len(currencies) != 1:
        raise_analytics_error(
            "PORTFOLIO_RETURN_REQUIRES_SINGLE_CURRENCY",
            "Portfolio returns cannot aggregate currencies without explicit FX conversion.",
            field="currency",
        )
    currency = next(iter(currencies))
    try:
        position_weights = portfolio.weights(WeightBasis.NET, currency=currency)
    except DomainValidationError as error:
        raise AnalyticsError(*error.issues) from error

    weights = {PriceSeriesKey(item.ticker, item.currency): item.weight for item in position_weights}
    expected_keys = set(returns.keys)
    actual_keys = set(weights)
    if expected_keys != actual_keys:
        missing = sorted(f"{key.ticker}:{key.currency.code}" for key in expected_keys - actual_keys)
        extra = sorted(f"{key.ticker}:{key.currency.code}" for key in actual_keys - expected_keys)
        detail = ", ".join(
            (*[f"missing={item}" for item in missing], *[f"extra={item}" for item in extra])
        )
        raise_analytics_error(
            "PORTFOLIO_RETURN_SERIES_MISMATCH",
            "Portfolio positions and return-table series must match exactly.",
            field="keys",
            item=detail,
        )
    weight_sum = sum(weights.values(), _ZERO)
    if abs(weight_sum - _ONE) > _WEIGHT_TOLERANCE:
        raise_analytics_error(
            "INVALID_PORTFOLIO_WEIGHT_SUM",
            "Net portfolio weights must sum to one.",
            field="weights",
            item=str(weight_sum),
        )

    ordered_weights = tuple(weights[key] for key in returns.keys)
    with analytics_context():
        observations = tuple(
            ReturnObservation(
                observed_on=row.observed_on,
                value=_portfolio_return(row.values, ordered_weights, returns.method),
            )
            for row in returns.rows
        )
    return ReturnSeries(
        key=PriceSeriesKey(portfolio.name, currency),
        frequency=returns.frequency,
        method=returns.method,
        initial_date=returns.initial_date,
        observations=observations,
    )


def _price_return(previous: Decimal, current: Decimal, method: ReturnMethod) -> Decimal:
    ratio = current / previous
    if method is ReturnMethod.SIMPLE:
        return ratio - _ONE
    return ratio.ln()


def _portfolio_return(
    values: tuple[Decimal, ...],
    weights: tuple[Decimal, ...],
    method: ReturnMethod,
) -> Decimal:
    if method is ReturnMethod.SIMPLE:
        simple_return = sum(
            (weight * value for weight, value in zip(weights, values, strict=True)), _ZERO
        )
    else:
        simple_return = sum(
            (weight * (value.exp() - _ONE) for weight, value in zip(weights, values, strict=True)),
            _ZERO,
        )
    growth_factor = _ONE + simple_return
    if growth_factor <= _ZERO:
        raise_analytics_error(
            "NON_POSITIVE_PORTFOLIO_GROWTH",
            "Leveraged portfolio return produced a non-positive growth factor.",
            field="returns",
            item=str(simple_return),
        )
    if method is ReturnMethod.SIMPLE:
        return simple_return
    return growth_factor.ln()


def _complete_price_rows(prices: AlignedPriceTable) -> tuple[tuple[Decimal, ...], ...]:
    complete: list[tuple[Decimal, ...]] = []
    for row in prices.rows:
        for index, value in enumerate(row.prices):
            if value is None:
                key = prices.keys[index]
                raise_analytics_error(
                    "MISSING_ALIGNED_PRICE",
                    "Analytics require complete aligned prices; no implicit fill is applied.",
                    field="prices",
                    item=f"{key.ticker}:{key.currency.code}:{row.observed_on.isoformat()}",
                )
        complete.append(tuple(value for value in row.prices if value is not None))
    return tuple(complete)


def _validate_method(method: ReturnMethod) -> None:
    if not isinstance(method, ReturnMethod):
        raise_analytics_error(
            "INVALID_RETURN_METHOD",
            "Return method must be simple or log.",
            field="method",
            item=str(method),
        )
