"""Tests for the currency value object."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from zeus_risk.domain import Currency, DomainValidationError


def test_currency_normalizes_code() -> None:
    currency = Currency(" brl ")

    assert currency.code == "BRL"
    assert str(currency) == "BRL"
    assert currency == Currency("BRL")


@pytest.mark.parametrize("code", ["", "US", "USDT", "12A", "R$L"])
def test_currency_rejects_invalid_code(code: str) -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        Currency(code)

    assert exc_info.value.primary_issue.code == "INVALID_CURRENCY_CODE"
    assert exc_info.value.primary_issue.field == "currency"


def test_currency_rejects_non_string_code() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        Currency(cast(str, 986))

    assert exc_info.value.primary_issue.code == "INVALID_CURRENCY_TYPE"


def test_currency_is_immutable() -> None:
    currency = Currency("USD")

    attribute = "code"
    with pytest.raises(FrozenInstanceError):
        setattr(currency, attribute, "BRL")
