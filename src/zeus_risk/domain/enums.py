"""Enumerations shared by the portfolio domain."""

from enum import StrEnum


class AssetClass(StrEnum):
    """Initial asset-class taxonomy used by portfolio instruments."""

    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    FX = "fx"
    CASH = "cash"
    COMMODITY = "commodity"
    FUND = "fund"
    DERIVATIVE = "derivative"
    OTHER = "other"


class WeightBasis(StrEnum):
    """Denominator convention used to normalize position weights."""

    NET = "net"
    GROSS = "gross"
