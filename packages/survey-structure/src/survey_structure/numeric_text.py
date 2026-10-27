"""Numeric answers kept as text (``numeric-text.ts`` and ``number-character-length.ts``)."""

from __future__ import annotations

import math
import re

from survey_structure._js import number_to_string

_NUMERIC_TEXT = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", re.ASCII)
_EDGE_SPACE = " \t\n\r\f\v"


def is_numeric_text(value: str) -> bool:
    """A numeric answer kept as text, so its original spelling (for example 007) survives."""
    trimmed = value.strip(_EDGE_SPACE)
    return bool(_NUMERIC_TEXT.fullmatch(trimmed)) and math.isfinite(float(trimmed))


def number_character_length(value: float) -> int:
    """Length of the decimal answer, including its sign and point, without exponent shorthand."""
    text = number_to_string(value)
    if "e" not in text:
        return len(text)
    coefficient, exponent = text.split("e")
    sign = 1 if coefficient.startswith("-") else 0
    whole, _, fraction = coefficient[sign:].partition(".")
    digits = len(whole) + len(fraction)
    point = len(whole) + int(exponent)
    if point <= 0:
        return sign + 2 - point + digits
    return sign + (point if point >= digits else digits + 1)
