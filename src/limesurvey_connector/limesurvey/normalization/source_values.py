"""Read optional values from LimeSurvey rows without exposing them as contract fields."""

from typing import Any

from .text_sanitizer import plain_text_from_html


def _clean_html(value: Any) -> str:
    return plain_text_from_html(value)


def _issue(
    level: str,
    code: str,
    message: str,
    field_id: str = "",
    question_code: str = "",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _compact(
        {
            "level": level,
            "code": code,
            "message": message,
            "fieldId": field_id or None,
            "questionCode": question_code or None,
            "details": details or None,
        }
    )


def _record(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else ([] if value is None else [value])


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _number(value: Any, fallback: float) -> float:
    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except (TypeError, ValueError):
        return fallback


def _optional_number(value: Any) -> float | None:
    if value is None or _text(value).strip() == "":
        return None
    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except (TypeError, ValueError):
        return None


def _yes(value: Any) -> bool:
    return _text(value).strip().upper() in {"Y", "1", "TRUE", "YES", "ON"}


def _compact(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None and item != {}}
