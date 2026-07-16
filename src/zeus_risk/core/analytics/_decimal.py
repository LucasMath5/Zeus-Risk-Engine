"""Shared deterministic Decimal context for quantitative calculations."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from decimal import ROUND_HALF_EVEN, Context, localcontext

ANALYTICS_PRECISION = 34


@contextmanager
def analytics_context() -> Iterator[Context]:
    """Use decimal128-equivalent precision without mutating global context."""

    with localcontext() as context:
        context.prec = ANALYTICS_PRECISION
        context.rounding = ROUND_HALF_EVEN
        yield context
