"""Unit tests for structured market-data operation failures."""

from __future__ import annotations

from typing import cast

import pytest

from zeus_risk.domain import MarketDataIssue, ValidationIssue, ValidationSeverity
from zeus_risk.exceptions import MarketDataError


def _problem(severity: ValidationSeverity) -> MarketDataIssue:
    return MarketDataIssue(ValidationIssue(severity, "SYNTHETIC", "Synthetic market-data problem"))


def test_requires_at_least_one_error_problem() -> None:
    with pytest.raises(ValueError, match="at least one"):
        MarketDataError()
    with pytest.raises(ValueError, match="only error-severity"):
        MarketDataError(_problem(ValidationSeverity.WARNING))
    with pytest.raises(TypeError, match="MarketDataIssue"):
        MarketDataError(cast(MarketDataIssue, object()))


def test_exposes_primary_problem_and_source_in_message() -> None:
    problem = _problem(ValidationSeverity.ERROR)

    error = MarketDataError(problem, source_name="prices.csv")

    assert error.primary_issue is problem
    assert str(error) == "SYNTHETIC: Synthetic market-data problem [prices.csv]"
