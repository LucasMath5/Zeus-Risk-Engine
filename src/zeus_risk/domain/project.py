"""Immutable desktop-project contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from zeus_risk.domain.analytics import ReturnMethod
from zeus_risk.domain.risk import HistoricalVaRConfiguration
from zeus_risk.domain.validation import raise_validation_error

PROJECT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class DesktopProject:
    """Restorable references and risk settings for one local desktop project."""

    name: str
    portfolio_path: Path
    market_data_path: Path
    risk_configuration: HistoricalVaRConfiguration
    worksheet_name: str | None = None
    return_method: ReturnMethod = ReturnMethod.SIMPLE

    def __post_init__(self) -> None:
        normalized_name = _normalize_name(self.name)
        _validate_file_reference(self.portfolio_path, "portfolio_path")
        _validate_file_reference(self.market_data_path, "market_data_path")
        if not isinstance(self.risk_configuration, HistoricalVaRConfiguration):
            raise_validation_error(
                "INVALID_PROJECT_RISK_CONFIGURATION",
                "Project risk configuration must be a HistoricalVaRConfiguration.",
                field="risk_configuration",
            )
        normalized_worksheet = _normalize_worksheet(self.worksheet_name)
        if not isinstance(self.return_method, ReturnMethod):
            raise_validation_error(
                "INVALID_PROJECT_RETURN_METHOD",
                "Project return method must be a ReturnMethod value.",
                field="return_method",
                item=str(self.return_method),
            )

        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "worksheet_name", normalized_worksheet)


def _normalize_name(name: str) -> str:
    if not isinstance(name, str):
        raise_validation_error(
            "INVALID_PROJECT_NAME_TYPE",
            "Project name must be a string.",
            field="name",
        )
    normalized = name.strip()
    if not normalized:
        raise_validation_error(
            "EMPTY_PROJECT_NAME",
            "Project name must not be empty.",
            field="name",
        )
    if len(normalized) > 120:
        raise_validation_error(
            "PROJECT_NAME_TOO_LONG",
            "Project name must contain at most 120 characters.",
            field="name",
        )
    return normalized


def _validate_file_reference(path: Path, field: str) -> None:
    if not isinstance(path, Path):
        raise_validation_error(
            "INVALID_PROJECT_PATH_TYPE",
            "Project file references must be pathlib Path values.",
            field=field,
        )
    if path == Path() or "\x00" in str(path):
        raise_validation_error(
            "INVALID_PROJECT_PATH",
            "Project file reference must identify a file path.",
            field=field,
            item=str(path),
        )


def _normalize_worksheet(worksheet_name: str | None) -> str | None:
    if worksheet_name is None:
        return None
    if not isinstance(worksheet_name, str):
        raise_validation_error(
            "INVALID_PROJECT_WORKSHEET_TYPE",
            "Project worksheet name must be a string or null.",
            field="worksheet_name",
        )
    normalized = worksheet_name.strip()
    if not normalized:
        raise_validation_error(
            "EMPTY_PROJECT_WORKSHEET",
            "Project worksheet name must not be blank.",
            field="worksheet_name",
        )
    return normalized
