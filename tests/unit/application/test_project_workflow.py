"""Tests for desktop-project application coordination."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from zeus_risk.application import ProjectWorkflow
from zeus_risk.domain import HistoricalVaRConfiguration


def test_creates_saves_and_restores_project_snapshot(tmp_path: Path) -> None:
    portfolio = tmp_path / "portfolio.csv"
    market_data = tmp_path / "prices.csv"
    portfolio.write_text("portfolio", encoding="utf-8")
    market_data.write_text("prices", encoding="utf-8")
    workflow = ProjectWorkflow()
    configuration = HistoricalVaRConfiguration(Decimal("0.5"), window=2)

    project = workflow.create_project(
        name="Desktop Risk",
        portfolio_path=portfolio,
        market_data_path=market_data,
        risk_configuration=configuration,
    )
    destination = workflow.save_project(project, tmp_path / "project.zeus.json")
    restored = workflow.load_project(destination)

    assert restored == project
    assert destination.is_file()
