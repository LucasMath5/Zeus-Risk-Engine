"""Application workflow for versioned local desktop projects."""

from __future__ import annotations

from pathlib import Path

from zeus_risk.domain import DesktopProject, HistoricalVaRConfiguration, ReturnMethod
from zeus_risk.projects import JsonProjectStore


class ProjectWorkflow:
    """Create, save, and restore project contracts through one injected adapter."""

    def __init__(self, store: JsonProjectStore | None = None) -> None:
        self._store = store or JsonProjectStore()

    def create_project(
        self,
        *,
        name: str,
        portfolio_path: str | Path,
        market_data_path: str | Path,
        risk_configuration: HistoricalVaRConfiguration,
        worksheet_name: str | None = None,
        return_method: ReturnMethod = ReturnMethod.SIMPLE,
    ) -> DesktopProject:
        """Create one validated, immutable desktop-project snapshot."""

        return DesktopProject(
            name=name,
            portfolio_path=Path(portfolio_path).resolve(),
            market_data_path=Path(market_data_path).resolve(),
            risk_configuration=risk_configuration,
            worksheet_name=worksheet_name,
            return_method=return_method,
        )

    def save_project(self, project: DesktopProject, path: str | Path) -> Path:
        """Persist one project through the JSON adapter."""

        return self._store.save(project, path)

    def load_project(self, path: str | Path) -> DesktopProject:
        """Restore one validated project through the JSON adapter."""

        return self._store.load(path)
