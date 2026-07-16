"""Structured failures for market-risk calculations."""

from __future__ import annotations

from typing import Never

from zeus_risk.domain.validation import ValidationIssue, ValidationSeverity


class RiskCalculationError(Exception):
    """A risk calculation that could not produce a valid result."""

    def __init__(self, *issues: ValidationIssue) -> None:
        if not issues:
            raise ValueError("RiskCalculationError requires at least one issue")
        if any(not isinstance(issue, ValidationIssue) for issue in issues):
            raise TypeError("issues must be ValidationIssue values")
        if any(issue.severity is not ValidationSeverity.ERROR for issue in issues):
            raise ValueError("RiskCalculationError accepts only error-severity issues")

        self.issues = tuple(issues)
        description = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        super().__init__(description)

    @property
    def primary_issue(self) -> ValidationIssue:
        """Return the first problem for simple presentation boundaries."""

        return self.issues[0]


def raise_risk_error(
    code: str,
    message: str,
    *,
    field: str | None = None,
    item: str | None = None,
) -> Never:
    """Raise one structured market-risk failure."""

    raise RiskCalculationError(
        ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code=code,
            message=message,
            field=field,
            item=item,
        )
    )
