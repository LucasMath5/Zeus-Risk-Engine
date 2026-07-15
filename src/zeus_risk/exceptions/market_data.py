"""Specific failures for market-data loading, alignment, and cache operations."""

from __future__ import annotations

from zeus_risk.domain.market_data import MarketDataIssue
from zeus_risk.domain.validation import ValidationSeverity


class MarketDataError(Exception):
    """A market-data operation that could not produce a valid result."""

    def __init__(
        self,
        *problems: MarketDataIssue,
        source_name: str | None = None,
    ) -> None:
        if not problems:
            raise ValueError("MarketDataError requires at least one problem")
        if any(not isinstance(problem, MarketDataIssue) for problem in problems):
            raise TypeError("problems must be MarketDataIssue values")
        if any(problem.issue.severity is not ValidationSeverity.ERROR for problem in problems):
            raise ValueError("MarketDataError accepts only error-severity problems")

        self.problems = tuple(problems)
        self.source_name = source_name
        source_suffix = f" [{source_name}]" if source_name else ""
        description = "; ".join(
            f"{problem.issue.code}: {problem.issue.message}" for problem in problems
        )
        super().__init__(f"{description}{source_suffix}")

    @property
    def primary_issue(self) -> MarketDataIssue:
        """Return the first problem for simple presentation boundaries."""

        return self.problems[0]
