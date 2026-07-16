"""Unit tests for structured analytics failures."""

from __future__ import annotations

from typing import cast

import pytest

from zeus_risk.domain import ValidationIssue, ValidationSeverity
from zeus_risk.exceptions import AnalyticsError


def _issue(severity: ValidationSeverity) -> ValidationIssue:
    return ValidationIssue(severity, "SYNTHETIC_ANALYTICS", "Synthetic analytics error")


def test_analytics_error_requires_typed_error_issues() -> None:
    with pytest.raises(ValueError, match="at least one"):
        AnalyticsError()
    with pytest.raises(ValueError, match="error-severity"):
        AnalyticsError(_issue(ValidationSeverity.WARNING))
    with pytest.raises(TypeError, match="ValidationIssue"):
        AnalyticsError(cast(ValidationIssue, object()))


def test_analytics_error_exposes_primary_issue() -> None:
    issue = _issue(ValidationSeverity.ERROR)

    error = AnalyticsError(issue)

    assert error.primary_issue is issue
    assert str(error) == "SYNTHETIC_ANALYTICS: Synthetic analytics error"
