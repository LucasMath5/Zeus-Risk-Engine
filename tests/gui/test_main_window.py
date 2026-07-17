"""Headless integration tests for the initial desktop workflow."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import QApplication

from zeus_risk import __version__
from zeus_risk.app import MainWindow, create_application

PROJECT_ROOT = Path(__file__).parents[2]
PORTFOLIO_PATH = PROJECT_ROOT / "assets" / "samples" / "risk_portfolio.csv"
MARKET_DATA_PATH = PROJECT_ROOT / "assets" / "samples" / "market_prices.csv"


def test_application_bootstrap_is_reusable_and_configured(
    qt_application: QApplication,
) -> None:
    same_application = create_application(["ignored"])

    assert same_application is qt_application
    assert same_application.applicationName() == "Zeus Risk Engine"
    assert same_application.applicationVersion() == __version__


def test_main_window_runs_portfolio_to_expected_shortfall_flow(
    qt_application: QApplication,
) -> None:
    window = MainWindow()

    assert window.load_portfolio(PORTFOLIO_PATH)
    window.set_market_data_path(MARKET_DATA_PATH)
    window.risk_page.confidence_spin.setValue(50.0)
    window.risk_page.window_spin.setValue(2)

    assert window.run_analysis()
    assert window.portfolio_page.position_model.rowCount() == 2
    assert window.risk_page.var_value.text() == "0.0000%"
    assert window.risk_page.es_value.text() != "—"
    assert window.risk_page.success_banner.isVisibleTo(window.risk_page)
    assert "2 cenários" in window.risk_page.sample_value.text()
    assert window.statusBar().currentMessage() == "Análise histórica concluída"

    window.close()
    qt_application.processEvents()


def test_main_window_surfaces_invalid_configuration_code(
    qt_application: QApplication,
) -> None:
    window = MainWindow()
    assert window.load_portfolio(PORTFOLIO_PATH)
    window.set_market_data_path(MARKET_DATA_PATH)
    window.risk_page.confidence_spin.setValue(99.0)
    window.risk_page.window_spin.setValue(2)

    assert not window.run_analysis()
    assert "INSUFFICIENT_VAR_TAIL_OBSERVATIONS" in window.risk_page.error_banner.text()
    assert window.risk_page.error_banner.isVisibleTo(window.risk_page)
    assert window.risk_page.run_button.isEnabled()

    window.close()
    qt_application.processEvents()


def test_main_window_surfaces_structured_import_failure(
    qt_application: QApplication,
) -> None:
    window = MainWindow()

    assert not window.load_portfolio(PROJECT_ROOT / "missing.csv")
    assert "FILE_NOT_FOUND" in window.portfolio_page.error_banner.text()
    assert not window.risk_page.run_button.isEnabled()

    window.close()
    qt_application.processEvents()


def test_main_window_saves_reopens_and_marks_project_changes(
    qt_application: QApplication,
    tmp_path: Path,
) -> None:
    source_window = MainWindow()
    assert source_window.load_portfolio(PORTFOLIO_PATH)
    source_window.set_market_data_path(MARKET_DATA_PATH)
    source_window.risk_page.confidence_spin.setValue(50.0)
    source_window.risk_page.window_spin.setValue(2)
    destination = tmp_path / "daily-risk.zeus.json"

    was_dirty = source_window.is_dirty
    assert was_dirty
    dirty_title = source_window.windowTitle()
    assert dirty_title.endswith(" *")
    assert source_window.save_project(destination)
    assert source_window.project_path == destination.resolve()
    is_clean_after_save = not source_window.is_dirty
    assert is_clean_after_save
    saved_title = source_window.windowTitle()
    assert saved_title != dirty_title
    assert not saved_title.endswith(" *")

    restored_window = MainWindow()
    assert restored_window.open_project(destination)
    assert restored_window.project_path == destination.resolve()
    assert restored_window.market_data_path == MARKET_DATA_PATH.resolve()
    assert restored_window.portfolio_page.position_model.rowCount() == 2
    assert restored_window.risk_page.confidence_spin.value() == 50.0
    assert restored_window.risk_page.window_spin.value() == 2
    restored_was_clean = not restored_window.is_dirty
    assert restored_was_clean
    assert restored_window.run_analysis()

    restored_window.risk_page.horizon_spin.setValue(2)

    restored_became_dirty = restored_window.is_dirty
    assert restored_became_dirty
    assert restored_window.windowTitle().endswith(" *")

    source_window.close()
    restored_window.close()
    qt_application.processEvents()


def test_main_window_surfaces_project_schema_failure_without_replacing_state(
    qt_application: QApplication,
    tmp_path: Path,
) -> None:
    window = MainWindow()
    assert window.load_portfolio(PORTFOLIO_PATH)
    original_result = window.import_result
    malformed_project = tmp_path / "invalid.zeus.json"
    malformed_project.write_text("{}", encoding="utf-8")

    assert not window.open_project(malformed_project)
    assert "MISSING_PROJECT_FIELD" in window.project_banner.text()
    assert window.import_result is original_result

    window.close()
    qt_application.processEvents()


def test_main_window_rejects_project_configuration_outside_control_limits(
    qt_application: QApplication,
    tmp_path: Path,
) -> None:
    source_window = MainWindow()
    assert source_window.load_portfolio(PORTFOLIO_PATH)
    source_window.set_market_data_path(MARKET_DATA_PATH)
    source_window.risk_page.confidence_spin.setValue(50.0)
    source_window.risk_page.window_spin.setValue(2)
    destination = tmp_path / "unsupported-controls.zeus.json"
    assert source_window.save_project(destination)
    payload = json.loads(destination.read_text(encoding="utf-8"))
    payload["risk"]["horizon_days"] = 61
    destination.write_text(json.dumps(payload), encoding="utf-8")

    restored_window = MainWindow()

    assert not restored_window.open_project(destination)
    assert "PROJECT_CONFIGURATION_NOT_REPRESENTABLE" in restored_window.project_banner.text()
    assert restored_window.import_result is None

    source_window.close()
    restored_window.close()
    qt_application.processEvents()


def test_main_window_rejects_save_before_required_inputs(
    qt_application: QApplication,
    tmp_path: Path,
) -> None:
    window = MainWindow()

    assert not window.save_project(tmp_path / "incomplete.zeus.json")
    assert "PROJECT_NOT_READY" in window.project_banner.text()
    assert not (tmp_path / "incomplete.zeus.json").exists()

    window.close()
    qt_application.processEvents()
