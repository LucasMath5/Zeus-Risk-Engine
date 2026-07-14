"""Currency value object."""

from __future__ import annotations

import re
from dataclasses import dataclass

from zeus_risk.domain.validation import raise_validation_error

_CURRENCY_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True, order=True, slots=True)
class Currency:
    """Normalized three-letter currency code without implicit FX conversion."""

    code: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, str):
            raise_validation_error(
                "INVALID_CURRENCY_TYPE",
                "Currency code must be a string.",
                field="currency",
            )

        normalized = self.code.strip().upper()
        if not _CURRENCY_CODE_PATTERN.fullmatch(normalized):
            raise_validation_error(
                "INVALID_CURRENCY_CODE",
                "Currency code must contain exactly three ASCII letters.",
                field="currency",
                item=normalized,
            )

        object.__setattr__(self, "code", normalized)

    def __str__(self) -> str:
        return self.code
