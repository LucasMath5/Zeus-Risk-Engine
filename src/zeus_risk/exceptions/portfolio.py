"""Portfolio import boundary exceptions."""

from __future__ import annotations

from zeus_risk.domain import ValidationIssue, ValidationSeverity


class PortfolioImportError(Exception):
    """A structural failure that prevents a portfolio file from being reviewed."""

    def __init__(self, issue: ValidationIssue, *, source_name: str | None = None) -> None:
        if issue.severity is not ValidationSeverity.ERROR:
            raise ValueError("PortfolioImportError requires an error-severity issue")

        self.issue = issue
        self.source_name = source_name
        source_suffix = f" [{source_name}]" if source_name else ""
        super().__init__(f"{issue.code}: {issue.message}{source_suffix}")
