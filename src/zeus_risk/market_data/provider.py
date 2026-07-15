"""Consumer-facing port for obtaining validated market data."""

from __future__ import annotations

from typing import Protocol

from zeus_risk.domain import MarketDataLoadResult


class MarketDataProvider(Protocol):
    """Minimal provider contract derived from the local loading use case."""

    @property
    def provider_name(self) -> str:
        """Return a stable provider identifier."""

        ...

    def load(self) -> MarketDataLoadResult:
        """Load a complete, validated market-data result."""

        ...
