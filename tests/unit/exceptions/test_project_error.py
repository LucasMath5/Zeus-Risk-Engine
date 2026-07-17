"""Tests for structured project-file failures."""

from __future__ import annotations

import pytest

from zeus_risk.domain import ValidationIssue, ValidationSeverity
from zeus_risk.exceptions import ProjectFileError


def test_project_file_error_preserves_issues_and_source() -> None:
    issue = ValidationIssue(
        ValidationSeverity.ERROR,
        "PROJECT_FILE_NOT_FOUND",
        "Project file was not found.",
    )

    error = ProjectFileError(issue, source_name="project.json")

    assert error.primary_issue is issue
    assert error.issues == (issue,)
    assert error.source_name == "project.json"
    assert "PROJECT_FILE_NOT_FOUND" in str(error)


def test_project_file_error_requires_error_issue() -> None:
    warning = ValidationIssue(
        ValidationSeverity.WARNING,
        "PROJECT_WARNING",
        "Project warning.",
    )

    with pytest.raises(ValueError, match="error-severity"):
        ProjectFileError(warning)


def test_project_file_error_requires_issue() -> None:
    with pytest.raises(ValueError, match="at least one"):
        ProjectFileError()
