"""Calendar days without a year (``month-day.ts``)."""

from __future__ import annotations

import re

from survey_structure._js import is_number

_DAYS = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_DAY = re.compile(r"\d{2}-\d{2}", re.ASCII)


def month_day_count(month: float) -> int:
    """Days in ``month``; February 29 remains a valid recurring date."""
    if is_number(month) and float(month).is_integer() and 1 <= month <= 12:
        return _DAYS[int(month) - 1]
    return 0


def is_month_day(value: object) -> bool:
    if not isinstance(value, str) or not _MONTH_DAY.fullmatch(value):
        return False
    month, day = (int(part) for part in value.split("-"))
    return 1 <= month <= 12 and 1 <= day <= month_day_count(month)
