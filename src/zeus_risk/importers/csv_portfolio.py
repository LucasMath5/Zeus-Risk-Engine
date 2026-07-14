"""Validated CSV adapter for portfolio positions."""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path

from zeus_risk.domain import (
    AssetClass,
    Currency,
    DomainValidationError,
    Instrument,
    Portfolio,
    Position,
    ValidationIssue,
    ValidationSeverity,
)
from zeus_risk.domain.position import validate_price, validate_quantity
from zeus_risk.exceptions import PortfolioImportError
from zeus_risk.importers.models import (
    ColumnMapping,
    ImportedField,
    ImportResult,
    ImportRow,
    ImportStatus,
    ImportSummary,
)

_ALLOWED_DELIMITERS = (",", ";", "\t", "|")
_SUPPORTED_ENCODINGS = ("utf-8", "utf-8-sig")
_REQUIRED_COLUMNS = ("ticker", "quantity", "price", "asset_class", "currency")

_HEADER_ALIASES = {
    "ticker": "ticker",
    "symbol": "ticker",
    "codigo": "ticker",
    "ativo": "ticker",
    "quantity": "quantity",
    "qty": "quantity",
    "quantidade": "quantity",
    "price": "price",
    "preco": "price",
    "unit_price": "price",
    "preco_unitario": "price",
    "asset_class": "asset_class",
    "classe": "asset_class",
    "classe_ativo": "asset_class",
    "classe_de_ativo": "asset_class",
    "currency": "currency",
    "ccy": "currency",
    "moeda": "currency",
    "sector": "sector",
    "setor": "sector",
}

_ASSET_CLASS_ALIASES = {
    "equity": AssetClass.EQUITY,
    "equities": AssetClass.EQUITY,
    "stock": AssetClass.EQUITY,
    "stocks": AssetClass.EQUITY,
    "acao": AssetClass.EQUITY,
    "acoes": AssetClass.EQUITY,
    "fixed_income": AssetClass.FIXED_INCOME,
    "renda_fixa": AssetClass.FIXED_INCOME,
    "bond": AssetClass.FIXED_INCOME,
    "bonds": AssetClass.FIXED_INCOME,
    "fx": AssetClass.FX,
    "forex": AssetClass.FX,
    "cambio": AssetClass.FX,
    "cambial": AssetClass.FX,
    "cash": AssetClass.CASH,
    "caixa": AssetClass.CASH,
    "commodity": AssetClass.COMMODITY,
    "commodities": AssetClass.COMMODITY,
    "fund": AssetClass.FUND,
    "funds": AssetClass.FUND,
    "fundo": AssetClass.FUND,
    "fundos": AssetClass.FUND,
    "derivative": AssetClass.DERIVATIVE,
    "derivatives": AssetClass.DERIVATIVE,
    "derivativo": AssetClass.DERIVATIVE,
    "derivativos": AssetClass.DERIVATIVE,
    "other": AssetClass.OTHER,
    "outro": AssetClass.OTHER,
}


@dataclass(frozen=True, slots=True)
class CsvImportOptions:
    """Explicit and reproducible CSV decoding options."""

    encoding: str = "utf-8-sig"
    delimiter: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.encoding, str):
            raise _import_error(
                "INVALID_ENCODING_TYPE",
                "CSV encoding must be a string.",
                field="encoding",
            )
        normalized_encoding = self.encoding.strip().lower().replace("_", "-")
        if normalized_encoding not in _SUPPORTED_ENCODINGS:
            raise _import_error(
                "UNSUPPORTED_ENCODING",
                "CSV encoding must be UTF-8 or UTF-8 with BOM.",
                field="encoding",
                item=self.encoding,
            )
        if self.delimiter is not None and not isinstance(self.delimiter, str):
            raise _import_error(
                "INVALID_DELIMITER_TYPE",
                "CSV delimiter must be a string or None.",
                field="delimiter",
            )
        if self.delimiter is not None and self.delimiter not in _ALLOWED_DELIMITERS:
            raise _import_error(
                "UNSUPPORTED_DELIMITER",
                "Delimiter must be comma, semicolon, tab, or vertical bar.",
                field="delimiter",
                item=self.delimiter,
            )

        object.__setattr__(self, "encoding", normalized_encoding)


class CsvPortfolioImporter:
    """Import reviewable portfolio rows from UTF-8 CSV content."""

    def __init__(self, options: CsvImportOptions | None = None) -> None:
        self._options = options or CsvImportOptions()

    @property
    def options(self) -> CsvImportOptions:
        """Return the immutable options used by this importer."""

        return self._options

    def import_file(
        self,
        path: str | Path,
        *,
        portfolio_name: str | None = None,
    ) -> ImportResult:
        """Read and import a local CSV file without external calls."""

        source_path = Path(path)
        source_name = str(source_path)
        try:
            text = source_path.read_text(encoding=self.options.encoding)
        except FileNotFoundError as error:
            raise _import_error(
                "FILE_NOT_FOUND",
                "Portfolio CSV file was not found.",
                field="path",
                item=source_name,
                source_name=source_name,
            ) from error
        except UnicodeDecodeError as error:
            raise _import_error(
                "INVALID_FILE_ENCODING",
                "Portfolio CSV could not be decoded as UTF-8.",
                field="encoding",
                item=self.options.encoding,
                source_name=source_name,
            ) from error
        except OSError as error:
            raise _import_error(
                "FILE_READ_ERROR",
                "Portfolio CSV could not be read.",
                field="path",
                item=source_name,
                source_name=source_name,
            ) from error

        resolved_name = source_path.stem if portfolio_name is None else portfolio_name
        return self.import_text(
            text,
            portfolio_name=resolved_name,
            source_name=source_name,
        )

    def import_text(
        self,
        text: str,
        *,
        portfolio_name: str = "Imported Portfolio",
        source_name: str = "<memory>",
    ) -> ImportResult:
        """Import CSV text and accumulate recoverable row-level problems."""

        if not isinstance(text, str):
            raise _import_error(
                "INVALID_CSV_TEXT",
                "CSV content must be text.",
                source_name=source_name,
            )
        if not isinstance(portfolio_name, str) or not portfolio_name.strip():
            raise _import_error(
                "INVALID_PORTFOLIO_NAME",
                "Portfolio name must be a non-empty string.",
                field="name",
                source_name=source_name,
            )

        normalized_text = text.removeprefix("\ufeff")
        if not normalized_text.strip():
            raise _import_error(
                "EMPTY_FILE",
                "Portfolio CSV is empty.",
                source_name=source_name,
            )

        delimiter = self.options.delimiter or _detect_delimiter(normalized_text)
        records = _read_records(normalized_text, delimiter, source_name)
        header_record, data_records = _split_header_and_data(records, source_name)
        column_mappings, global_issues = _map_columns(header_record[1], source_name)

        parsed_rows = tuple(
            _parse_row(
                line_number=line_number,
                record=record,
                headers=header_record[1],
                mappings=column_mappings,
            )
            for line_number, record in data_records
            if not _is_blank_record(record)
        )
        if not parsed_rows:
            raise _import_error(
                "NO_DATA_ROWS",
                "Portfolio CSV contains a header but no data rows.",
                source_name=source_name,
            )

        reviewed_rows = _mark_duplicate_positions(parsed_rows)
        positions = tuple(row.position for row in reviewed_rows if row.position is not None)
        portfolio = _build_portfolio(portfolio_name.strip(), positions, source_name)
        summary = ImportSummary.from_rows(reviewed_rows)

        return ImportResult(
            source_name=source_name,
            encoding=self.options.encoding,
            delimiter=delimiter,
            column_mappings=column_mappings,
            rows=reviewed_rows,
            summary=summary,
            portfolio=portfolio,
            issues=global_issues,
        )


def _read_records(
    text: str,
    delimiter: str,
    source_name: str,
) -> tuple[tuple[int, tuple[str, ...]], ...]:
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
    records: list[tuple[int, tuple[str, ...]]] = []
    try:
        for record in reader:
            records.append((reader.line_num, tuple(record)))
    except csv.Error as error:
        raise _import_error(
            "MALFORMED_CSV",
            "Portfolio CSV contains malformed quoting or fields.",
            item=str(error),
            source_name=source_name,
        ) from error
    return tuple(records)


def _split_header_and_data(
    records: tuple[tuple[int, tuple[str, ...]], ...],
    source_name: str,
) -> tuple[tuple[int, tuple[str, ...]], tuple[tuple[int, tuple[str, ...]], ...]]:
    for index, record in enumerate(records):
        if not _is_blank_record(record[1]):
            return record, records[index + 1 :]

    raise _import_error(
        "EMPTY_FILE",
        "Portfolio CSV is empty.",
        source_name=source_name,
    )


def _map_columns(
    headers: tuple[str, ...],
    source_name: str,
) -> tuple[tuple[ColumnMapping, ...], tuple[ValidationIssue, ...]]:
    if not headers or any(not header.strip() for header in headers):
        raise _import_error(
            "EMPTY_COLUMN_NAME",
            "CSV header contains an empty column name.",
            field="header",
            source_name=source_name,
        )

    mappings = tuple(
        ColumnMapping(
            source_name=header,
            normalized_name=_normalize_token(header),
            canonical_name=_HEADER_ALIASES.get(_normalize_token(header)),
        )
        for header in headers
    )

    normalized_names = [mapping.normalized_name for mapping in mappings]
    duplicate_source = _first_duplicate(normalized_names)
    if duplicate_source is not None:
        raise _import_error(
            "DUPLICATE_SOURCE_COLUMN",
            "CSV header contains duplicate normalized column names.",
            field="header",
            item=duplicate_source,
            source_name=source_name,
        )

    canonical_names = [
        mapping.canonical_name for mapping in mappings if mapping.canonical_name is not None
    ]
    duplicate_canonical = _first_duplicate(canonical_names)
    if duplicate_canonical is not None:
        raise _import_error(
            "DUPLICATE_COLUMN_MAPPING",
            "More than one source column maps to the same portfolio field.",
            field="header",
            item=duplicate_canonical,
            source_name=source_name,
        )

    missing = tuple(column for column in _REQUIRED_COLUMNS if column not in canonical_names)
    if missing:
        raise _import_error(
            "MISSING_REQUIRED_COLUMNS",
            "CSV header is missing required portfolio columns.",
            field="header",
            item=", ".join(missing),
            source_name=source_name,
        )

    extra_columns = tuple(
        mapping.source_name for mapping in mappings if mapping.canonical_name is None
    )
    issues: tuple[ValidationIssue, ...] = ()
    if extra_columns:
        issues = (
            _issue(
                ValidationSeverity.WARNING,
                "EXTRA_COLUMNS_IGNORED",
                "Unmapped source columns were preserved but ignored.",
                field="header",
                item=", ".join(extra_columns),
            ),
        )

    return mappings, issues


def _parse_row(
    *,
    line_number: int,
    record: tuple[str, ...],
    headers: tuple[str, ...],
    mappings: tuple[ColumnMapping, ...],
) -> ImportRow:
    issues: list[ValidationIssue] = []
    padded_values = record[: len(headers)] + ("",) * max(0, len(headers) - len(record))
    raw_fields = tuple(
        ImportedField(name=header, value=padded_values[index])
        for index, header in enumerate(headers)
    )

    if len(record) > len(headers):
        extra_values = record[len(headers) :]
        raw_fields += tuple(
            ImportedField(name=f"__extra_{index}", value=value)
            for index, value in enumerate(extra_values, start=1)
        )
        issues.append(
            _issue(
                ValidationSeverity.ERROR,
                "TOO_MANY_FIELDS",
                "CSV row contains more values than the header defines.",
                item=str(len(extra_values)),
            )
        )

    values = {
        mapping.canonical_name: padded_values[index].strip()
        for index, mapping in enumerate(mappings)
        if mapping.canonical_name is not None
    }

    for field in _REQUIRED_COLUMNS:
        if not values.get(field, ""):
            issues.append(
                _issue(
                    ValidationSeverity.ERROR,
                    "MISSING_REQUIRED_VALUE",
                    "Required portfolio value is missing.",
                    field=field,
                    item=values.get("ticker") or None,
                )
            )

    sector = values.get("sector", "")
    if not sector:
        issues.append(
            _issue(
                ValidationSeverity.WARNING,
                "MISSING_OPTIONAL_SECTOR",
                "Sector was not provided.",
                field="sector",
                item=values.get("ticker") or None,
            )
        )

    quantity = _parse_decimal(values.get("quantity", ""), "quantity", issues)
    price = _parse_decimal(values.get("price", ""), "price", issues)
    asset_class = _parse_asset_class(values.get("asset_class", ""), issues)
    currency = _parse_currency(values.get("currency", ""), issues)

    position: Position | None = None
    if (
        values.get("ticker")
        and quantity is not None
        and price is not None
        and asset_class is not None
        and currency is not None
    ):
        try:
            instrument = Instrument(
                ticker=values["ticker"],
                asset_class=asset_class,
                currency=currency,
                sector=sector or None,
            )
            position = Position(instrument=instrument, quantity=quantity, price=price)
        except DomainValidationError as error:
            issues.extend(error.issues)

    has_error = any(issue.severity is ValidationSeverity.ERROR for issue in issues)
    if has_error:
        status = ImportStatus.ERROR
        position = None
    elif issues:
        status = ImportStatus.WARNING
    else:
        status = ImportStatus.VALID

    return ImportRow(
        line_number=line_number,
        status=status,
        raw_fields=raw_fields,
        position=position,
        issues=tuple(issues),
    )


def _parse_decimal(
    value: str,
    field: str,
    issues: list[ValidationIssue],
) -> Decimal | None:
    if not value:
        return None
    try:
        decimal_value = Decimal(value)
    except InvalidOperation:
        issues.append(
            _issue(
                ValidationSeverity.ERROR,
                "INVALID_DECIMAL",
                "Numeric value must use a decimal point and contain no thousands separator.",
                field=field,
                item=value,
            )
        )
        return None

    try:
        if field == "quantity":
            validate_quantity(decimal_value)
        else:
            validate_price(decimal_value)
    except DomainValidationError as error:
        issues.extend(error.issues)
        return None
    return decimal_value


def _parse_asset_class(
    value: str,
    issues: list[ValidationIssue],
) -> AssetClass | None:
    if not value:
        return None
    asset_class = _ASSET_CLASS_ALIASES.get(_normalize_token(value))
    if asset_class is None:
        issues.append(
            _issue(
                ValidationSeverity.ERROR,
                "UNSUPPORTED_ASSET_CLASS",
                "Asset class is not supported by the current taxonomy.",
                field="asset_class",
                item=value,
            )
        )
    return asset_class


def _parse_currency(
    value: str,
    issues: list[ValidationIssue],
) -> Currency | None:
    if not value:
        return None
    try:
        return Currency(value)
    except DomainValidationError as error:
        issues.extend(error.issues)
        return None


def _mark_duplicate_positions(rows: tuple[ImportRow, ...]) -> tuple[ImportRow, ...]:
    seen: set[tuple[str, str]] = set()
    reviewed_rows: list[ImportRow] = []

    for row in rows:
        if row.position is None:
            reviewed_rows.append(row)
            continue

        key = (row.position.instrument.ticker, row.position.instrument.currency.code)
        if key in seen:
            duplicate_issue = _issue(
                ValidationSeverity.ERROR,
                "DUPLICATE_POSITION",
                "Ticker and currency identify more than one CSV position.",
                field="ticker",
                item=f"{key[0]}:{key[1]}",
            )
            reviewed_rows.append(
                replace(
                    row,
                    status=ImportStatus.ERROR,
                    position=None,
                    issues=(*row.issues, duplicate_issue),
                )
            )
            continue

        seen.add(key)
        reviewed_rows.append(row)

    return tuple(reviewed_rows)


def _build_portfolio(
    name: str,
    positions: tuple[Position, ...],
    source_name: str,
) -> Portfolio | None:
    if not positions:
        return None
    try:
        return Portfolio(name=name, positions=positions)
    except DomainValidationError as error:
        raise PortfolioImportError(error.primary_issue, source_name=source_name) from error


def _detect_delimiter(text: str) -> str:
    sample_lines = [line for line in text.splitlines() if line.strip()][:25]
    sample = "\n".join(sample_lines)[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(_ALLOWED_DELIMITERS))
    except csv.Error:
        return ","
    return dialect.delimiter


def _normalize_token(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    normalized = re.sub(r"[^a-z0-9]+", "_", without_accents.strip().lower())
    return normalized.strip("_")


def _first_duplicate(values: list[str]) -> str | None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None


def _is_blank_record(record: tuple[str, ...]) -> bool:
    return not record or all(not value.strip() for value in record)


def _issue(
    severity: ValidationSeverity,
    code: str,
    message: str,
    *,
    field: str | None = None,
    item: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        severity=severity,
        code=code,
        message=message,
        field=field,
        item=item,
    )


def _import_error(
    code: str,
    message: str,
    *,
    field: str | None = None,
    item: str | None = None,
    source_name: str | None = None,
) -> PortfolioImportError:
    return PortfolioImportError(
        _issue(
            ValidationSeverity.ERROR,
            code,
            message,
            field=field,
            item=item,
        ),
        source_name=source_name,
    )
