"""Integration test for a saved project through the local risk pipeline."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from zeus_risk.application import PortfolioRiskWorkflow, ProjectWorkflow
from zeus_risk.domain import HistoricalVaRConfiguration

PROJECT_ROOT = Path(__file__).parents[2]


def test_versioned_demo_project_is_loadable() -> None:
    project = ProjectWorkflow().load_project(
        PROJECT_ROOT / "assets" / "samples" / "historical-risk-demo.zeus.json"
    )

    assert project.name == "Historical Risk Demo"
    assert project.portfolio_path.name == "risk_portfolio.csv"
    assert project.market_data_path.name == "market_prices.csv"
    assert project.risk_configuration.confidence_level == Decimal("0.5")


def test_saved_project_restores_inputs_and_reproduces_historical_risk(
    tmp_path: Path,
) -> None:
    portfolio_path = PROJECT_ROOT / "assets" / "samples" / "risk_portfolio.csv"
    market_data_path = PROJECT_ROOT / "assets" / "samples" / "market_prices.csv"
    configuration = HistoricalVaRConfiguration(Decimal("0.5"), window=2)
    project_workflow = ProjectWorkflow()
    project = project_workflow.create_project(
        name="Reproducible Risk",
        portfolio_path=portfolio_path,
        market_data_path=market_data_path,
        risk_configuration=configuration,
    )
    destination = project_workflow.save_project(project, tmp_path / "risk.zeus.json")

    restored = project_workflow.load_project(destination)
    risk_workflow = PortfolioRiskWorkflow()
    imported = risk_workflow.import_portfolio(
        restored.portfolio_path,
        worksheet_name=restored.worksheet_name,
    )
    assert imported.portfolio is not None
    analysis = risk_workflow.run_historical_risk(
        imported.portfolio,
        restored.market_data_path,
        restored.risk_configuration,
        return_method=restored.return_method,
    )

    assert analysis.historical_var.value_at_risk == Decimal("0")
    assert analysis.expected_shortfall.expected_shortfall > Decimal("0")
