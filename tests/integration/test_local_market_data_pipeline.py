"""Integration tests for provider, alignment, and local cache composition."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from zeus_risk.market_data import (
    AlignmentPolicy,
    CsvMarketDataProvider,
    JsonMarketDataCache,
    align_price_series,
)


def test_loads_versioned_fixture_aligns_and_caches(tmp_path: Path) -> None:
    source = Path("tests/fixtures/market_data/valid_prices.csv")
    provider = CsvMarketDataProvider(
        source,
        clock=lambda: datetime(2026, 1, 10, tzinfo=UTC),
    )

    result = provider.load()
    table = align_price_series(result.data.series, AlignmentPolicy.INTERSECTION)
    cache = JsonMarketDataCache(tmp_path / "cache")
    cache.store(result)
    restored = cache.load(result.data.metadata.content_hash)

    assert result.data.metadata.series_count == 2
    assert result.data.metadata.observation_count == 6
    assert len(table.rows) == 3
    assert table.rows[0].prices == (Decimal("100.00"), Decimal("50.00"))
    assert restored == result


def test_packaged_market_data_sample_is_valid() -> None:
    source = Path("assets/samples/market_prices.csv")

    result = CsvMarketDataProvider(source).load()

    assert result.data.metadata.source_name == str(source)
    assert result.data.metadata.series_count == 2
    assert result.data.metadata.observation_count == 6
    assert not result.issues
