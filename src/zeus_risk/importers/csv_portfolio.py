"""Validated CSV adapter for portfolio positions."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path

from zeus_risk.importers.models import ImportResult
from zeus_risk.importers.tabular import (
    TabularRecord,
    build_import_result,
    import_error,
    is_blank_record,
    map_columns,
)

_ALLOWED_DELIMITERS = (",", ";", "\t", "|")
_SUPPORTED_ENCODINGS = ("utf-8", "utf-8-sig")


@dataclass(frozen=True, slots=True)
class CsvImportOptions:
    """Explicit and reproducible CSV decoding options."""

    encoding: str = "utf-8-sig"
    delimiter: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.encoding, str):
            raise import_error(
                "INVALID_ENCODING_TYPE",
                "CSV encoding must be a string.",
                field="encoding",
            )
        normalized_encoding = self.encoding.strip().lower().replace("_", "-")
        if normalized_encoding not in _SUPPORTED_ENCODINGS:
            raise import_error(
                "UNSUPPORTED_ENCODING",
                "CSV encoding must be UTF-8 or UTF-8 with BOM.",
                field="encoding",
                item=self.encoding,
            )
        if self.delimiter is not None and not isinstance(self.delimiter, str):
            raise import_error(
                "INVALID_DELIMITER_TYPE",
                "CSV delimiter must be a string or None.",
                field="delimiter",
            )
        if self.delimiter is not None and self.delimiter not in _ALLOWED_DELIMITERS:
            raise import_error(
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
            raise import_error(
                "FILE_NOT_FOUND",
                "Portfolio CSV file was not found.",
                field="path",
                item=source_name,
                source_name=source_name,
            ) from error
        except UnicodeDecodeError as error:
            raise import_error(
                "INVALID_FILE_ENCODING",
                "Portfolio CSV could not be decoded as UTF-8.",
                field="encoding",
                item=self.options.encoding,
                source_name=source_name,
            ) from error
        except OSError as error:
            raise import_error(
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
            raise import_error(
                "INVALID_CSV_TEXT",
                "CSV content must be text.",
                source_name=source_name,
            )
        if not isinstance(portfolio_name, str) or not portfolio_name.strip():
            raise import_error(
                "INVALID_PORTFOLIO_NAME",
                "Portfolio name must be a non-empty string.",
                field="name",
                source_name=source_name,
            )

        normalized_text = text.removeprefix("\ufeff")
        if not normalized_text.strip():
            raise import_error(
                "EMPTY_FILE",
                "Portfolio CSV is empty.",
                source_name=source_name,
            )

        delimiter = self.options.delimiter or _detect_delimiter(normalized_text)
        records = _read_records(normalized_text, delimiter, source_name)
        header_record, data_records = _split_header_and_data(records, source_name)
        column_mappings, global_issues = map_columns(header_record.values, source_name)

        return build_import_result(
            source_name=source_name,
            portfolio_name=portfolio_name,
            column_mappings=column_mappings,
            records=data_records,
            global_issues=global_issues,
            encoding=self.options.encoding,
            delimiter=delimiter,
        )


def _read_records(
    text: str,
    delimiter: str,
    source_name: str,
) -> tuple[TabularRecord, ...]:
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
    records: list[TabularRecord] = []
    try:
        for record in reader:
            records.append(TabularRecord(line_number=reader.line_num, values=tuple(record)))
    except csv.Error as error:
        raise import_error(
            "MALFORMED_CSV",
            "Portfolio CSV contains malformed quoting or fields.",
            item=str(error),
            source_name=source_name,
        ) from error
    return tuple(records)


def _split_header_and_data(
    records: tuple[TabularRecord, ...],
    source_name: str,
) -> tuple[TabularRecord, tuple[TabularRecord, ...]]:
    for index, record in enumerate(records):
        if not is_blank_record(record.values):
            return record, records[index + 1 :]

    raise import_error(
        "EMPTY_FILE",
        "Portfolio CSV is empty.",
        source_name=source_name,
    )


def _detect_delimiter(text: str) -> str:
    sample_lines = [line for line in text.splitlines() if line.strip()][:25]
    sample = "\n".join(sample_lines)[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(_ALLOWED_DELIMITERS))
    except csv.Error:
        return ","
    return dialect.delimiter
