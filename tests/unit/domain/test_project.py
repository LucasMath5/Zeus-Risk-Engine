"""Unit tests for the immutable desktop-project contract."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest

from zeus_risk.domain import (
    DesktopProject,
    DomainValidationError,
    HistoricalVaRConfiguration,
    ReturnMethod,
)


def _configuration() -> HistoricalVaRConfiguration:
    return HistoricalVaRConfiguration(Decimal("0.5"), window=2)


def test_normalizes_project_name_and_worksheet() -> None:
    project = DesktopProject(
        name="  Daily Risk  ",
        portfolio_path=Path("portfolio.csv"),
        market_data_path=Path("prices.csv"),
        risk_configuration=_configuration(),
        worksheet_name="  Positions  ",
    )

    assert project.name == "Daily Risk"
    assert project.worksheet_name == "Positions"
    assert project.return_method is ReturnMethod.SIMPLE


@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("", "EMPTY_PROJECT_NAME"),
        ("x" * 121, "PROJECT_NAME_TOO_LONG"),
    ],
)
def test_rejects_invalid_project_names(name: str, code: str) -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        DesktopProject(
            name=name,
            portfolio_path=Path("portfolio.csv"),
            market_data_path=Path("prices.csv"),
            risk_configuration=_configuration(),
        )

    assert exc_info.value.primary_issue.code == code


def test_rejects_invalid_project_boundary_types() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        DesktopProject(
            name="Risk",
            portfolio_path=cast(Path, "portfolio.csv"),
            market_data_path=Path("prices.csv"),
            risk_configuration=_configuration(),
        )
    assert exc_info.value.primary_issue.code == "INVALID_PROJECT_PATH_TYPE"

    with pytest.raises(DomainValidationError) as exc_info:
        DesktopProject(
            name="Risk",
            portfolio_path=Path("portfolio.csv"),
            market_data_path=Path("prices.csv"),
            risk_configuration=cast(HistoricalVaRConfiguration, object()),
        )
    assert exc_info.value.primary_issue.code == "INVALID_PROJECT_RISK_CONFIGURATION"

    with pytest.raises(DomainValidationError) as exc_info:
        DesktopProject(
            name="Risk",
            portfolio_path=Path("portfolio.csv"),
            market_data_path=Path("prices.csv"),
            risk_configuration=_configuration(),
            return_method=cast(ReturnMethod, "simple"),
        )
    assert exc_info.value.primary_issue.code == "INVALID_PROJECT_RETURN_METHOD"


def test_rejects_blank_worksheet_name() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        DesktopProject(
            name="Risk",
            portfolio_path=Path("portfolio.xlsx"),
            market_data_path=Path("prices.csv"),
            risk_configuration=_configuration(),
            worksheet_name="  ",
        )

    assert exc_info.value.primary_issue.code == "EMPTY_PROJECT_WORKSHEET"
