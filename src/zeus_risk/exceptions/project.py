"""Structured failures for versioned desktop-project files."""

from __future__ import annotations

from zeus_risk.domain import ValidationIssue, ValidationSeverity


class ProjectFileError(Exception):
    """A project-file operation that could not produce its validated contract."""

    def __init__(
        self,
        *issues: ValidationIssue,
        source_name: str | None = None,
    ) -> None:
        if not issues:
            raise ValueError("ProjectFileError requires at least one issue")
        if any(not isinstance(issue, ValidationIssue) for issue in issues):
            raise TypeError("issues must be ValidationIssue values")
        if any(issue.severity is not ValidationSeverity.ERROR for issue in issues):
            raise ValueError("ProjectFileError accepts only error-severity issues")

        self.issues = tuple(issues)
        self.source_name = source_name
        source_suffix = f" [{source_name}]" if source_name else ""
        description = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        super().__init__(f"{description}{source_suffix}")

    @property
    def primary_issue(self) -> ValidationIssue:
        """Return the first issue for presentation boundaries."""

        return self.issues[0]
