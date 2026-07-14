"""Tests for financial instruments."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from zeus_risk.domain import AssetClass, Currency, DomainValidationError, Instrument


def test_instrument_normalizes_ticker_and_sector() -> None:
    instrument = Instrument(
        ticker=" petr4 ",
        asset_class=AssetClass.EQUITY,
        currency=Currency("brl"),
        sector=" Energy ",
    )

    assert instrument.ticker == "PETR4"
    assert instrument.currency == Currency("BRL")
    assert instrument.sector == "Energy"


def test_instrument_converts_blank_optional_sector_to_none() -> None:
    instrument = Instrument(
        ticker="VALE3",
        asset_class=AssetClass.EQUITY,
        currency=Currency("BRL"),
        sector="   ",
    )

    assert instrument.sector is None


def test_instrument_rejects_empty_ticker() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        Instrument("  ", AssetClass.EQUITY, Currency("BRL"))

    assert exc_info.value.primary_issue.code == "EMPTY_TICKER"


def test_instrument_rejects_invalid_ticker_type() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        Instrument(cast(str, 123), AssetClass.EQUITY, Currency("BRL"))

    assert exc_info.value.primary_issue.code == "INVALID_TICKER_TYPE"


def test_instrument_rejects_invalid_asset_class() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        Instrument("PETR4", cast(AssetClass, "equity"), Currency("BRL"))

    assert exc_info.value.primary_issue.code == "INVALID_ASSET_CLASS"


def test_instrument_rejects_invalid_currency_object() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        Instrument("PETR4", AssetClass.EQUITY, cast(Currency, "BRL"))

    assert exc_info.value.primary_issue.code == "INVALID_CURRENCY"


def test_instrument_rejects_invalid_sector_type() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        Instrument(
            "PETR4",
            AssetClass.EQUITY,
            Currency("BRL"),
            sector=cast(str, 10),
        )

    assert exc_info.value.primary_issue.code == "INVALID_SECTOR_TYPE"


def test_instrument_is_immutable() -> None:
    instrument = Instrument("PETR4", AssetClass.EQUITY, Currency("BRL"))

    attribute = "ticker"
    with pytest.raises(FrozenInstanceError):
        setattr(instrument, attribute, "VALE3")
