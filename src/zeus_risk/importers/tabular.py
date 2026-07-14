"""Shared normalization and domain validation for tabular portfolio adapters."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation

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

REQUIRED_COLUMNS = ("ticker", "quantity", "price", "asset_class", "currency")

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
class TabularRecord:
    """One source row converted to textual values plus adapter-level issues."""

    line_number: int
    values: tuple[str, ...]
    issues: tuple[ValidationIssue, ...] = ()
    raw_values: tuple[str, ...] | None = None


def map_columns(
    headers: tuple[str, ...],
    source_name: str,
) -> tuple[tuple[ColumnMapping, ...], tuple[ValidationIssue, ...]]:
    """Normalize a header and validate the shared portfolio column contract."""

    if not headers or any(not header.strip() for header in headers):
        raise import_error(
            "EMPTY_COLUMN_NAME",
            "Tabular header contains an empty column name.",
            field="header",
            source_name=source_name,
        )

    mappings = tuple(
        ColumnMapping(
            source_name=header,
            normalized_name=normalize_token(header),
            canonical_name=_HEADER_ALIASES.get(normalize_token(header)),
        )
        for header in headers
    )

    normalized_names = [mapping.normalized_name for mapping in mappings]
    duplicate_source = _first_duplicate(normalized_names)
    if duplicate_source is not None:
        raise import_error(
            "DUPLICATE_SOURCE_COLUMN",
            "Tabular header contains duplicate normalized column names.",
            field="header",
            item=duplicate_source,
            source_name=source_name,
        )

    canonical_names = [
        mapping.canonical_name for mapping in mappings if mapping.canonical_name is not None
    ]
    duplicate_canonical = _first_duplicate(canonical_names)
    if duplicate_canonical is not None:
        raise import_error(
            "DUPLICATE_COLUMN_MAPPING",
            "More than one source column maps to the same portfolio field.",
            field="header",
            item=duplicate_canonical,
            source_name=source_name,
        )

    missing = tuple(column for column in REQUIRED_COLUMNS if column not in canonical_names)
    if missing:
        raise import_error(
            "MISSING_REQUIRED_COLUMNS",
            "Tabular header is missing required portfolio columns.",
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
            issue(
                ValidationSeverity.WARNING,
                "EXTRA_COLUMNS_IGNORED",
                "Unmapped source columns were preserved but ignored.",
                field="header",
                item=", ".join(extra_columns),
            ),
        )

    return mappings, issues


def build_import_result(
    *,
    source_name: str,
    portfolio_name: str,
    column_mappings: tuple[ColumnMapping, ...],
    records: tuple[TabularRecord, ...],
    global_issues: tuple[ValidationIssue, ...] = (),
    encoding: str | None = None,
    delimiter: str | None = None,
    worksheet_name: str | None = None,
) -> ImportResult:
    """Validate converted rows and assemble the format-independent import result."""

    parsed_rows = tuple(
        _parse_row(record=record, mappings=column_mappings)
        for record in records
        if not is_blank_record(record.values) or record.issues
    )
    if not parsed_rows:
        raise import_error(
            "NO_DATA_ROWS",
            "Portfolio source contains a header but no data rows.",
            source_name=source_name,
        )

    reviewed_rows = _mark_duplicate_positions(parsed_rows)
    positions = tuple(row.position for row in reviewed_rows if row.position is not None)
    portfolio = _build_portfolio(portfolio_name.strip(), positions, source_name)

    return ImportResult(
        source_name=source_name,
        encoding=encoding,
        delimiter=delimiter,
        column_mappings=column_mappings,
        rows=reviewed_rows,
        summary=ImportSummary.from_rows(reviewed_rows),
        portfolio=portfolio,
        worksheet_name=worksheet_name,
        issues=global_issues,
    )


def is_blank_record(record: tuple[str, ...]) -> bool:
    """Return whether a converted record contains no usable value."""

    return not record or all(not value.strip() for value in record)


def normalize_token(value: str) -> str:
    """Normalize external labels for controlled alias matching."""

    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    normalized = re.sub(r"[^a-z0-9]+", "_", without_accents.strip().lower())
    return normalized.strip("_")


def issue(
    severity: ValidationSeverity,
    code: str,
    message: str,
    *,
    field: str | None = None,
    item: str | None = None,
) -> ValidationIssue:
    """Create one issue using the shared validation contract."""

    return ValidationIssue(
        severity=severity,
        code=code,
        message=message,
        field=field,
        item=item,
    )


def import_error(
    code: str,
    message: str,
    *,
    field: str | None = None,
    item: str | None = None,
    source_name: str | None = None,
) -> PortfolioImportError:
    """Create one structural portfolio-import exception."""

    return PortfolioImportError(
        issue(
            ValidationSeverity.ERROR,
            code,
            message,
            field=field,
            item=item,
        ),
        source_name=source_name,
    )


def _parse_row(
    *,
    record: TabularRecord,
    mappings: tuple[ColumnMapping, ...],
) -> ImportRow:
    issues = list(record.issues)
    headers = tuple(mapping.source_name for mapping in mappings)
    values = record.values
    raw_values = record.raw_values if record.raw_values is not None else values
    padded_values = values[: len(headers)] + ("",) * max(0, len(headers) - len(values))
    padded_raw_values = raw_values[: len(headers)] + ("",) * max(0, len(headers) - len(raw_values))
    raw_fields = tuple(
        ImportedField(name=header, value=padded_raw_values[index])
        for index, header in enumerate(headers)
    )

    if len(raw_values) > len(headers):
        extra_values = raw_values[len(headers) :]
        raw_fields += tuple(
            ImportedField(name=f"__extra_{index}", value=value)
            for index, value in enumerate(extra_values, start=1)
        )
        issues.append(
            issue(
                ValidationSeverity.ERROR,
                "TOO_MANY_FIELDS",
                "Source row contains more values than the header defines.",
                item=str(len(extra_values)),
            )
        )

    canonical_values = {
        mapping.canonical_name: padded_values[index].strip()
        for index, mapping in enumerate(mappings)
        if mapping.canonical_name is not None
    }

    for field in REQUIRED_COLUMNS:
        field_has_error = any(
            problem.field == field and problem.severity is ValidationSeverity.ERROR
            for problem in issues
        )
        if not canonical_values.get(field, "") and not field_has_error:
            issues.append(
                issue(
                    ValidationSeverity.ERROR,
                    "MISSING_REQUIRED_VALUE",
                    "Required portfolio value is missing.",
                    field=field,
                    item=canonical_values.get("ticker") or None,
                )
            )

    sector = canonical_values.get("sector", "")
    sector_has_error = any(
        problem.field == "sector" and problem.severity is ValidationSeverity.ERROR
        for problem in issues
    )
    if not sector and not sector_has_error:
        issues.append(
            issue(
                ValidationSeverity.WARNING,
                "MISSING_OPTIONAL_SECTOR",
                "Sector was not provided.",
                field="sector",
                item=canonical_values.get("ticker") or None,
            )
        )

    quantity = _parse_decimal(canonical_values.get("quantity", ""), "quantity", issues)
    price = _parse_decimal(canonical_values.get("price", ""), "price", issues)
    asset_class = _parse_asset_class(canonical_values.get("asset_class", ""), issues)
    currency = _parse_currency(canonical_values.get("currency", ""), issues)

    position: Position | None = None
    if (
        canonical_values.get("ticker")
        and quantity is not None
        and price is not None
        and asset_class is not None
        and currency is not None
    ):
        try:
            instrument = Instrument(
                ticker=canonical_values["ticker"],
                asset_class=asset_class,
                currency=currency,
                sector=sector or None,
            )
            position = Position(instrument=instrument, quantity=quantity, price=price)
        except DomainValidationError as error:
            issues.extend(error.issues)

    has_error = any(problem.severity is ValidationSeverity.ERROR for problem in issues)
    if has_error:
        status = ImportStatus.ERROR
        position = None
    elif issues:
        status = ImportStatus.WARNING
    else:
        status = ImportStatus.VALID

    return ImportRow(
        line_number=record.line_number,
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
            issue(
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
    asset_class = _ASSET_CLASS_ALIASES.get(normalize_token(value))
    if asset_class is None:
        issues.append(
            issue(
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
            duplicate_issue = issue(
                ValidationSeverity.ERROR,
                "DUPLICATE_POSITION",
                "Ticker and currency identify more than one imported position.",
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


def _first_duplicate(values: list[str]) -> str | None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None
