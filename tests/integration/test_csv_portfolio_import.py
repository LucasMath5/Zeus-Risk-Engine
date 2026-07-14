"""Integration tests for local CSV files and packaged sample data."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from zeus_risk.exceptions import PortfolioImportError
from zeus_risk.importers import CsvPortfolioImporter


def test_imports_versioned_fixture_from_disk() -> None:
    path = Path("tests/fixtures/portfolios/valid_portfolio.csv")

    result = CsvPortfolioImporter().import_file(path, portfolio_name="Fixture")

    assert result.source_name == str(path)
    assert result.portfolio is not None
    assert result.portfolio.name == "Fixture"
    assert result.portfolio.market_value == Decimal("600")
    assert result.summary.valid_rows == 2


def test_packaged_sample_is_valid_and_contains_short_position() -> None:
    path = Path("assets/samples/portfolio.csv")

    result = CsvPortfolioImporter().import_file(path)

    assert result.portfolio is not None
    assert result.portfolio.name == "portfolio"
    assert result.summary.accepted_rows == 3
    assert result.positions[-1].quantity == Decimal("-10")


def test_reports_missing_file() -> None:
    path = Path("tests/fixtures/portfolios/does-not-exist.csv")

    with pytest.raises(PortfolioImportError) as exc_info:
        CsvPortfolioImporter().import_file(path)

    assert exc_info.value.issue.code == "FILE_NOT_FOUND"
    assert exc_info.value.source_name == str(path)


def test_reports_invalid_utf8_file(tmp_path: Path) -> None:
    path = tmp_path / "invalid-encoding.csv"
    path.write_bytes(b"\xff\xfe\x00")

    with pytest.raises(PortfolioImportError) as exc_info:
        CsvPortfolioImporter().import_file(path)

    assert exc_info.value.issue.code == "INVALID_FILE_ENCODING"


def test_reports_directory_as_file_read_error(tmp_path: Path) -> None:
    with pytest.raises(PortfolioImportError) as exc_info:
        CsvPortfolioImporter().import_file(tmp_path)

    assert exc_info.value.issue.code == "FILE_READ_ERROR"
