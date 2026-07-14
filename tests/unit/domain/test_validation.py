"""Tests for structured domain validation contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from zeus_risk.domain import DomainValidationError, ValidationIssue, ValidationSeverity


def test_validation_issue_normalizes_optional_text() -> None:
    issue = ValidationIssue(
        severity=ValidationSeverity.WARNING,
        code="MISSING_SECTOR",
        message="  Sector was not provided.  ",
        field=" sector ",
        item=" PETR4 ",
    )

    assert issue.message == "Sector was not provided."
    assert issue.field == "sector"
    assert issue.item == "PETR4"


@pytest.mark.parametrize("code", ["", "lower_case", "HAS-HYPHEN", "1STARTS_WITH_NUMBER"])
def test_validation_issue_rejects_unstable_code_formats(code: str) -> None:
    with pytest.raises(ValueError, match="uppercase"):
        ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code=code,
            message="Invalid issue code.",
        )


def test_validation_issue_rejects_invalid_severity_and_message() -> None:
    with pytest.raises(TypeError, match="ValidationSeverity"):
        ValidationIssue(
            severity=cast(ValidationSeverity, "error"),
            code="INVALID_SEVERITY",
            message="Invalid severity.",
        )
    with pytest.raises(ValueError, match="non-empty"):
        ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code="EMPTY_MESSAGE",
            message="   ",
        )


def test_validation_issue_rejects_invalid_optional_text_type() -> None:
    with pytest.raises(TypeError, match="field"):
        ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code="INVALID_FIELD",
            message="Invalid field type.",
            field=cast(str, 1),
        )


def test_validation_issue_is_immutable() -> None:
    issue = ValidationIssue(
        severity=ValidationSeverity.INFO,
        code="NORMALIZED_TICKER",
        message="Ticker was normalized.",
    )

    attribute = "code"
    with pytest.raises(FrozenInstanceError):
        setattr(issue, attribute, "CHANGED")


def test_domain_validation_error_preserves_all_issues() -> None:
    first = ValidationIssue(
        severity=ValidationSeverity.ERROR,
        code="FIRST_ERROR",
        message="First problem.",
    )
    second = ValidationIssue(
        severity=ValidationSeverity.ERROR,
        code="SECOND_ERROR",
        message="Second problem.",
    )

    error = DomainValidationError(first, second)

    assert error.issues == (first, second)
    assert error.primary_issue is first
    assert str(error) == "FIRST_ERROR: First problem.; SECOND_ERROR: Second problem."


def test_domain_validation_error_rejects_non_error_issue() -> None:
    warning = ValidationIssue(
        severity=ValidationSeverity.WARNING,
        code="WARNING_ONLY",
        message="This is not fatal.",
    )

    with pytest.raises(ValueError, match="error-severity"):
        DomainValidationError(warning)


def test_domain_validation_error_requires_an_issue() -> None:
    with pytest.raises(ValueError, match="at least one"):
        DomainValidationError()
