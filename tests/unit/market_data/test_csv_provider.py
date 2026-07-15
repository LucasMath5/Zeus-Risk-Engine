"""Unit tests for the offline CSV market-data provider."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest

from zeus_risk.domain import MissingValuePolicy
from zeus_risk.exceptions import MarketDataError
from zeus_risk.market_data import CsvMarketDataOptions, CsvMarketDataProvider
from zeus_risk.market_data.provider import MarketDataProvider

VALID_TEXT = """ticker,date,price,currency
AAA,2026-01-02,10.00,BRL
AAA,2026-01-05,11.00,BRL
BBB,2026-01-02,20.00,USD
BBB,2026-01-05,21.00,USD
"""
LOADED_AT = datetime(2026, 1, 10, 12, tzinfo=UTC)


def _write(path: Path, text: str = VALID_TEXT) -> Path:
    path.write_text(text, encoding="utf-8", newline="")
    return path


def _provider(
    path: Path,
    options: CsvMarketDataOptions | None = None,
) -> CsvMarketDataProvider:
    return CsvMarketDataProvider(path, options, clock=lambda: LOADED_AT)


def _load_from_port(provider: MarketDataProvider) -> int:
    return provider.load().data.metadata.series_count


def test_loads_multiple_series_with_reproducible_metadata(tmp_path: Path) -> None:
    path = _write(tmp_path / "prices.csv")
    provider = _provider(path)

    result = provider.load()

    assert _load_from_port(provider) == 2
    assert provider.provider_name == "csv-local"
    assert provider.path == path
    assert result.data.metadata.source_name == str(path)
    assert result.data.metadata.loaded_at == LOADED_AT
    assert result.data.metadata.content_hash == hashlib.sha256(path.read_bytes()).hexdigest()
    assert result.data.metadata.observation_count == 4
    assert result.data.metadata.series_count == 2
    assert result.data.metadata.start_date == date(2026, 1, 2)
    assert result.data.metadata.end_date == date(2026, 1, 5)
    assert result.data.series[0].prices == (Decimal("10.00"), Decimal("11.00"))
    assert not result.issues


def test_accepts_portuguese_aliases_bom_and_semicolon(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "aliases.csv",
        "\ufeffAtivo;Data;Fechamento;Moeda\nAAA;2026-01-02;10.5;brl\n",
    )

    result = _provider(path).load()

    assert result.data.series[0].key.ticker == "AAA"
    assert result.data.series[0].key.currency.code == "BRL"
    assert result.data.series[0].prices == (Decimal("10.5"),)


def test_reorders_unsorted_rows_with_explicit_warning(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "unsorted.csv",
        "ticker,date,price,currency\nAAA,2026-01-05,11,BRL\nAAA,2026-01-02,10,BRL\n",
    )

    result = _provider(path).load()

    assert tuple(item.observed_on for item in result.data.series[0].observations) == (
        date(2026, 1, 2),
        date(2026, 1, 5),
    )
    assert result.issues[0].issue.code == "PRICE_ROWS_REORDERED"
    assert result.issues[0].line_number is None


def test_missing_price_errors_by_default(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "missing.csv",
        "ticker,date,price,currency\nAAA,2026-01-02,,BRL\n",
    )

    with pytest.raises(MarketDataError) as exc_info:
        _provider(path).load()

    assert exc_info.value.primary_issue.issue.code == "MISSING_PRICE"
    assert exc_info.value.primary_issue.line_number == 2


def test_drop_policy_skips_missing_price_and_preserves_warning(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "drop.csv",
        "ticker,date,price,currency\nAAA,2026-01-02,,BRL\nAAA,2026-01-05,11,BRL\n",
    )
    options = CsvMarketDataOptions(missing_value_policy=MissingValuePolicy.DROP)

    result = _provider(path, options).load()

    assert result.data.series[0].prices == (Decimal("11"),)
    assert result.data.metadata.dropped_rows == 1
    assert result.data.metadata.missing_value_policy is MissingValuePolicy.DROP
    assert result.issues[0].issue.code == "MISSING_PRICE_DROPPED"
    assert result.issues[0].line_number == 2


def test_drop_policy_rejects_source_when_no_observation_remains(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "all-missing.csv",
        "ticker,date,price,currency\nAAA,2026-01-02,,BRL\n",
    )
    options = CsvMarketDataOptions(missing_value_policy=MissingValuePolicy.DROP)

    with pytest.raises(MarketDataError) as exc_info:
        _provider(path, options).load()

    assert exc_info.value.primary_issue.issue.code == "NO_PRICE_OBSERVATIONS"


def test_accumulates_independent_row_errors(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "errors.csv",
        "ticker,date,price,currency\n,2026-13-40,wrong,B1L\nAAA,14/07/2026,0,BRL\n",
    )

    with pytest.raises(MarketDataError) as exc_info:
        _provider(path).load()

    problems = exc_info.value.problems
    codes = {problem.issue.code for problem in problems}
    assert codes == {
        "MISSING_MARKET_DATA_VALUE",
        "INVALID_CURRENCY_CODE",
        "INVALID_PRICE_DATE",
        "INVALID_PRICE_DECIMAL",
        "NON_POSITIVE_PRICE",
    }
    assert {problem.line_number for problem in problems} == {2, 3}


def test_rejects_duplicate_ticker_currency_and_date(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "duplicate.csv",
        "ticker,date,price,currency\naaa,2026-01-02,10,brl\nAAA,2026-01-02,11,BRL\n",
    )

    with pytest.raises(MarketDataError) as exc_info:
        _provider(path).load()

    assert exc_info.value.primary_issue.issue.code == "DUPLICATE_PRICE_OBSERVATION"
    assert exc_info.value.primary_issue.line_number == 3


def test_extra_column_warns_but_extra_value_without_header_errors(tmp_path: Path) -> None:
    declared = _write(
        tmp_path / "declared.csv",
        "ticker,date,price,currency,source\nAAA,2026-01-02,10,BRL,Synthetic\n",
    )
    extra = _write(
        tmp_path / "extra.csv",
        "ticker,date,price,currency\nAAA,2026-01-02,10,BRL,unexpected\n",
    )

    result = _provider(declared).load()
    assert result.issues[0].issue.code == "EXTRA_MARKET_DATA_COLUMNS_IGNORED"

    with pytest.raises(MarketDataError) as exc_info:
        _provider(extra).load()
    assert exc_info.value.primary_issue.issue.code == "TOO_MANY_MARKET_DATA_FIELDS"


@pytest.mark.parametrize(
    ("text", "expected_code"),
    [
        ("", "EMPTY_MARKET_DATA_FILE"),
        ("ticker,date,price,currency\n", "NO_MARKET_DATA_ROWS"),
        ("ticker,date,price\nAAA,2026-01-02,10\n", "MISSING_MARKET_DATA_COLUMNS"),
        (
            "ticker,symbol,date,price,currency\nAAA,AAA,2026-01-02,10,BRL\n",
            "DUPLICATE_MARKET_DATA_MAPPING",
        ),
        (
            "ticker,date,price,currency,foo,foo\nAAA,2026-01-02,10,BRL,a,b\n",
            "DUPLICATE_MARKET_DATA_COLUMN",
        ),
        (
            "ticker,,price,currency\nAAA,2026-01-02,10,BRL\n",
            "EMPTY_MARKET_DATA_COLUMN",
        ),
        (
            'ticker,date,price,currency\n"AAA,2026-01-02,10,BRL\n',
            "MALFORMED_MARKET_DATA_CSV",
        ),
    ],
)
def test_reports_structural_csv_errors(
    tmp_path: Path,
    text: str,
    expected_code: str,
) -> None:
    path = _write(tmp_path / "structural.csv", text)

    with pytest.raises(MarketDataError) as exc_info:
        _provider(path).load()

    assert exc_info.value.primary_issue.issue.code == expected_code


def test_reports_file_encoding_size_and_row_limit_errors(tmp_path: Path) -> None:
    invalid_encoding = tmp_path / "encoding.csv"
    invalid_encoding.write_bytes(b"\xff\xfe")
    valid = _write(tmp_path / "valid.csv")

    with pytest.raises(MarketDataError) as encoding_error:
        _provider(invalid_encoding).load()
    with pytest.raises(MarketDataError) as size_error:
        _provider(valid, CsvMarketDataOptions(max_file_size_bytes=1)).load()
    with pytest.raises(MarketDataError) as row_error:
        _provider(valid, CsvMarketDataOptions(max_rows=1)).load()

    assert encoding_error.value.primary_issue.issue.code == "INVALID_FILE_ENCODING"
    assert size_error.value.primary_issue.issue.code == "MARKET_DATA_FILE_TOO_LARGE"
    assert row_error.value.primary_issue.issue.code == "MARKET_DATA_ROW_LIMIT_EXCEEDED"


def test_reports_missing_file_and_directory_read_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.csv"

    with pytest.raises(MarketDataError) as missing_error:
        _provider(missing).load()
    with pytest.raises(MarketDataError) as directory_error:
        _provider(tmp_path).load()

    assert missing_error.value.primary_issue.issue.code == "FILE_NOT_FOUND"
    assert directory_error.value.primary_issue.issue.code == "FILE_READ_ERROR"


def test_rejects_invalid_options_path_and_clock(tmp_path: Path) -> None:
    path = _write(tmp_path / "valid.csv")

    with pytest.raises(MarketDataError) as encoding_error:
        CsvMarketDataOptions(encoding="latin-1")
    with pytest.raises(MarketDataError) as delimiter_error:
        CsvMarketDataOptions(delimiter=":")
    with pytest.raises(MarketDataError) as policy_error:
        CsvMarketDataOptions(missing_value_policy=cast(MissingValuePolicy, "skip"))
    with pytest.raises(MarketDataError) as limit_error:
        CsvMarketDataOptions(max_rows=cast(int, True))
    with pytest.raises(MarketDataError) as path_error:
        CsvMarketDataProvider(cast(Path, 7))
    with pytest.raises(MarketDataError) as clock_error:
        CsvMarketDataProvider(path, clock=cast(Callable[[], datetime], 7))

    assert encoding_error.value.primary_issue.issue.code == "UNSUPPORTED_ENCODING"
    assert delimiter_error.value.primary_issue.issue.code == "UNSUPPORTED_DELIMITER"
    assert policy_error.value.primary_issue.issue.code == "INVALID_MISSING_VALUE_POLICY"
    assert limit_error.value.primary_issue.issue.code == "INVALID_MARKET_DATA_LIMIT"
    assert path_error.value.primary_issue.issue.code == "INVALID_FILE_PATH"
    assert clock_error.value.primary_issue.issue.code == "INVALID_PROVIDER_CLOCK"


def test_rejects_naive_clock_result(tmp_path: Path) -> None:
    path = _write(tmp_path / "valid.csv")
    provider = CsvMarketDataProvider(path, clock=lambda: datetime(2026, 1, 10))

    with pytest.raises(MarketDataError) as exc_info:
        provider.load()

    assert exc_info.value.primary_issue.issue.code == "INVALID_PROVIDER_CLOCK"
