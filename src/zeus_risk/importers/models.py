"""Structured results produced by portfolio import adapters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from zeus_risk.domain import Portfolio, Position, ValidationIssue, ValidationSeverity


class ImportStatus(StrEnum):
    """Review status assigned to one imported data row."""

    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ColumnMapping:
    """Mapping between a source header and an optional canonical portfolio field."""

    source_name: str
    normalized_name: str
    canonical_name: str | None


@dataclass(frozen=True, slots=True)
class ImportedField:
    """Original source value preserved with its source-column name."""

    name: str
    value: str


@dataclass(frozen=True, slots=True)
class ImportRow:
    """One reviewable CSV row and the position it produced, when valid."""

    line_number: int
    status: ImportStatus
    raw_fields: tuple[ImportedField, ...]
    position: Position | None
    issues: tuple[ValidationIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class LocatedValidationIssue:
    """A validation issue associated with a physical line when applicable."""

    issue: ValidationIssue
    line_number: int | None


@dataclass(frozen=True, slots=True)
class ImportSummary:
    """Deterministic row counts for an import result."""

    total_rows: int
    accepted_rows: int
    valid_rows: int
    warning_rows: int
    error_rows: int

    @classmethod
    def from_rows(cls, rows: tuple[ImportRow, ...]) -> ImportSummary:
        """Build a summary without relying on mutable counters at the boundary."""

        valid_rows = sum(row.status is ImportStatus.VALID for row in rows)
        warning_rows = sum(row.status is ImportStatus.WARNING for row in rows)
        error_rows = sum(row.status is ImportStatus.ERROR for row in rows)
        accepted_rows = sum(row.position is not None for row in rows)
        return cls(
            total_rows=len(rows),
            accepted_rows=accepted_rows,
            valid_rows=valid_rows,
            warning_rows=warning_rows,
            error_rows=error_rows,
        )


@dataclass(frozen=True, slots=True)
class ImportResult:
    """Portfolio import output with provenance, review rows, and global issues."""

    source_name: str
    encoding: str | None
    delimiter: str | None
    column_mappings: tuple[ColumnMapping, ...]
    rows: tuple[ImportRow, ...]
    summary: ImportSummary
    portfolio: Portfolio | None
    issues: tuple[ValidationIssue, ...] = ()
    worksheet_name: str | None = None

    @property
    def positions(self) -> tuple[Position, ...]:
        """Return accepted positions in source order."""

        return tuple(row.position for row in self.rows if row.position is not None)

    @property
    def located_issues(self) -> tuple[LocatedValidationIssue, ...]:
        """Return global and row issues while retaining physical line numbers."""

        global_issues = tuple(
            LocatedValidationIssue(issue=issue, line_number=None) for issue in self.issues
        )
        row_issues = tuple(
            LocatedValidationIssue(issue=issue, line_number=row.line_number)
            for row in self.rows
            for issue in row.issues
        )
        return global_issues + row_issues

    @property
    def has_errors(self) -> bool:
        """Report whether any row or global issue has error severity."""

        return self.summary.error_rows > 0 or any(
            issue.severity is ValidationSeverity.ERROR for issue in self.issues
        )

    @property
    def is_partial(self) -> bool:
        """Report whether valid positions coexist with rejected rows."""

        return self.portfolio is not None and self.summary.error_rows > 0
