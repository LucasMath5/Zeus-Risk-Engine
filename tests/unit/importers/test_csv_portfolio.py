"""Unit tests for the validated CSV portfolio adapter."""

from __future__ import annotations

from decimal import Decimal
from typing import cast

import pytest

from zeus_risk.domain import Currency, ValidationSeverity
from zeus_risk.exceptions import PortfolioImportError
from zeus_risk.importers import CsvImportOptions, CsvPortfolioImporter, ImportStatus

VALID_CSV = """ticker,quantity,price,asset_class,currency,sector
PETR4,10,25,equity,BRL,Energy
VALE3,5,70,equity,BRL,Materials
"""


def test_imports_valid_csv_into_portfolio() -> None:
    result = CsvPortfolioImporter().import_text(VALID_CSV, portfolio_name="Brazil")

    assert result.source_name == "<memory>"
    assert result.encoding == "utf-8-sig"
    assert result.delimiter == ","
    assert result.summary.total_rows == 2
    assert result.summary.accepted_rows == 2
    assert result.summary.valid_rows == 2
    assert result.summary.warning_rows == 0
    assert result.summary.error_rows == 0
    assert result.portfolio is not None
    assert result.portfolio.name == "Brazil"
    assert result.portfolio.market_value == Decimal("600")
    assert tuple(position.instrument.ticker for position in result.positions) == (
        "PETR4",
        "VALE3",
    )
    assert not result.has_errors
    assert not result.is_partial


def test_preserves_source_fields_and_column_mapping() -> None:
    result = CsvPortfolioImporter().import_text(VALID_CSV)

    assert result.column_mappings[0].source_name == "ticker"
    assert result.column_mappings[0].canonical_name == "ticker"
    assert result.rows[0].line_number == 2
    assert result.rows[0].raw_fields[1].name == "quantity"
    assert result.rows[0].raw_fields[1].value == "10"


def test_accepts_portuguese_aliases_and_semicolon_delimiter() -> None:
    text = """Ativo;Quantidade;Preço;Classe de Ativo;Moeda;Setor
PETR4;10;25.50;ação;brl;Energia
"""

    result = CsvPortfolioImporter().import_text(text)

    assert result.delimiter == ";"
    assert result.summary.valid_rows == 1
    assert result.positions[0].instrument.ticker == "PETR4"
    assert result.positions[0].instrument.currency == Currency("BRL")
    assert result.positions[0].price == Decimal("25.50")


def test_accepts_utf8_bom_in_memory() -> None:
    result = CsvPortfolioImporter().import_text("\ufeff" + VALID_CSV)

    assert result.summary.accepted_rows == 2


def test_accepts_explicit_controlled_delimiter() -> None:
    text = """ticker|quantity|price|asset_class|currency|sector
PETR4|10|25|equity|BRL|Energy
"""
    importer = CsvPortfolioImporter(CsvImportOptions(delimiter="|"))

    result = importer.import_text(text)

    assert result.delimiter == "|"
    assert result.summary.valid_rows == 1


def test_missing_optional_sector_creates_warning_and_accepted_position() -> None:
    text = """ticker,quantity,price,asset_class,currency
PETR4,10,25,equity,BRL
"""

    result = CsvPortfolioImporter().import_text(text)

    assert result.summary.warning_rows == 1
    assert result.summary.accepted_rows == 1
    assert result.rows[0].status is ImportStatus.WARNING
    assert result.rows[0].position is not None
    assert result.rows[0].issues[0].code == "MISSING_OPTIONAL_SECTOR"
    assert result.located_issues[0].line_number == 2


def test_declared_extra_columns_are_preserved_and_warn_globally() -> None:
    text = """ticker,quantity,price,asset_class,currency,sector,book
PETR4,10,25,equity,BRL,Energy,Trading
"""

    result = CsvPortfolioImporter().import_text(text)

    assert result.summary.valid_rows == 1
    assert result.issues[0].severity is ValidationSeverity.WARNING
    assert result.issues[0].code == "EXTRA_COLUMNS_IGNORED"
    assert result.column_mappings[-1].canonical_name is None
    assert result.rows[0].raw_fields[-1].value == "Trading"
    assert result.located_issues[0].line_number is None


def test_extra_row_values_create_recoverable_row_error() -> None:
    text = """ticker,quantity,price,asset_class,currency,sector
PETR4,10,25,equity,BRL,Energy,unexpected
VALE3,5,70,equity,BRL,Materials
"""

    result = CsvPortfolioImporter().import_text(text)

    assert result.summary.error_rows == 1
    assert result.summary.accepted_rows == 1
    assert result.rows[0].status is ImportStatus.ERROR
    assert result.rows[0].position is None
    assert result.rows[0].issues[0].code == "TOO_MANY_FIELDS"
    assert result.rows[0].raw_fields[-1].name == "__extra_1"
    assert result.is_partial


def test_accumulates_independent_field_errors_and_continues() -> None:
    text = """ticker,quantity,price,asset_class,currency,sector
BAD,not-a-number,-1,unsupported,B1L,
GOOD,2,10,equity,BRL,Energy
"""

    result = CsvPortfolioImporter().import_text(text)

    first_codes = {issue.code for issue in result.rows[0].issues}
    assert first_codes == {
        "INVALID_DECIMAL",
        "NON_POSITIVE_PRICE",
        "UNSUPPORTED_ASSET_CLASS",
        "INVALID_CURRENCY_CODE",
        "MISSING_OPTIONAL_SECTOR",
    }
    assert result.rows[0].line_number == 2
    assert result.rows[1].status is ImportStatus.VALID
    assert result.summary.error_rows == 1
    assert result.summary.accepted_rows == 1
    assert result.portfolio is not None
    assert result.portfolio.positions[0].instrument.ticker == "GOOD"


@pytest.mark.parametrize(
    ("quantity", "price", "expected_code"),
    [
        ("0", "10", "ZERO_QUANTITY"),
        ("NaN", "10", "NON_FINITE_QUANTITY"),
        ("1", "NaN", "NON_FINITE_PRICE"),
        ("1", "0", "NON_POSITIVE_PRICE"),
    ],
)
def test_applies_domain_numeric_validation(
    quantity: str,
    price: str,
    expected_code: str,
) -> None:
    text = (
        "ticker,quantity,price,asset_class,currency,sector\n"
        f"TEST,{quantity},{price},equity,BRL,Energy\n"
    )

    result = CsvPortfolioImporter().import_text(text)

    assert result.summary.error_rows == 1
    assert expected_code in {issue.code for issue in result.rows[0].issues}
    assert result.portfolio is None


def test_accepts_negative_quantity_as_short_position() -> None:
    text = """ticker,quantity,price,asset_class,currency,sector
SHORT3,-2,100,equity,BRL,Energy
"""

    result = CsvPortfolioImporter().import_text(text)

    assert result.positions[0].market_value == Decimal("-200")


def test_rejects_later_duplicate_but_preserves_first_position() -> None:
    text = """ticker,quantity,price,asset_class,currency,sector
petr4,10,25,equity,brl,Energy
PETR4,5,26,equity,BRL,Energy
"""

    result = CsvPortfolioImporter().import_text(text)

    assert result.summary.accepted_rows == 1
    assert result.summary.error_rows == 1
    assert result.rows[1].issues[-1].code == "DUPLICATE_POSITION"
    assert result.rows[1].issues[-1].item == "PETR4:BRL"


def test_same_ticker_in_different_currency_is_not_duplicate() -> None:
    text = """ticker,quantity,price,asset_class,currency,sector
ABC,10,25,equity,BRL,Energy
ABC,5,10,equity,USD,Energy
"""

    result = CsvPortfolioImporter().import_text(text)

    assert result.summary.accepted_rows == 2
    assert result.portfolio is not None
    assert result.portfolio.currencies == (Currency("BRL"), Currency("USD"))


def test_blank_lines_are_ignored_without_changing_source_line_numbers() -> None:
    text = """

ticker,quantity,price,asset_class,currency,sector

PETR4,10,25,equity,BRL,Energy

"""

    result = CsvPortfolioImporter().import_text(text)

    assert result.summary.total_rows == 1
    assert result.rows[0].line_number == 5


@pytest.mark.parametrize(
    ("text", "expected_code"),
    [
        ("", "EMPTY_FILE"),
        ("ticker,quantity,price,asset_class,currency\n", "NO_DATA_ROWS"),
        ("ticker,quantity,price\nPETR4,10,25\n", "MISSING_REQUIRED_COLUMNS"),
        (
            "ticker,symbol,quantity,price,asset_class,currency\nPETR4,PETR4,10,25,equity,BRL\n",
            "DUPLICATE_COLUMN_MAPPING",
        ),
        (
            "ticker,quantity,price,asset_class,currency,foo,foo\nPETR4,10,25,equity,BRL,a,b\n",
            "DUPLICATE_SOURCE_COLUMN",
        ),
        ("ticker,,price,asset_class,currency\nPETR4,10,25,equity,BRL\n", "EMPTY_COLUMN_NAME"),
        (
            'ticker,quantity,price,asset_class,currency\n"PETR4,10,25,equity,BRL\n',
            "MALFORMED_CSV",
        ),
    ],
)
def test_structural_file_errors_raise_import_exception(text: str, expected_code: str) -> None:
    with pytest.raises(PortfolioImportError) as exc_info:
        CsvPortfolioImporter().import_text(text)

    assert exc_info.value.issue.code == expected_code


def test_rejects_invalid_options_and_boundary_types() -> None:
    with pytest.raises(PortfolioImportError) as encoding_error:
        CsvImportOptions(encoding="latin-1")
    with pytest.raises(PortfolioImportError) as delimiter_error:
        CsvImportOptions(delimiter=":")
    with pytest.raises(PortfolioImportError) as encoding_type_error:
        CsvImportOptions(encoding=cast(str, 8))
    with pytest.raises(PortfolioImportError) as delimiter_type_error:
        CsvImportOptions(delimiter=cast(str, 8))
    with pytest.raises(PortfolioImportError) as text_error:
        CsvPortfolioImporter().import_text(cast(str, b"bytes"))
    with pytest.raises(PortfolioImportError) as name_error:
        CsvPortfolioImporter().import_text(VALID_CSV, portfolio_name="  ")

    assert encoding_error.value.issue.code == "UNSUPPORTED_ENCODING"
    assert delimiter_error.value.issue.code == "UNSUPPORTED_DELIMITER"
    assert encoding_type_error.value.issue.code == "INVALID_ENCODING_TYPE"
    assert delimiter_type_error.value.issue.code == "INVALID_DELIMITER_TYPE"
    assert text_error.value.issue.code == "INVALID_CSV_TEXT"
    assert name_error.value.issue.code == "INVALID_PORTFOLIO_NAME"
