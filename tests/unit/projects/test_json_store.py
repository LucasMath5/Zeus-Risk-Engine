"""Tests for strict, versioned JSON project persistence."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest

from zeus_risk.domain import DesktopProject, HistoricalVaRConfiguration, ReturnMethod
from zeus_risk.exceptions import ProjectFileError
from zeus_risk.projects import JsonProjectStore


def _project(directory: Path) -> DesktopProject:
    inputs = directory / "inputs"
    inputs.mkdir()
    portfolio = inputs / "portfolio.csv"
    prices = inputs / "prices.csv"
    portfolio.write_text("portfolio", encoding="utf-8")
    prices.write_text("prices", encoding="utf-8")
    return DesktopProject(
        name="Daily Risk",
        portfolio_path=portfolio,
        market_data_path=prices,
        risk_configuration=HistoricalVaRConfiguration(Decimal("0.5"), window=2),
        return_method=ReturnMethod.LOG,
    )


def test_round_trip_uses_relative_references_inside_project_directory(
    tmp_path: Path,
) -> None:
    store = JsonProjectStore()
    project = _project(tmp_path)
    destination = tmp_path / "daily-risk.zeus.json"

    saved_path = store.save(project, destination)
    payload = json.loads(destination.read_text(encoding="utf-8"))
    restored = store.load(destination)

    assert saved_path == destination.resolve()
    assert payload["schema_version"] == "1.0"
    assert payload["portfolio"]["path"] == "inputs/portfolio.csv"
    assert payload["market_data"]["path"] == "inputs/prices.csv"
    assert restored == DesktopProject(
        name=project.name,
        portfolio_path=project.portfolio_path.resolve(),
        market_data_path=project.market_data_path.resolve(),
        risk_configuration=project.risk_configuration,
        return_method=ReturnMethod.LOG,
    )


def test_save_keeps_external_references_absolute(tmp_path: Path) -> None:
    store = JsonProjectStore()
    project = _project(tmp_path)
    project_directory = tmp_path / "project"
    project_directory.mkdir()
    destination = project_directory / "external.zeus.json"

    store.save(project, destination)
    payload = json.loads(destination.read_text(encoding="utf-8"))

    assert Path(payload["portfolio"]["path"]).is_absolute()
    assert Path(payload["market_data"]["path"]).is_absolute()


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ({"schema_version": "2.0"}, "UNSUPPORTED_PROJECT_SCHEMA_VERSION"),
        ({"unexpected": True}, "UNKNOWN_PROJECT_FIELD"),
    ],
)
def test_rejects_incompatible_or_unknown_root_fields(
    tmp_path: Path,
    mutation: dict[str, object],
    code: str,
) -> None:
    store = JsonProjectStore()
    destination = tmp_path / "project.json"
    store.save(_project(tmp_path), destination)
    payload = cast(dict[str, object], json.loads(destination.read_text(encoding="utf-8")))
    payload.update(mutation)
    destination.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ProjectFileError) as exc_info:
        store.load(destination)

    assert exc_info.value.primary_issue.code == code


def test_rejects_missing_required_field(tmp_path: Path) -> None:
    store = JsonProjectStore()
    destination = tmp_path / "project.json"
    store.save(_project(tmp_path), destination)
    payload = cast(dict[str, object], json.loads(destination.read_text(encoding="utf-8")))
    del payload["risk"]
    destination.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ProjectFileError) as exc_info:
        store.load(destination)

    assert exc_info.value.primary_issue.code == "MISSING_PROJECT_FIELD"
    assert exc_info.value.primary_issue.item == "risk"


def test_rejects_duplicate_and_malformed_json(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema_version":"1.0","schema_version":"1.0"}', encoding="utf-8")
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    store = JsonProjectStore()

    with pytest.raises(ProjectFileError) as exc_info:
        store.load(duplicate)
    assert exc_info.value.primary_issue.code == "DUPLICATE_PROJECT_FIELD"

    with pytest.raises(ProjectFileError) as exc_info:
        store.load(malformed)
    assert exc_info.value.primary_issue.code == "INVALID_PROJECT_JSON"


def test_rejects_missing_referenced_file_on_load(tmp_path: Path) -> None:
    store = JsonProjectStore()
    project = _project(tmp_path)
    destination = tmp_path / "project.json"
    store.save(project, destination)
    project.market_data_path.unlink()

    with pytest.raises(ProjectFileError) as exc_info:
        store.load(destination)

    assert exc_info.value.primary_issue.code == "PROJECT_MARKET_DATA_FILE_NOT_FOUND"


def test_rejects_missing_destination_and_invalid_project_type(tmp_path: Path) -> None:
    store = JsonProjectStore()
    project = _project(tmp_path)

    with pytest.raises(ProjectFileError) as exc_info:
        store.save(project, tmp_path / "missing" / "project.json")
    assert exc_info.value.primary_issue.code == "PROJECT_DIRECTORY_NOT_FOUND"

    with pytest.raises(TypeError, match="DesktopProject"):
        store.save(cast(DesktopProject, object()), tmp_path / "project.json")
