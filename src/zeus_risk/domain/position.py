"""Portfolio position domain model."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from zeus_risk.domain.instrument import Instrument
from zeus_risk.domain.validation import raise_validation_error


@dataclass(frozen=True, slots=True)
class Position:
    """A non-zero long or short quantity marked at a strictly positive price."""

    instrument: Instrument
    quantity: Decimal
    price: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.instrument, Instrument):
            raise_validation_error(
                "INVALID_INSTRUMENT",
                "Position instrument must be an Instrument.",
                field="instrument",
            )
        _validate_quantity(self.quantity)
        _validate_price(self.price)

    @property
    def market_value(self) -> Decimal:
        """Return signed market value using the instrument's currency."""

        return self.quantity * self.price


def _validate_quantity(quantity: Decimal) -> None:
    if not isinstance(quantity, Decimal):
        raise_validation_error(
            "INVALID_QUANTITY_TYPE",
            "Quantity must be a Decimal.",
            field="quantity",
            item=str(quantity),
        )
    if not quantity.is_finite():
        raise_validation_error(
            "NON_FINITE_QUANTITY",
            "Quantity must be finite.",
            field="quantity",
            item=str(quantity),
        )
    if quantity.is_zero():
        raise_validation_error(
            "ZERO_QUANTITY",
            "Quantity must be different from zero.",
            field="quantity",
            item=str(quantity),
        )


def _validate_price(price: Decimal) -> None:
    if not isinstance(price, Decimal):
        raise_validation_error(
            "INVALID_PRICE_TYPE",
            "Price must be a Decimal.",
            field="price",
            item=str(price),
        )
    if not price.is_finite():
        raise_validation_error(
            "NON_FINITE_PRICE",
            "Price must be finite.",
            field="price",
            item=str(price),
        )
    if price <= 0:
        raise_validation_error(
            "NON_POSITIVE_PRICE",
            "Price must be strictly positive.",
            field="price",
            item=str(price),
        )
