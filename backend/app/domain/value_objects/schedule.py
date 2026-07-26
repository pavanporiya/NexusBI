"""Schedule value object for cron scheduling validation and normalization.

Enforces domain invariants for analytical report schedules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from app.domain.exceptions import DomainValidationError

MONTH_MAP: dict[str, int] = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}

DAY_MAP: dict[str, int] = {
    "SUN": 0,
    "MON": 1,
    "TUE": 2,
    "WED": 3,
    "THU": 4,
    "FRI": 5,
    "SAT": 6,
}


@dataclass(frozen=True, slots=True)
class Schedule:
    """Immutable value object representing a normalized, validated cron schedule.

    Attributes
    ----------
    expression : str
        Normalized 5-part cron expression (e.g., '0 0 * * *').
    """

    expression: str

    FIELD_BOUNDS: ClassVar[list[tuple[int, int]]] = [
        (0, 59),  # minute
        (0, 23),  # hour
        (1, 31),  # day of month
        (1, 12),  # month
        (0, 7),  # day of week (0 or 7 = Sunday)
    ]

    def __post_init__(self) -> None:
        """Validate and normalize the cron expression upon instantiation."""
        if not isinstance(self.expression, str):
            raise DomainValidationError("Schedule expression must be a string")

        raw = self.expression.strip()
        if not raw:
            raise DomainValidationError("Schedule expression must not be empty")

        tokens = raw.split()
        if len(tokens) != 5:
            raise DomainValidationError(
                f"Invalid cron expression '{raw}': "
                "must contain exactly 5 space-separated fields"
            )

        normalized_tokens: list[str] = []
        for idx, (token, bounds) in enumerate(
            zip(tokens, self.FIELD_BOUNDS, strict=True)
        ):
            norm_field = self._validate_field(token, bounds, idx)
            normalized_tokens.append(norm_field)

        normalized_expression = " ".join(normalized_tokens)
        object.__setattr__(self, "expression", normalized_expression)

    @classmethod
    def _validate_field(
        cls, field_str: str, bounds: tuple[int, int], field_idx: int
    ) -> str:
        """Validate a single cron field and return normalized string."""
        items = field_str.split(",")
        norm_items: list[str] = []

        for item in items:
            if not item:
                raise DomainValidationError(
                    f"Invalid empty value in cron field '{field_str}'"
                )

            if "/" in item:
                parts = item.split("/")
                if len(parts) != 2:
                    raise DomainValidationError(
                        f"Invalid step syntax in cron field '{item}'"
                    )
                base, step_str = parts[0], parts[1]
                if not step_str.isdigit() or int(step_str) <= 0:
                    raise DomainValidationError(
                        f"Invalid step value '{step_str}' in cron field '{item}'. "
                        "Must be a positive integer."
                    )

                norm_base = cls._validate_sub_expr(base, bounds, field_idx)
                norm_items.append(f"{norm_base}/{step_str}")
            else:
                norm_items.append(cls._validate_sub_expr(item, bounds, field_idx))

        return ",".join(norm_items)

    @classmethod
    def _validate_sub_expr(
        cls, sub: str, bounds: tuple[int, int], field_idx: int
    ) -> str:
        """Validate a wildcard, range, or single numeric/named value."""
        min_val, max_val = bounds

        if sub == "*":
            return "*"

        if "-" in sub:
            parts = sub.split("-")
            if len(parts) != 2:
                raise DomainValidationError(f"Invalid range syntax in '{sub}'")
            start_val = cls._parse_value(parts[0], field_idx)
            end_val = cls._parse_value(parts[1], field_idx)

            if not (min_val <= start_val <= max_val):
                raise DomainValidationError(
                    f"Range start value '{parts[0]}' out of bounds "
                    f"({min_val}-{max_val})"
                )
            if not (min_val <= end_val <= max_val):
                raise DomainValidationError(
                    f"Range end value '{parts[1]}' out of bounds ({min_val}-{max_val})"
                )
            if start_val > end_val:
                raise DomainValidationError(
                    f"Range start '{parts[0]}' cannot be greater than end '{parts[1]}'"
                )

            return f"{parts[0]}-{parts[1]}"

        val = cls._parse_value(sub, field_idx)
        if not (min_val <= val <= max_val):
            raise DomainValidationError(
                f"Value '{sub}' in cron field out of bounds ({min_val}-{max_val})"
            )
        return sub

    @classmethod
    def _parse_value(cls, val_str: str, field_idx: int) -> int:
        """Parse numeric value or month/day name."""
        upper = val_str.upper()
        if field_idx == 3 and upper in MONTH_MAP:
            return MONTH_MAP[upper]
        if field_idx == 4 and upper in DAY_MAP:
            return DAY_MAP[upper]

        if not val_str.isdigit():
            raise DomainValidationError(
                f"Invalid numeric token '{val_str}' in cron expression"
            )
        return int(val_str)

    @classmethod
    def create(cls, value: Schedule | str | None) -> Schedule | None:
        """Factory method to construct a Schedule or return None if empty/None."""
        if value is None:
            return None
        if isinstance(value, Schedule):
            return value
        val_str = str(value).strip()
        if not val_str:
            return None
        return cls(val_str)

    def __str__(self) -> str:
        return self.expression

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Schedule):
            return self.expression == other.expression
        if isinstance(other, str):
            return self.expression == other
        return False
