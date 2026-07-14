"""Tests for long and short portfolio positions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal
from typing import cast

import pytest

from zeus_risk.domain import AssetClass, Currency, DomainValidationError, Instrument, Position


def make_instrument() -> Instrument:
    return Instrument("PETR4", AssetClass.EQUITY, Currency("BRL"), "Energy")


def test_long_position_has_positive_market_value() -> None:
    position = Position(make_instrument(), Decimal("10"), Decimal("25.50"))

    assert position.market_value == Decimal("255.00")


def test_short_position_has_negative_market_value() -> None:
    position = Position(make_instrument(), Decimal("-4"), Decimal("25.50"))

    assert position.market_value == Decimal("-102.00")


def test_position_rejects_invalid_instrument() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        Position(cast(Instrument, object()), Decimal("1"), Decimal("10"))

    assert exc_info.value.primary_issue.code == "INVALID_INSTRUMENT"


@pytest.mark.parametrize(
    ("quantity", "expected_code"),
    [
        (Decimal("0"), "ZERO_QUANTITY"),
        (Decimal("NaN"), "NON_FINITE_QUANTITY"),
        (Decimal("Infinity"), "NON_FINITE_QUANTITY"),
    ],
)
def test_position_rejects_invalid_quantity(quantity: Decimal, expected_code: str) -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        Position(make_instrument(), quantity, Decimal("10"))

    assert exc_info.value.primary_issue.code == expected_code


@pytest.mark.parametrize(
    ("price", "expected_code"),
    [
        (Decimal("0"), "NON_POSITIVE_PRICE"),
        (Decimal("-1"), "NON_POSITIVE_PRICE"),
        (Decimal("NaN"), "NON_FINITE_PRICE"),
        (Decimal("Infinity"), "NON_FINITE_PRICE"),
    ],
)
def test_position_rejects_invalid_price(price: Decimal, expected_code: str) -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        Position(make_instrument(), Decimal("1"), price)

    assert exc_info.value.primary_issue.code == expected_code


def test_position_rejects_float_inputs() -> None:
    with pytest.raises(DomainValidationError) as quantity_error:
        Position(make_instrument(), cast(Decimal, 1.5), Decimal("10"))
    with pytest.raises(DomainValidationError) as price_error:
        Position(make_instrument(), Decimal("1"), cast(Decimal, 10.5))

    assert quantity_error.value.primary_issue.code == "INVALID_QUANTITY_TYPE"
    assert price_error.value.primary_issue.code == "INVALID_PRICE_TYPE"


def test_position_is_immutable() -> None:
    position = Position(make_instrument(), Decimal("1"), Decimal("10"))

    attribute = "price"
    with pytest.raises(FrozenInstanceError):
        setattr(position, attribute, Decimal("11"))
