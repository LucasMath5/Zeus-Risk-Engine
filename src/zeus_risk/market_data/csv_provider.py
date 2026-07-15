"""Offline CSV provider for validated daily price series."""

from __future__ import annotations

import csv
import hashlib
import io
import re
import unicodedata
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from zeus_risk.domain import (
    Currency,
    DataFrequency,
    DomainValidationError,
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
from zeus_risk.domain.position import validate_price
from zeus_risk.exceptions import MarketDataError

_ALLOWED_DELIMITERS = (",", ";", "\t", "|")
_SUPPORTED_ENCODINGS = ("utf-8", "utf-8-sig")
_ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_REQUIRED_COLUMNS = ("ticker", "date", "price", "currency")
_HEADER_ALIASES = {
    "ticker": "ticker",
    "symbol": "ticker",
    "ativo": "ticker",
    "codigo": "ticker",
    "date": "date",
    "data": "date",
    "price": "price",
    "close": "price",
    "preco": "price",
    "fechamento": "price",
    "currency": "currency",
    "ccy": "currency",
    "moeda": "currency",
}


@dataclass(frozen=True, slots=True)
class CsvMarketDataOptions:
    """Explicit parsing and resource policies for the local CSV provider."""

    encoding: str = "utf-8-sig"
    delimiter: str | None = None
    missing_value_policy: MissingValuePolicy = MissingValuePolicy.ERROR
    max_file_size_bytes: int = 25 * 1024 * 1024
    max_rows: int = 250_000

    def __post_init__(self) -> None:
        if not isinstance(self.encoding, str):
            raise _market_data_error(
                "INVALID_ENCODING_TYPE",
                "Market-data encoding must be a string.",
                field="encoding",
            )
        encoding = self.encoding.strip().lower().replace("_", "-")
        if encoding not in _SUPPORTED_ENCODINGS:
            raise _market_data_error(
                "UNSUPPORTED_ENCODING",
                "Market-data CSV encoding must be UTF-8 or UTF-8 with BOM.",
                field="encoding",
                item=self.encoding,
            )
        if self.delimiter is not None and (
            not isinstance(self.delimiter, str) or self.delimiter not in _ALLOWED_DELIMITERS
        ):
            raise _market_data_error(
                "UNSUPPORTED_DELIMITER",
                "Delimiter must be comma, semicolon, tab, or vertical bar.",
                field="delimiter",
                item=str(self.delimiter),
            )
        if not isinstance(self.missing_value_policy, MissingValuePolicy):
            raise _market_data_error(
                "INVALID_MISSING_VALUE_POLICY",
                "Missing-value policy must be error or drop.",
                field="missing_value_policy",
            )
        for field_name in ("max_file_size_bytes", "max_rows"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise _market_data_error(
                    "INVALID_MARKET_DATA_LIMIT",
                    "Market-data limits must be positive integers.",
                    field=field_name,
                )
        object.__setattr__(self, "encoding", encoding)


@dataclass(frozen=True, slots=True)
class _ParsedRow:
    key: PriceSeriesKey
    observed_on: date
    price: Decimal
    line_number: int


class CsvMarketDataProvider:
    """Load one or more daily price series from a long-format local CSV."""

    def __init__(
        self,
        path: str | Path,
        options: CsvMarketDataOptions | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(path, (str, Path)):
            raise _market_data_error(
                "INVALID_FILE_PATH",
                "Market-data path must be a string or Path.",
                field="path",
            )
        if options is not None and not isinstance(options, CsvMarketDataOptions):
            raise _market_data_error(
                "INVALID_MARKET_DATA_OPTIONS",
                "CSV provider options have an invalid type.",
                field="options",
            )
        if clock is not None and not callable(clock):
            raise _market_data_error(
                "INVALID_PROVIDER_CLOCK",
                "Provider clock must be callable.",
                field="clock",
            )

        self._path = Path(path)
        self._options = options or CsvMarketDataOptions()
        self._clock = clock or _utc_now

    @property
    def provider_name(self) -> str:
        """Return the stable local provider identifier."""

        return "csv-local"

    @property
    def path(self) -> Path:
        """Return the configured local source path."""

        return self._path

    @property
    def options(self) -> CsvMarketDataOptions:
        """Return immutable provider options."""

        return self._options

    def load(self) -> MarketDataLoadResult:
        """Read, validate, normalize, and group all series from the CSV source."""

        raw_content = self._read_source()
        source_name = str(self.path)
        try:
            text = raw_content.decode(self.options.encoding)
        except UnicodeDecodeError as error:
            raise _market_data_error(
                "INVALID_FILE_ENCODING",
                "Market-data CSV could not be decoded as UTF-8.",
                field="encoding",
                item=self.options.encoding,
                source_name=source_name,
            ) from error
        text = text.removeprefix("\ufeff")
        if not text.strip():
            raise _market_data_error(
                "EMPTY_MARKET_DATA_FILE",
                "Market-data CSV is empty.",
                source_name=source_name,
            )

        delimiter = self.options.delimiter or _detect_delimiter(text)
        records = _read_records(text, delimiter, source_name)
        header_line, headers, data_records = _split_header(records, source_name)
        mappings, warnings = _map_columns(headers, header_line, source_name)

        parsed_rows: list[_ParsedRow] = []
        errors: list[MarketDataIssue] = []
        data_row_count = 0
        for line_number, record in data_records:
            if _is_blank_record(record):
                continue
            data_row_count += 1
            if data_row_count > self.options.max_rows:
                raise _market_data_error(
                    "MARKET_DATA_ROW_LIMIT_EXCEEDED",
                    "Market-data CSV exceeds the configured row limit.",
                    item=str(self.options.max_rows),
                    source_name=source_name,
                )
            parsed, row_warnings, row_errors = _parse_row(
                line_number=line_number,
                record=record,
                headers=headers,
                mappings=mappings,
                missing_value_policy=self.options.missing_value_policy,
            )
            warnings.extend(row_warnings)
            errors.extend(row_errors)
            if parsed is not None:
                parsed_rows.append(parsed)

        if not data_row_count:
            raise _market_data_error(
                "NO_MARKET_DATA_ROWS",
                "Market-data CSV contains a header but no data rows.",
                source_name=source_name,
            )

        unique_rows, duplicate_errors = _reject_duplicates(parsed_rows)
        errors.extend(duplicate_errors)
        if errors:
            raise MarketDataError(*errors, source_name=source_name)
        if not unique_rows:
            raise _market_data_error(
                "NO_PRICE_OBSERVATIONS",
                "No price observation remains after applying the missing-value policy.",
                source_name=source_name,
            )

        series, order_warnings = _build_series(unique_rows)
        warnings.extend(order_warnings)
        loaded_at = self._clock()
        if not isinstance(loaded_at, datetime) or loaded_at.tzinfo is None:
            raise _market_data_error(
                "INVALID_PROVIDER_CLOCK",
                "Provider clock must return a timezone-aware datetime.",
                field="clock",
                source_name=source_name,
            )

        observation_count = sum(len(item.observations) for item in series)
        metadata = MarketDataMetadata(
            provider_name=self.provider_name,
            source_name=source_name,
            frequency=DataFrequency.DAILY,
            loaded_at=loaded_at,
            content_hash=hashlib.sha256(raw_content).hexdigest(),
            start_date=min(item.start_date for item in series),
            end_date=max(item.end_date for item in series),
            observation_count=observation_count,
            series_count=len(series),
            missing_value_policy=self.options.missing_value_policy,
            dropped_rows=sum(problem.issue.code == "MISSING_PRICE_DROPPED" for problem in warnings),
        )
        return MarketDataLoadResult(
            data=MarketDataSet(series=series, metadata=metadata),
            issues=tuple(warnings),
        )

    def _read_source(self) -> bytes:
        source_name = str(self.path)
        try:
            file_size = self.path.stat().st_size
        except FileNotFoundError as error:
            raise _market_data_error(
                "FILE_NOT_FOUND",
                "Market-data CSV file was not found.",
                field="path",
                item=source_name,
                source_name=source_name,
            ) from error
        except OSError as error:
            raise _market_data_error(
                "FILE_READ_ERROR",
                "Market-data CSV could not be inspected.",
                field="path",
                item=source_name,
                source_name=source_name,
            ) from error
        if file_size > self.options.max_file_size_bytes:
            raise _market_data_error(
                "MARKET_DATA_FILE_TOO_LARGE",
                "Market-data CSV exceeds the configured file-size limit.",
                item=str(file_size),
                source_name=source_name,
            )
        try:
            return self.path.read_bytes()
        except OSError as error:
            raise _market_data_error(
                "FILE_READ_ERROR",
                "Market-data CSV could not be read.",
                field="path",
                item=source_name,
                source_name=source_name,
            ) from error


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
        raise _market_data_error(
            "MALFORMED_MARKET_DATA_CSV",
            "Market-data CSV contains malformed quoting or fields.",
            item=str(error),
            source_name=source_name,
        ) from error
    return tuple(records)


def _split_header(
    records: tuple[tuple[int, tuple[str, ...]], ...],
    source_name: str,
) -> tuple[int, tuple[str, ...], tuple[tuple[int, tuple[str, ...]], ...]]:
    for index, (line_number, record) in enumerate(records):
        if not _is_blank_record(record):
            return line_number, record, records[index + 1 :]
    raise _market_data_error(
        "EMPTY_MARKET_DATA_FILE",
        "Market-data CSV is empty.",
        source_name=source_name,
    )


def _map_columns(
    headers: tuple[str, ...],
    header_line: int,
    source_name: str,
) -> tuple[tuple[str | None, ...], list[MarketDataIssue]]:
    if not headers or any(not value.strip() for value in headers):
        raise _market_data_error(
            "EMPTY_MARKET_DATA_COLUMN",
            "Market-data header contains an empty column name.",
            field="header",
            line_number=header_line,
            source_name=source_name,
        )
    normalized = tuple(_normalize_token(value) for value in headers)
    duplicate_source = _first_duplicate(normalized)
    if duplicate_source is not None:
        raise _market_data_error(
            "DUPLICATE_MARKET_DATA_COLUMN",
            "Market-data header contains duplicate normalized columns.",
            field="header",
            item=duplicate_source,
            line_number=header_line,
            source_name=source_name,
        )
    mappings = tuple(_HEADER_ALIASES.get(value) for value in normalized)
    canonical = tuple(value for value in mappings if value is not None)
    duplicate_mapping = _first_duplicate(canonical)
    if duplicate_mapping is not None:
        raise _market_data_error(
            "DUPLICATE_MARKET_DATA_MAPPING",
            "More than one source column maps to the same market-data field.",
            field="header",
            item=duplicate_mapping,
            line_number=header_line,
            source_name=source_name,
        )
    missing = tuple(value for value in _REQUIRED_COLUMNS if value not in canonical)
    if missing:
        raise _market_data_error(
            "MISSING_MARKET_DATA_COLUMNS",
            "Market-data header is missing required columns.",
            field="header",
            item=", ".join(missing),
            line_number=header_line,
            source_name=source_name,
        )
    extras = tuple(headers[index] for index, value in enumerate(mappings) if value is None)
    warnings: list[MarketDataIssue] = []
    if extras:
        warnings.append(
            _located_issue(
                ValidationSeverity.WARNING,
                "EXTRA_MARKET_DATA_COLUMNS_IGNORED",
                "Unmapped market-data columns were ignored.",
                field="header",
                item=", ".join(extras),
                line_number=header_line,
            )
        )
    return mappings, warnings


def _parse_row(
    *,
    line_number: int,
    record: tuple[str, ...],
    headers: tuple[str, ...],
    mappings: tuple[str | None, ...],
    missing_value_policy: MissingValuePolicy,
) -> tuple[_ParsedRow | None, list[MarketDataIssue], list[MarketDataIssue]]:
    warnings: list[MarketDataIssue] = []
    errors: list[MarketDataIssue] = []
    values = record[: len(headers)] + ("",) * max(0, len(headers) - len(record))
    if len(record) > len(headers):
        errors.append(
            _located_issue(
                ValidationSeverity.ERROR,
                "TOO_MANY_MARKET_DATA_FIELDS",
                "Market-data row contains more values than the header defines.",
                item=str(len(record) - len(headers)),
                line_number=line_number,
            )
        )
    canonical = {
        mapping: values[index].strip()
        for index, mapping in enumerate(mappings)
        if mapping is not None
    }
    for field in ("ticker", "date", "currency"):
        if not canonical.get(field, ""):
            errors.append(
                _located_issue(
                    ValidationSeverity.ERROR,
                    "MISSING_MARKET_DATA_VALUE",
                    "Required market-data value is missing.",
                    field=field,
                    line_number=line_number,
                )
            )

    price_text = canonical.get("price", "")
    if not price_text:
        if missing_value_policy is MissingValuePolicy.DROP:
            warnings.append(
                _located_issue(
                    ValidationSeverity.WARNING,
                    "MISSING_PRICE_DROPPED",
                    "Row with an absent price was dropped by explicit policy.",
                    field="price",
                    item=canonical.get("ticker") or None,
                    line_number=line_number,
                )
            )
        else:
            errors.append(
                _located_issue(
                    ValidationSeverity.ERROR,
                    "MISSING_PRICE",
                    "Price is required by the active missing-value policy.",
                    field="price",
                    item=canonical.get("ticker") or None,
                    line_number=line_number,
                )
            )

    key = _parse_key(
        canonical.get("ticker", ""),
        canonical.get("currency", ""),
        line_number,
        errors,
    )
    observed_on = _parse_date(canonical.get("date", ""), line_number, errors)
    price = _parse_price(price_text, line_number, errors)
    if errors or key is None or observed_on is None or price is None:
        return None, warnings, errors
    return (
        _ParsedRow(
            key=key,
            observed_on=observed_on,
            price=price,
            line_number=line_number,
        ),
        warnings,
        errors,
    )


def _parse_key(
    ticker: str,
    currency_code: str,
    line_number: int,
    errors: list[MarketDataIssue],
) -> PriceSeriesKey | None:
    currency: Currency | None = None
    if currency_code:
        try:
            currency = Currency(currency_code)
        except DomainValidationError as error:
            errors.extend(
                MarketDataIssue(issue=value, line_number=line_number) for value in error.issues
            )
    if not ticker or currency is None:
        return None
    try:
        return PriceSeriesKey(ticker=ticker, currency=currency)
    except DomainValidationError as error:
        errors.extend(
            MarketDataIssue(issue=value, line_number=line_number) for value in error.issues
        )
        return None


def _parse_date(
    value: str,
    line_number: int,
    errors: list[MarketDataIssue],
) -> date | None:
    if not value:
        return None
    if not _ISO_DATE_PATTERN.fullmatch(value):
        errors.append(
            _located_issue(
                ValidationSeverity.ERROR,
                "INVALID_PRICE_DATE",
                "Price date must use the ISO YYYY-MM-DD format.",
                field="date",
                item=value,
                line_number=line_number,
            )
        )
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(
            _located_issue(
                ValidationSeverity.ERROR,
                "INVALID_PRICE_DATE",
                "Price date is not a valid calendar date.",
                field="date",
                item=value,
                line_number=line_number,
            )
        )
        return None


def _parse_price(
    value: str,
    line_number: int,
    errors: list[MarketDataIssue],
) -> Decimal | None:
    if not value:
        return None
    try:
        price = Decimal(value)
    except InvalidOperation:
        errors.append(
            _located_issue(
                ValidationSeverity.ERROR,
                "INVALID_PRICE_DECIMAL",
                "Price must be a decimal number using a dot separator.",
                field="price",
                item=value,
                line_number=line_number,
            )
        )
        return None
    try:
        validate_price(price)
    except DomainValidationError as error:
        errors.extend(MarketDataIssue(issue=item, line_number=line_number) for item in error.issues)
        return None
    return price


def _reject_duplicates(
    rows: list[_ParsedRow],
) -> tuple[list[_ParsedRow], list[MarketDataIssue]]:
    seen: set[tuple[PriceSeriesKey, date]] = set()
    accepted: list[_ParsedRow] = []
    errors: list[MarketDataIssue] = []
    for row in rows:
        identity = (row.key, row.observed_on)
        if identity in seen:
            errors.append(
                _located_issue(
                    ValidationSeverity.ERROR,
                    "DUPLICATE_PRICE_OBSERVATION",
                    "Ticker, currency, and date identify more than one price.",
                    field="date",
                    item=f"{row.key.ticker}:{row.key.currency.code}:{row.observed_on.isoformat()}",
                    line_number=row.line_number,
                )
            )
            continue
        seen.add(identity)
        accepted.append(row)
    return accepted, errors


def _build_series(
    rows: list[_ParsedRow],
) -> tuple[tuple[PriceSeries, ...], list[MarketDataIssue]]:
    grouped: dict[PriceSeriesKey, list[_ParsedRow]] = defaultdict(list)
    for row in rows:
        grouped[row.key].append(row)

    warnings: list[MarketDataIssue] = []
    series: list[PriceSeries] = []
    for key in sorted(grouped):
        source_rows = grouped[key]
        ordered_rows = sorted(source_rows, key=lambda item: item.observed_on)
        if source_rows != ordered_rows:
            warnings.append(
                _located_issue(
                    ValidationSeverity.WARNING,
                    "PRICE_ROWS_REORDERED",
                    "Price rows were reordered chronologically.",
                    field="date",
                    item=f"{key.ticker}:{key.currency.code}",
                )
            )
        observations = tuple(
            PriceObservation(observed_on=item.observed_on, price=item.price)
            for item in ordered_rows
        )
        series.append(
            PriceSeries(
                key=key,
                frequency=DataFrequency.DAILY,
                observations=observations,
            )
        )
    return tuple(series), warnings


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


def _first_duplicate(values: tuple[str, ...]) -> str | None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None


def _is_blank_record(record: tuple[str, ...]) -> bool:
    return not record or all(not value.strip() for value in record)


def _located_issue(
    severity: ValidationSeverity,
    code: str,
    message: str,
    *,
    field: str | None = None,
    item: str | None = None,
    line_number: int | None = None,
) -> MarketDataIssue:
    return MarketDataIssue(
        issue=ValidationIssue(
            severity=severity,
            code=code,
            message=message,
            field=field,
            item=item,
        ),
        line_number=line_number,
    )


def _market_data_error(
    code: str,
    message: str,
    *,
    field: str | None = None,
    item: str | None = None,
    line_number: int | None = None,
    source_name: str | None = None,
) -> MarketDataError:
    return MarketDataError(
        _located_issue(
            ValidationSeverity.ERROR,
            code,
            message,
            field=field,
            item=item,
            line_number=line_number,
        ),
        source_name=source_name,
    )


def _utc_now() -> datetime:
    return datetime.now(UTC)
