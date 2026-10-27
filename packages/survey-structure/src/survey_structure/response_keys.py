"""Response columns produced by a SurveyStructure field."""

from __future__ import annotations

from typing import Any


def field_response_keys(field: dict[str, Any], prefix: str = "") -> list[str]:
    key = f"{prefix}_{field['code']}" if prefix else field["code"]
    field_type = field["type"]
    if field_type == "display":
        return []
    if field_type == "custom":
        return [
            item for child in field["childrenFields"] for item in field_response_keys(child, key)
        ]
    if field_type == "matrix":
        matrix = field["matrix"]
        if matrix["mode"] == "single":
            return [f"{key}_{row['code']}" for row in matrix["rows"]]
        return [
            f"{key}_{row['code']}_{column['code']}"
            for row in matrix["rows"]
            for column in matrix["columns"]
        ]
    if field_type == "multiple-input":
        return [f"{key}_{item['code']}" for item in field["subquestions"]]
    if field_type == "ranking":
        return [f"{key}_{index + 1}" for index in range(len(field["options"]))]
    if field_type == "multiple-choice":
        keys = [f"{key}_{option['code']}" for option in field["options"]]
    elif field_type == "multiple-choice-with-comments":
        keys = [
            item
            for option in field["options"]
            for item in (
                f"{key}_{option['code']}",
                option.get("commentResponseKey") or f"{key}_{option['code']}_comment",
            )
        ]
    elif field_type == "list-with-comment":
        keys = [key, field.get("commentResponseKey") or f"{key}_comment"]
    else:
        keys = [key]
    other = field.get("other")
    if other:
        keys.append(other["textResponseKey"])
        if other.get("commentResponseKey"):
            keys.append(other["commentResponseKey"])
    return keys
