"""Tests for import result helper properties."""

from __future__ import annotations

from zeus_risk.importers import CsvPortfolioImporter, ImportStatus, ImportSummary


def test_summary_counts_status_and_accepted_rows_independently() -> None:
    text = """ticker,quantity,price,asset_class,currency,sector
VALID,1,10,equity,BRL,Energy
WARNING,1,10,equity,BRL,
ERROR,0,10,equity,BRL,Energy
"""

    result = CsvPortfolioImporter().import_text(text)

    assert result.summary == ImportSummary(
        total_rows=3,
        accepted_rows=2,
        valid_rows=1,
        warning_rows=1,
        error_rows=1,
    )
    assert tuple(row.status for row in result.rows) == (
        ImportStatus.VALID,
        ImportStatus.WARNING,
        ImportStatus.ERROR,
    )
    assert result.has_errors
    assert result.is_partial
