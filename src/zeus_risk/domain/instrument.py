"""Financial instrument domain model."""

from __future__ import annotations

from dataclasses import dataclass

from zeus_risk.domain.currency import Currency
from zeus_risk.domain.enums import AssetClass
from zeus_risk.domain.validation import raise_validation_error


@dataclass(frozen=True, slots=True)
class Instrument:
    """Tradable instrument identified within an asset class and currency."""

    ticker: str
    asset_class: AssetClass
    currency: Currency
    sector: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.ticker, str):
            raise_validation_error(
                "INVALID_TICKER_TYPE",
                "Ticker must be a string.",
                field="ticker",
            )

        normalized_ticker = self.ticker.strip().upper()
        if not normalized_ticker:
            raise_validation_error(
                "EMPTY_TICKER",
                "Ticker must not be empty.",
                field="ticker",
            )
        if not isinstance(self.asset_class, AssetClass):
            raise_validation_error(
                "INVALID_ASSET_CLASS",
                "Asset class must be a supported AssetClass value.",
                field="asset_class",
                item=str(self.asset_class),
            )
        if not isinstance(self.currency, Currency):
            raise_validation_error(
                "INVALID_CURRENCY",
                "Instrument currency must be a Currency value object.",
                field="currency",
                item=str(self.currency),
            )

        normalized_sector = _normalize_sector(self.sector)
        object.__setattr__(self, "ticker", normalized_ticker)
        object.__setattr__(self, "sector", normalized_sector)


def _normalize_sector(sector: str | None) -> str | None:
    if sector is None:
        return None
    if not isinstance(sector, str):
        raise_validation_error(
            "INVALID_SECTOR_TYPE",
            "Sector must be a string or None.",
            field="sector",
        )

    normalized = sector.strip()
    return normalized or None
