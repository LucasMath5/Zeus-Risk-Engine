"""Structured validation issues and domain validation failures."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Never

_ISSUE_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


class ValidationSeverity(StrEnum):
    """Severity assigned to a structured validation issue."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A stable, machine-readable problem accompanied by a user-facing message."""

    severity: ValidationSeverity
    code: str
    message: str
    field: str | None = None
    item: str | None = None

    def __post_init__(self) -> None:
        """Protect the validation contract from malformed issue definitions."""

        if not isinstance(self.severity, ValidationSeverity):
            raise TypeError("severity must be a ValidationSeverity")
        if not isinstance(self.code, str) or not _ISSUE_CODE_PATTERN.fullmatch(self.code):
            raise ValueError("code must use uppercase letters, digits, and underscores")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message must be a non-empty string")

        object.__setattr__(self, "message", self.message.strip())
        object.__setattr__(self, "field", _normalize_optional_text(self.field, "field"))
        object.__setattr__(self, "item", _normalize_optional_text(self.item, "item"))


class DomainValidationError(ValueError):
    """Raised when invalid input cannot form a valid domain object or result."""

    def __init__(self, *issues: ValidationIssue) -> None:
        if not issues:
            raise ValueError("DomainValidationError requires at least one issue")
        if any(issue.severity is not ValidationSeverity.ERROR for issue in issues):
            raise ValueError("DomainValidationError only accepts error-severity issues")

        self.issues = tuple(issues)
        description = "; ".join(f"{issue.code}: {issue.message}" for issue in self.issues)
        super().__init__(description)

    @property
    def primary_issue(self) -> ValidationIssue:
        """Return the first issue for simple boundaries that display one problem."""

        return self.issues[0]


def raise_validation_error(
    code: str,
    message: str,
    *,
    field: str | None = None,
    item: str | None = None,
) -> Never:
    """Raise a domain failure containing one structured error issue."""

    raise DomainValidationError(
        ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code=code,
            message=message,
            field=field,
            item=item,
        )
    )


def _normalize_optional_text(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")

    normalized = value.strip()
    return normalized or None
