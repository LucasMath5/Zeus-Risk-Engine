"""Unit tests for the versioned local market-data cache."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest

from zeus_risk.domain import (
    Currency,
    DataFrequency,
    MarketDataIssue,
    MarketDataLoadResult,
    MarketDataMetadata,
    MarketDataSet,
    MissingValuePolicy,
    PriceObservation,
    PriceSeries,
    PriceSeriesKey,
    ValidationIssue,
    ValidationSeverity,
)
from zeus_risk.exceptions import MarketDataError
from zeus_risk.market_data import JsonMarketDataCache

HASH = "b" * 64


def _result() -> MarketDataLoadResult:
    series = PriceSeries(
        key=PriceSeriesKey("ZEUS", Currency("BRL")),
        frequency=DataFrequency.DAILY,
        observations=(
            PriceObservation(date(2026, 1, 2), Decimal("10.50")),
            PriceObservation(date(2026, 1, 5), Decimal("11.25")),
        ),
    )
    metadata = MarketDataMetadata(
        provider_name="csv-local",
        source_name="prices.csv",
        frequency=DataFrequency.DAILY,
        loaded_at=datetime(2026, 1, 10, tzinfo=UTC),
        content_hash=HASH,
        start_date=series.start_date,
        end_date=series.end_date,
        observation_count=2,
        series_count=1,
        missing_value_policy=MissingValuePolicy.DROP,
        dropped_rows=1,
    )
    warning = MarketDataIssue(
        issue=ValidationIssue(
            ValidationSeverity.WARNING,
            "MISSING_PRICE_DROPPED",
            "Synthetic dropped price.",
            field="price",
            item="ZEUS",
        ),
        line_number=3,
    )
    return MarketDataLoadResult(
        data=MarketDataSet(series=(series,), metadata=metadata),
        issues=(warning,),
    )


def test_store_and_load_round_trip_preserves_full_result(tmp_path: Path) -> None:
    cache = JsonMarketDataCache(tmp_path / "cache")
    result = _result()

    path = cache.store(result)
    restored = cache.load(HASH)

    assert path == cache.cache_path(HASH)
    assert path.name == f"market-data-v1-{HASH}.json"
    assert restored == result
    assert not tuple(cache.directory.glob("*.tmp"))


def test_missing_cache_entry_returns_none_without_creating_directory(tmp_path: Path) -> None:
    cache = JsonMarketDataCache(tmp_path / "cache")

    assert cache.load(HASH) is None
    assert not cache.directory.exists()


def test_rejects_invalid_cache_key_and_result(tmp_path: Path) -> None:
    cache = JsonMarketDataCache(tmp_path)

    with pytest.raises(MarketDataError) as key_error:
        cache.load("../escape")
    with pytest.raises(MarketDataError) as result_error:
        cache.store(cast(MarketDataLoadResult, object()))

    assert key_error.value.primary_issue.issue.code == "INVALID_CACHE_KEY"
    assert result_error.value.primary_issue.issue.code == "INVALID_CACHE_RESULT"


def test_detects_content_hash_mismatch(tmp_path: Path) -> None:
    cache = JsonMarketDataCache(tmp_path)
    path = cache.store(_result())
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["metadata"]["content_hash"] = "c" * 64
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(MarketDataError) as exc_info:
        cache.load(HASH)

    assert exc_info.value.primary_issue.issue.code == "CACHE_KEY_MISMATCH"


def test_detects_invalid_json_encoding_and_schema(tmp_path: Path) -> None:
    cache = JsonMarketDataCache(tmp_path)
    path = cache.cache_path(HASH)
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(MarketDataError) as json_error:
        cache.load(HASH)

    path.write_bytes(b"\xff\xfe")
    with pytest.raises(MarketDataError) as encoding_error:
        cache.load(HASH)

    path.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
    with pytest.raises(MarketDataError) as schema_error:
        cache.load(HASH)

    assert json_error.value.primary_issue.issue.code == "CACHE_INVALID_JSON"
    assert encoding_error.value.primary_issue.issue.code == "CACHE_INVALID_ENCODING"
    assert schema_error.value.primary_issue.issue.code == "CACHE_SCHEMA_UNSUPPORTED"


def test_detects_invalid_cached_domain_content(tmp_path: Path) -> None:
    cache = JsonMarketDataCache(tmp_path)
    path = cache.store(_result())
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["series"][0]["observations"][0]["price"] = "0"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(MarketDataError) as exc_info:
        cache.load(HASH)

    assert exc_info.value.primary_issue.issue.code == "CACHE_INVALID_CONTENT"


def test_reports_cache_write_error_when_directory_is_a_file(tmp_path: Path) -> None:
    directory = tmp_path / "cache"
    directory.write_text("not a directory", encoding="utf-8")

    with pytest.raises(MarketDataError) as exc_info:
        JsonMarketDataCache(directory).store(_result())

    assert exc_info.value.primary_issue.issue.code == "CACHE_WRITE_ERROR"
