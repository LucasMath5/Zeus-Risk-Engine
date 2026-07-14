"""Integration tests for XLSX import through the shared portfolio contract."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from zeus_risk.importers import CsvPortfolioImporter, XlsxPortfolioImporter


def test_csv_and_xlsx_produce_equivalent_positions(tmp_path: Path) -> None:
    csv_text = """ticker,quantity,price,asset_class,currency,sector
ZEUS_EQ1,100,25.40,equity,BRL,Energy
ZEUS_EQ2,50,70.00,equity,BRL,Materials
ZEUS_FUND1,-10,126.30,fund,BRL,Fund
"""
    path = tmp_path / "portfolio.xlsx"
    workbook = Workbook()
    worksheet = cast(Worksheet, workbook.active)
    worksheet.title = "Portfolio"
    worksheet.append(["ticker", "quantity", "price", "asset_class", "currency", "sector"])
    worksheet.append(["ZEUS_EQ1", 100, 25.40, "equity", "BRL", "Energy"])
    worksheet.append(["ZEUS_EQ2", 50, 70.00, "equity", "BRL", "Materials"])
    worksheet.append(["ZEUS_FUND1", -10, 126.30, "fund", "BRL", "Fund"])
    workbook.save(path)
    workbook.close()

    csv_result = CsvPortfolioImporter().import_text(csv_text)
    xlsx_result = XlsxPortfolioImporter().import_file(path)

    assert xlsx_result.positions == csv_result.positions
    assert xlsx_result.summary == csv_result.summary
    assert xlsx_result.portfolio is not None
    assert csv_result.portfolio is not None
    assert xlsx_result.portfolio.market_value == csv_result.portfolio.market_value


def test_reads_worksheet_protection_without_treating_it_as_encryption(tmp_path: Path) -> None:
    path = tmp_path / "protected.xlsx"
    workbook = Workbook()
    worksheet = cast(Worksheet, workbook.active)
    worksheet.append(["ticker", "quantity", "price", "asset_class", "currency", "sector"])
    worksheet.append(["ZEUS", 1, 10, "equity", "BRL", "Energy"])
    worksheet.protection.sheet = True
    worksheet.protection.password = "synthetic"
    workbook.save(path)
    workbook.close()

    result = XlsxPortfolioImporter().import_file(path)

    assert result.summary.accepted_rows == 1
