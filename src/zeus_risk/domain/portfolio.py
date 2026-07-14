"""Portfolio aggregate, valuation, and position-weight results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from zeus_risk.domain.currency import Currency
from zeus_risk.domain.enums import WeightBasis
from zeus_risk.domain.position import Position
from zeus_risk.domain.validation import (
    DomainValidationError,
    ValidationIssue,
    ValidationSeverity,
    raise_validation_error,
)

_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class PortfolioValuation:
    """Net and gross market values expressed in one currency."""

    currency: Currency
    net_market_value: Decimal
    gross_market_value: Decimal


@dataclass(frozen=True, slots=True)
class PositionWeight:
    """A position's normalized weight under an explicit denominator convention."""

    ticker: str
    currency: Currency
    basis: WeightBasis
    market_value: Decimal
    weight: Decimal


@dataclass(frozen=True, slots=True)
class Portfolio:
    """Immutable collection of unique positions at an optional reference date."""

    name: str
    positions: tuple[Position, ...]
    reference_date: date | None = None

    def __post_init__(self) -> None:
        normalized_name = _validate_name(self.name)
        _validate_positions(self.positions)
        _validate_reference_date(self.reference_date)

        duplicate_issues = _find_duplicate_positions(self.positions)
        if duplicate_issues:
            raise DomainValidationError(*duplicate_issues)

        object.__setattr__(self, "name", normalized_name)

    @property
    def currencies(self) -> tuple[Currency, ...]:
        """Return the portfolio currencies in deterministic code order."""

        unique_currencies = {position.instrument.currency for position in self.positions}
        return tuple(sorted(unique_currencies, key=lambda currency: currency.code))

    @property
    def currency(self) -> Currency:
        """Return the single portfolio currency or reject ambiguous aggregation."""

        selected_currency, _ = self._select_positions(None)
        return selected_currency

    @property
    def market_value(self) -> Decimal:
        """Return single-currency net market value."""

        return self.valuation().net_market_value

    @property
    def gross_market_value(self) -> Decimal:
        """Return single-currency gross market value."""

        return self.valuation().gross_market_value

    def valuation(self, currency: Currency | None = None) -> PortfolioValuation:
        """Calculate net and gross market value for one explicit currency."""

        selected_currency, selected_positions = self._select_positions(currency)
        market_values = tuple(position.market_value for position in selected_positions)
        net_market_value = sum(market_values, _ZERO)
        gross_market_value = sum((abs(value) for value in market_values), _ZERO)
        return PortfolioValuation(
            currency=selected_currency,
            net_market_value=net_market_value,
            gross_market_value=gross_market_value,
        )

    def valuations(self) -> tuple[PortfolioValuation, ...]:
        """Return one valuation per currency without performing FX conversion."""

        return tuple(self.valuation(currency) for currency in self.currencies)

    def weights(
        self,
        basis: WeightBasis = WeightBasis.NET,
        *,
        currency: Currency | None = None,
    ) -> tuple[PositionWeight, ...]:
        """Calculate position weights for one currency and an explicit basis."""

        if not isinstance(basis, WeightBasis):
            raise_validation_error(
                "INVALID_WEIGHT_BASIS",
                "Weight basis must be a WeightBasis value.",
                field="basis",
                item=str(basis),
            )

        selected_currency, selected_positions = self._select_positions(currency)
        valuation = self.valuation(selected_currency)

        if basis is WeightBasis.NET:
            denominator = valuation.net_market_value
            if denominator.is_zero():
                raise_validation_error(
                    "ZERO_NET_MARKET_VALUE",
                    "Net weights are undefined when net market value is zero.",
                    field="basis",
                    item=basis.value,
                )
        else:
            denominator = valuation.gross_market_value

        return tuple(
            PositionWeight(
                ticker=position.instrument.ticker,
                currency=selected_currency,
                basis=basis,
                market_value=position.market_value,
                weight=(
                    position.market_value / denominator
                    if basis is WeightBasis.NET
                    else abs(position.market_value) / denominator
                ),
            )
            for position in selected_positions
        )

    def _select_positions(
        self,
        currency: Currency | None,
    ) -> tuple[Currency, tuple[Position, ...]]:
        if currency is not None and not isinstance(currency, Currency):
            raise_validation_error(
                "INVALID_CURRENCY",
                "Currency filter must be a Currency value object.",
                field="currency",
                item=str(currency),
            )

        if currency is None:
            if len(self.currencies) != 1:
                codes = ", ".join(item.code for item in self.currencies)
                raise_validation_error(
                    "CURRENCY_CONVERSION_REQUIRED",
                    "An explicit currency is required for a multi-currency portfolio.",
                    field="currency",
                    item=codes,
                )
            selected_currency = self.currencies[0]
        else:
            selected_currency = currency

        selected_positions = tuple(
            position
            for position in self.positions
            if position.instrument.currency == selected_currency
        )
        if not selected_positions:
            raise_validation_error(
                "CURRENCY_NOT_FOUND",
                "The requested currency does not exist in the portfolio.",
                field="currency",
                item=selected_currency.code,
            )

        return selected_currency, selected_positions


def _validate_name(name: str) -> str:
    if not isinstance(name, str):
        raise_validation_error(
            "INVALID_PORTFOLIO_NAME_TYPE",
            "Portfolio name must be a string.",
            field="name",
        )

    normalized = name.strip()
    if not normalized:
        raise_validation_error(
            "EMPTY_PORTFOLIO_NAME",
            "Portfolio name must not be empty.",
            field="name",
        )
    return normalized


def _validate_positions(positions: tuple[Position, ...]) -> None:
    if not isinstance(positions, tuple):
        raise_validation_error(
            "INVALID_POSITIONS_TYPE",
            "Portfolio positions must be an immutable tuple.",
            field="positions",
        )
    if not positions:
        raise_validation_error(
            "EMPTY_PORTFOLIO",
            "Portfolio must contain at least one position.",
            field="positions",
        )

    for index, position in enumerate(positions):
        if not isinstance(position, Position):
            raise_validation_error(
                "INVALID_POSITION",
                "Every portfolio item must be a Position.",
                field="positions",
                item=str(index),
            )


def _validate_reference_date(reference_date: date | None) -> None:
    if reference_date is not None and type(reference_date) is not date:
        raise_validation_error(
            "INVALID_REFERENCE_DATE",
            "Reference date must be a date without a time component.",
            field="reference_date",
            item=str(reference_date),
        )


def _find_duplicate_positions(positions: tuple[Position, ...]) -> tuple[ValidationIssue, ...]:
    seen: set[tuple[str, str]] = set()
    issues: list[ValidationIssue] = []

    for position in positions:
        key = (position.instrument.ticker, position.instrument.currency.code)
        if key in seen:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="DUPLICATE_POSITION",
                    message="Ticker and currency identify more than one position.",
                    field="ticker",
                    item=f"{key[0]}:{key[1]}",
                )
            )
        seen.add(key)

    return tuple(issues)
