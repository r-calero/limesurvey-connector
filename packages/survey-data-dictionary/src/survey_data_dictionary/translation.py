"""Interpret response records with a dictionary (port of ``translation.ts``)."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from survey_data_dictionary.contracts import (
    DictionaryField,
    SurveyDictionary,
    TranslatedDataset,
    TranslatedResponse,
)
from survey_structure._js import UNDEFINED, to_string
from survey_structure._js import keys as js_keys


def translate_response(
    dictionary: SurveyDictionary,
    response: dict[str, Any],
    *,
    response_index: int | None = None,
    response_id: Any = UNDEFINED,
    unmapped_values: Sequence[dict[str, Any]] | None = None,
    ignored_keys: Iterable[str] | None = None,
) -> TranslatedResponse:
    """Translate one record. ``response_id`` may be ``None`` (JSON null); omit it for no identifier."""
    flat = _flatten(response)
    issues: list[dict[str, Any]] = []
    by_key = {field["responseKey"]: field for field in dictionary["fields"]}
    by_alias = _index_aliases(dictionary["fields"])
    fields: list[dict[str, Any]] = []
    unmapped: list[dict[str, Any]] = list(unmapped_values or [])
    translated: set[str] = set()
    ignored = set(ignored_keys or [])

    key_counts: dict[str, int] = {}
    for key, _ in flat:
        if key not in ignored:
            key_counts[key] = key_counts.get(key, 0) + 1
    alias_targets: dict[str, int] = {}
    for key, _ in flat:
        if key in ignored or key in by_key:
            continue
        candidates = by_alias.get(key, [])
        if len(candidates) == 1:
            target = candidates[0]["responseKey"]
            alias_targets[target] = alias_targets.get(target, 0) + 1

    for source_key, source_value in flat:
        if source_key in ignored:
            continue

        def preserve(message: str, *, key: str = source_key, value: Any = source_value) -> None:
            issues.append(
                {
                    "level": "warning",
                    "code": "AMBIGUOUS_RESPONSE_ALIAS",
                    "responseKey": key,
                    "message": message,
                }
            )
            unmapped.append({"sourceKey": key, "sourceValue": value})

        if key_counts.get(source_key, 0) > 1:
            preserve(
                f'More than one input value becomes "{source_key}" after flattening. '
                "Each value was preserved without choosing one."
            )
            continue
        field = by_key.get(source_key)
        if field is None:
            candidates = by_alias.get(source_key, [])
            if len(candidates) == 1:
                field = candidates[0]
            elif len(candidates) > 1:
                issues.append(
                    {
                        "level": "warning",
                        "code": "AMBIGUOUS_RESPONSE_ALIAS",
                        "message": f"Response alias {source_key} matches multiple dictionary fields.",
                        "responseKey": source_key,
                        "details": {
                            "candidates": [candidate["responseKey"] for candidate in candidates]
                        },
                    }
                )
                unmapped.append({"sourceKey": source_key, "sourceValue": source_value})
                continue
        if field is None:
            issue: dict[str, Any] = {
                "level": "warning",
                "code": "UNKNOWN_RESPONSE_KEY",
                "message": f"Response key {source_key} does not exist in the dictionary.",
                "responseKey": source_key,
            }
            if response_index is not None:
                issue["responseIndex"] = response_index
            issues.append(issue)
            unmapped.append({"sourceKey": source_key, "sourceValue": source_value})
            continue
        target = field["responseKey"]
        if source_key != target and target in key_counts:
            preserve(
                f'The canonical input "{target}" takes priority. '
                "This alias value was preserved without overwriting it."
            )
            continue
        if target in translated:
            preserve(
                f'Another input already mapped to "{target}". '
                "This additional value was preserved without overwriting it."
            )
            continue
        if source_key != target and alias_targets.get(target, 0) > 1:
            preserve(
                f'Multiple aliases target "{target}" without an exact response key. '
                "Every value was preserved without choosing one."
            )
            continue
        translated.add(target)
        fields.append(_translate_field(field, source_value, issues))

    for field in dictionary["fields"]:
        if field["responseKey"] not in translated:
            fields.append(_translate_field(field, None, issues))

    index = 1 if response_index is None else response_index
    result: dict[str, Any] = {"responseIndex": index}
    if response_id is not UNDEFINED:
        result["responseId"] = response_id
    result["fields"] = fields
    result["unmappedValues"] = unmapped
    result["issues"] = [{**issue, "responseIndex": index} for issue in issues]
    return result  # type: ignore[return-value]


def translate_dataset(
    dictionary: SurveyDictionary,
    responses: Sequence[dict[str, Any]],
    *,
    response_ids: Sequence[Any] | None = None,
    unmapped_values: Sequence[Sequence[dict[str, Any]] | None] | None = None,
    ignored_keys: Iterable[str] | None = None,
) -> TranslatedDataset:
    """Translate several records; ``response_ids`` and ``unmapped_values`` align by position."""
    ignored = list(ignored_keys or [])
    translated = [
        translate_response(
            dictionary,
            response,
            response_index=index + 1,
            response_id=_at(response_ids, index),
            unmapped_values=_at(unmapped_values, index, None),
            ignored_keys=ignored,
        )
        for index, response in enumerate(responses)
    ]
    return {
        "responses": translated,
        "issues": [
            {**issue, "responseIndex": response["responseIndex"]}
            for response in translated
            for issue in response["issues"]
        ],
    }


def _at(values: Sequence[Any] | None, index: int, default: Any = UNDEFINED) -> Any:
    if values is None or index >= len(values):
        return default
    return values[index]


def _translate_field(
    field: DictionaryField, source_value: Any, issues: list[dict[str, Any]]
) -> dict[str, Any]:
    display_value = source_value
    values = field.get("values") or []
    if source_value is not None and to_string(source_value) != "" and values:
        text = to_string(source_value)
        match = next((value for value in values if value["code"] == text), None) or next(
            (value for value in values if value["label"] == text), None
        )
        if match is not None:
            display_value = match["label"]
        else:
            issues.append(
                {
                    "level": "warning",
                    "code": "UNKNOWN_RESPONSE_VALUE",
                    "message": f"Value {text} is not defined for {field['responseKey']}.",
                    "questionCode": field["questionCode"],
                    "responseKey": field["responseKey"],
                    "details": {"sourceValue": source_value},
                }
            )
    return {
        "responseKey": field["responseKey"],
        "questionCode": field["questionCode"],
        "questionLabel": field["questionLabel"],
        "dataType": field["dataType"],
        "sourceValue": source_value,
        "displayValue": display_value,
        "missing": source_value is None or source_value == "",
    }


def _index_aliases(fields: list[DictionaryField]) -> dict[str, list[DictionaryField]]:
    result: dict[str, list[DictionaryField]] = {}
    for field in fields:
        for alias in field.get("aliases", []):
            result.setdefault(alias, []).append(field)
    return result


def _flatten(
    value: Any, prefix: str | None = None, result: list[tuple[str, Any]] | None = None
) -> list[tuple[str, Any]]:
    result = [] if result is None else result
    if isinstance(value, dict) and (prefix is None or value):
        for key in js_keys(value):
            _flatten(value[key], key if prefix is None else f"{prefix}_{key}", result)
        return result
    if prefix is not None:
        result.append((prefix, value))
    return result
