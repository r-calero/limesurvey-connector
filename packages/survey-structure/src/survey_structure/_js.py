"""JavaScript value semantics needed to reproduce the reference validator exactly."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Mapping
from typing import Any

# ECMAScript WhiteSpace and LineTerminator code points (the \s class).
JS_WHITESPACE = "".join(
    chr(code)
    for code in (
        0x09,
        0x0A,
        0x0B,
        0x0C,
        0x0D,
        0x20,
        0xA0,
        0x1680,
        *range(0x2000, 0x200B),
        0x2028,
        0x2029,
        0x202F,
        0x205F,
        0x3000,
        0xFEFF,
    )
)
_ARRAY_INDEX = re.compile(r"^(?:0|[1-9][0-9]*)$")
_MAX_ARRAY_INDEX = 2**32 - 2


class _Undefined:
    __slots__ = ()

    def __repr__(self) -> str:
        return "undefined"

    def __bool__(self) -> bool:
        return False


UNDEFINED: Any = _Undefined()


def is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def typeof(value: object) -> str:
    if value is UNDEFINED:
        return "undefined"
    if isinstance(value, bool):
        return "boolean"
    if is_number(value):
        return "number"
    if isinstance(value, str):
        return "string"
    return "object"


def strict_equal(left: object, right: object) -> bool:
    """``left === right`` for JSON values."""
    if typeof(left) != typeof(right):
        return False
    if is_number(left):
        return bool(left == right)
    if isinstance(left, str | bool) or left is None or left is UNDEFINED:
        return left == right
    return left is right


def is_integer(value: float) -> bool:
    return math.isfinite(value) and float(value).is_integer()


def keys(value: Mapping[str, Any]) -> list[str]:
    """Own enumerable keys in ECMAScript order: array indices first, ascending."""
    indices = [key for key in value if _ARRAY_INDEX.match(key) and int(key) <= _MAX_ARRAY_INDEX]
    indices.sort(key=int)
    index_set = set(indices)
    return indices + [key for key in value if key not in index_set]


def length(value: str) -> int:
    """String length in UTF-16 code units."""
    return len(value.encode("utf-16-le")) // 2


def number_to_string(value: float) -> str:
    """``Number.prototype.toString()`` (ECMAScript Number::toString, radix 10)."""
    if isinstance(value, int):
        return str(value) if abs(value) < 10**21 else number_to_string(float(value))
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    if value == 0:
        return "0"
    if value < 0:
        return "-" + number_to_string(-value)
    digits, exponent = _shortest_digits(value)
    k = len(digits)
    n = exponent + k
    if k <= n <= 21:
        return digits + "0" * (n - k)
    if 0 < n <= 21:
        return f"{digits[:n]}.{digits[n:]}"
    if -6 < n <= 0:
        return f"0.{'0' * -n}{digits}"
    sign = "+" if n - 1 >= 0 else "-"
    mantissa = digits if k == 1 else f"{digits[0]}.{digits[1:]}"
    return f"{mantissa}e{sign}{abs(n - 1)}"


def _shortest_digits(value: float) -> tuple[str, int]:
    """Shortest round-trip decimal digits and exponent: ``value == int(digits) * 10**exponent``."""
    mantissa, _, power = repr(value).partition("e")
    whole, _, fraction = mantissa.partition(".")
    digits = (whole + fraction).lstrip("0")
    exponent = (int(power) if power else 0) - len(fraction)
    stripped = digits.rstrip("0")
    exponent += len(digits) - len(stripped)
    return stripped or "0", exponent


def trim(value: str) -> str:
    """``String.prototype.trim``."""
    return value.strip(JS_WHITESPACE)


def to_string(value: object) -> str:
    """``String(value)`` for JSON values."""
    if value is UNDEFINED:
        return "undefined"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if is_number(value):
        return number_to_string(value)  # type: ignore[arg-type]
    if isinstance(value, list):
        return ",".join("" if item is None else to_string(item) for item in value)
    if isinstance(value, dict):
        return "[object Object]"
    return str(value)


def stringify(value: object) -> str:
    """``JSON.stringify`` for JSON values."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if is_number(value):
        return number_to_string(value) if math.isfinite(value) else "null"  # type: ignore[arg-type]
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return (
            "[" + ",".join("null" if item is UNDEFINED else stringify(item) for item in value) + "]"
        )
    if isinstance(value, dict):
        items = [
            f"{json.dumps(key, ensure_ascii=False)}:{stringify(value[key])}"
            for key in keys(value)
            if value[key] is not UNDEFINED
        ]
        return "{" + ",".join(items) + "}"
    return "null"


def join_values(values: Iterable[object], separator: str = " | ") -> str:
    return separator.join(
        f"'{value}'" if isinstance(value, str) else to_string(value) for value in values
    )
