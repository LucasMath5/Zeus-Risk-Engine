"""Unit tests for structured risk-calculation failures."""

from __future__ import annotations

import pytest

from zeus_risk.domain import ValidationIssue, ValidationSeverity
from zeus_risk.exceptions import RiskCalculationError
from zeus_risk.exceptions.risk import raise_risk_error


def _issue(severity: ValidationSeverity = ValidationSeverity.ERROR) -> ValidationIssue:
    return ValidationIssue(severity, "RISK_TEST", "Risk test failure.", field="returns")


def test_exposes_structured_risk_issues() -> None:
    error = RiskCalculationError(_issue())

    assert error.primary_issue.code == "RISK_TEST"
    assert error.issues == (_issue(),)
    assert str(error) == "RISK_TEST: Risk test failure."


def test_helper_raises_one_structured_issue() -> None:
    with pytest.raises(RiskCalculationError) as exc_info:
        raise_risk_error("INSUFFICIENT_HISTORY", "More observations are required.")

    assert exc_info.value.primary_issue.code == "INSUFFICIENT_HISTORY"


def test_rejects_empty_invalid_and_non_error_issues() -> None:
    with pytest.raises(ValueError):
        RiskCalculationError()
    with pytest.raises(TypeError):
        RiskCalculationError("invalid")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        RiskCalculationError(_issue(ValidationSeverity.WARNING))
