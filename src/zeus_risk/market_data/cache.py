"""Versioned JSON cache for validated market-data results."""

from __future__ import annotations

import json
import os
import re
import tempfile
from contextlib import suppress
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

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

_CACHE_SCHEMA_VERSION = 1
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class JsonMarketDataCache:
    """Persist and restore validated data by original source-content hash."""

    def __init__(self, directory: str | Path) -> None:
        if not isinstance(directory, (str, Path)):
            raise _cache_error(
                "INVALID_CACHE_PATH",
                "Cache directory must be a string or Path.",
                field="directory",
            )
        self._directory = Path(directory)

    @property
    def directory(self) -> Path:
        """Return the configured cache directory without creating it."""

        return self._directory

    def cache_path(self, content_hash: str) -> Path:
        """Return the safe cache path for a validated SHA-256 key."""

        _validate_hash(content_hash)
        return self.directory / f"market-data-v{_CACHE_SCHEMA_VERSION}-{content_hash}.json"

    def store(self, result: MarketDataLoadResult) -> Path:
        """Atomically store one validated provider result."""

        if not isinstance(result, MarketDataLoadResult):
            raise _cache_error(
                "INVALID_CACHE_RESULT",
                "Cache accepts only MarketDataLoadResult values.",
                field="result",
            )
        target = self.cache_path(result.data.metadata.content_hash)
        payload = _encode_result(result)
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        temporary_path: Path | None = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                dir=self.directory,
                prefix=".market-data-",
                suffix=".tmp",
            )
            os.close(descriptor)
            temporary_path = Path(temporary_name)
            temporary_path.write_text(serialized, encoding="utf-8", newline="\n")
            temporary_path.replace(target)
        except OSError as error:
            if temporary_path is not None:
                with suppress(OSError):
                    temporary_path.unlink(missing_ok=True)
            raise _cache_error(
                "CACHE_WRITE_ERROR",
                "Market-data cache could not be written.",
                field="directory",
                item=str(self.directory),
                source_name=str(target),
            ) from error
        return target

    def load(self, content_hash: str) -> MarketDataLoadResult | None:
        """Load and fully validate a cached result, or return None when absent."""

        target = self.cache_path(content_hash)
        try:
            if not target.exists():
                return None
            serialized = target.read_text(encoding="utf-8")
        except OSError as error:
            raise _cache_error(
                "CACHE_READ_ERROR",
                "Market-data cache could not be read.",
                field="path",
                item=str(target),
                source_name=str(target),
            ) from error
        except UnicodeDecodeError as error:
            raise _cache_error(
                "CACHE_INVALID_ENCODING",
                "Market-data cache is not valid UTF-8.",
                field="path",
                item=str(target),
                source_name=str(target),
            ) from error

        try:
            payload: object = json.loads(serialized)
        except json.JSONDecodeError as error:
            raise _cache_error(
                "CACHE_INVALID_JSON",
                "Market-data cache does not contain valid JSON.",
                item=str(target),
                source_name=str(target),
            ) from error
        try:
            return _decode_result(payload, expected_hash=content_hash)
        except MarketDataError:
            raise
        except (KeyError, TypeError, ValueError) as error:
            raise _cache_error(
                "CACHE_INVALID_CONTENT",
                "Market-data cache content violates the current schema.",
                item=type(error).__name__,
                source_name=str(target),
            ) from error


def _encode_result(result: MarketDataLoadResult) -> dict[str, object]:
    metadata = result.data.metadata
    return {
        "schema_version": _CACHE_SCHEMA_VERSION,
        "metadata": {
            "provider_name": metadata.provider_name,
            "source_name": metadata.source_name,
            "frequency": metadata.frequency.value,
            "loaded_at": metadata.loaded_at.isoformat(),
            "content_hash": metadata.content_hash,
            "start_date": metadata.start_date.isoformat(),
            "end_date": metadata.end_date.isoformat(),
            "observation_count": metadata.observation_count,
            "series_count": metadata.series_count,
            "missing_value_policy": metadata.missing_value_policy.value,
            "dropped_rows": metadata.dropped_rows,
        },
        "series": [
            {
                "ticker": item.key.ticker,
                "currency": item.key.currency.code,
                "frequency": item.frequency.value,
                "observations": [
                    {
                        "date": observation.observed_on.isoformat(),
                        "price": str(observation.price),
                    }
                    for observation in item.observations
                ],
            }
            for item in result.data.series
        ],
        "issues": [
            {
                "severity": item.issue.severity.value,
                "code": item.issue.code,
                "message": item.issue.message,
                "field": item.issue.field,
                "item": item.issue.item,
                "line_number": item.line_number,
            }
            for item in result.issues
        ],
    }


def _decode_result(payload: object, *, expected_hash: str) -> MarketDataLoadResult:
    root = _require_dict(payload)
    schema_version = _require_int(root, "schema_version")
    if schema_version != _CACHE_SCHEMA_VERSION:
        raise _cache_error(
            "CACHE_SCHEMA_UNSUPPORTED",
            "Market-data cache schema version is not supported.",
            field="schema_version",
            item=str(schema_version),
        )

    metadata_payload = _require_dict(root["metadata"])
    content_hash = _require_str(metadata_payload, "content_hash")
    if content_hash != expected_hash:
        raise _cache_error(
            "CACHE_KEY_MISMATCH",
            "Cache content hash does not match its requested key.",
            field="content_hash",
            item=content_hash,
        )
    metadata = MarketDataMetadata(
        provider_name=_require_str(metadata_payload, "provider_name"),
        source_name=_require_str(metadata_payload, "source_name"),
        frequency=DataFrequency(_require_str(metadata_payload, "frequency")),
        loaded_at=datetime.fromisoformat(_require_str(metadata_payload, "loaded_at")),
        content_hash=content_hash,
        start_date=date.fromisoformat(_require_str(metadata_payload, "start_date")),
        end_date=date.fromisoformat(_require_str(metadata_payload, "end_date")),
        observation_count=_require_int(metadata_payload, "observation_count"),
        series_count=_require_int(metadata_payload, "series_count"),
        missing_value_policy=MissingValuePolicy(
            _require_str(metadata_payload, "missing_value_policy")
        ),
        dropped_rows=_require_int(metadata_payload, "dropped_rows"),
    )

    series_values = _require_list(root, "series")
    series = tuple(_decode_series(value) for value in series_values)
    issue_values = _require_list(root, "issues")
    issues = tuple(_decode_issue(value) for value in issue_values)
    return MarketDataLoadResult(
        data=MarketDataSet(series=series, metadata=metadata),
        issues=issues,
    )


def _decode_series(payload: object) -> PriceSeries:
    value = _require_dict(payload)
    observation_values = _require_list(value, "observations")
    observations = tuple(_decode_observation(item) for item in observation_values)
    return PriceSeries(
        key=PriceSeriesKey(
            ticker=_require_str(value, "ticker"),
            currency=Currency(_require_str(value, "currency")),
        ),
        frequency=DataFrequency(_require_str(value, "frequency")),
        observations=observations,
    )


def _decode_observation(payload: object) -> PriceObservation:
    value = _require_dict(payload)
    return PriceObservation(
        observed_on=date.fromisoformat(_require_str(value, "date")),
        price=Decimal(_require_str(value, "price")),
    )


def _decode_issue(payload: object) -> MarketDataIssue:
    value = _require_dict(payload)
    line_number_value = value.get("line_number")
    if line_number_value is not None and (
        isinstance(line_number_value, bool) or not isinstance(line_number_value, int)
    ):
        raise TypeError("line_number must be an integer or null")
    return MarketDataIssue(
        issue=ValidationIssue(
            severity=ValidationSeverity(_require_str(value, "severity")),
            code=_require_str(value, "code"),
            message=_require_str(value, "message"),
            field=_optional_str(value, "field"),
            item=_optional_str(value, "item"),
        ),
        line_number=line_number_value,
    )


def _require_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise TypeError("value must be an object with string keys")
    return value


def _require_list(value: dict[str, object], key: str) -> list[object]:
    result = value[key]
    if not isinstance(result, list):
        raise TypeError(f"{key} must be a list")
    return result


def _require_str(value: dict[str, object], key: str) -> str:
    result = value[key]
    if not isinstance(result, str):
        raise TypeError(f"{key} must be a string")
    return result


def _optional_str(value: dict[str, object], key: str) -> str | None:
    result = value.get(key)
    if result is not None and not isinstance(result, str):
        raise TypeError(f"{key} must be a string or null")
    return result


def _require_int(value: dict[str, object], key: str) -> int:
    result = value[key]
    if isinstance(result, bool) or not isinstance(result, int):
        raise TypeError(f"{key} must be an integer")
    return result


def _validate_hash(content_hash: str) -> None:
    if not isinstance(content_hash, str) or not _SHA256_PATTERN.fullmatch(content_hash):
        raise _cache_error(
            "INVALID_CACHE_KEY",
            "Cache key must be a lowercase SHA-256 digest.",
            field="content_hash",
        )


def _cache_error(
    code: str,
    message: str,
    *,
    field: str | None = None,
    item: str | None = None,
    source_name: str | None = None,
) -> MarketDataError:
    return MarketDataError(
        MarketDataIssue(
            issue=ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code=code,
                message=message,
                field=field,
                item=item,
            )
        ),
        source_name=source_name,
    )
