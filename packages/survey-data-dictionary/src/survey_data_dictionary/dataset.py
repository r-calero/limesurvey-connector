"""Map positional tabular data to response records (port of ``dataset.ts``)."""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Iterable, Sequence
from typing import Any, TypedDict

from survey_data_dictionary.contracts import SurveyDictionary
from survey_structure._js import JS_WHITESPACE, UNDEFINED, is_number, strict_equal, trim
from survey_structure._js import keys as js_keys

_WHITESPACE_RUN = re.compile(f"[{re.escape(JS_WHITESPACE)}]+")


class TabularDatasetMapping(TypedDict):
    responses: list[dict[str, Any]]
    issues: list[dict[str, Any]]
    columns: list[str | None]
    unmappedValues: list[list[dict[str, Any]]]
    responseIds: list[Any]


def normalize_header(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).replace(chr(0xA0), " ")
    return trim(_WHITESPACE_RUN.sub(" ", normalized))


def map_tabular_dataset(
    dictionary: SurveyDictionary,
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
    ignored_headers: Iterable[str] = (),
    missing_values: Sequence[Any] = (),
    response_id_headers: Iterable[str] = (),
) -> TabularDatasetMapping:
    """Map rows by position without collapsing duplicate headers.

    ``responseIds`` holds ``ABSENT`` for rows without an identifier column or cell.
    """
    headers = list(headers)
    ignored = set(ignored_headers)
    identifiers = {normalize_header(header) for header in response_id_headers}
    candidates = _index_dictionary_keys(dictionary)
    canonical = {field["responseKey"] for field in dictionary["fields"]}

    def skip(header: str) -> bool:
        return header in ignored or normalize_header(header) in identifiers

    exact = {header for header in headers if header in canonical and not skip(header)}
    column_candidates = [
        []
        if skip(header)
        else [header]
        if header in canonical
        else candidates.get(normalize_header(header), [])
        for header in headers
    ]
    preferred: list[str | None] = []
    for index, entries in enumerate(column_candidates):
        if len(entries) != 1:
            preferred.append(None)
            continue
        target = entries[0]
        # Reserve canonical columns before considering aliases, regardless of order.
        preferred.append(None if target in exact and headers[index] != target else target)
    counts: dict[str, int] = {}
    for preferred_target in preferred:
        if preferred_target:
            counts[preferred_target] = counts.get(preferred_target, 0) + 1
    mapping = [target if target and counts[target] == 1 else None for target in preferred]

    issues: list[dict[str, Any]] = []
    for index, header in enumerate(headers):
        if skip(header) or mapping[index]:
            continue
        entries = column_candidates[index]
        details: dict[str, Any] = {"columnIndex": index}
        if entries:
            details["candidates"] = entries
        issues.append(
            {
                "level": "warning",
                "code": "AMBIGUOUS_RESPONSE_ALIAS" if entries else "UNKNOWN_RESPONSE_KEY",
                "message": (
                    f"Dataset header {header} has an ambiguous or conflicting mapping. "
                    "Its values were preserved without choosing by position."
                    if entries
                    else f"Dataset header {header} could not be mapped to a canonical response key."
                ),
                "responseKey": header,
                "details": details,
            }
        )
    for index, row in enumerate(rows):
        if len(row) != len(headers):
            issues.append(
                {
                    "level": "warning",
                    "code": "SOURCE_PARSE_ISSUE",
                    "responseIndex": index + 1,
                    "message": f"Dataset row {index + 1} contains {len(row)} cells for {len(headers)} headers. "
                    "Surplus cells are preserved as unmapped values.",
                    "details": {"expectedColumns": len(headers), "actualColumns": len(row)},
                }
            )

    responses = []
    for row in rows:
        response: dict[str, Any] = {}
        for index, key in enumerate(mapping):
            if not key:
                continue
            value = row[index] if index < len(row) else ""
            missing = any(strict_equal(value, item) for item in missing_values)
            response[key] = None if missing else _to_response_value(value)
        responses.append(response)

    unmapped = []
    for row in rows:
        values = []
        for column, value in enumerate(row):
            source_key = headers[column] if column < len(headers) else f"[column {column + 1}]"
            if column < len(mapping) and mapping[column]:
                continue
            if column < len(headers) and skip(source_key):
                continue
            values.append(
                {
                    "sourceKey": source_key,
                    "sourceValue": _to_response_value(value),
                    "columnIndex": column,
                }
            )
        unmapped.append(values)

    id_column = next(
        (index for index, header in enumerate(headers) if normalize_header(header) in identifiers),
        -1,
    )
    response_ids = []
    for row in rows:
        value = row[id_column] if 0 <= id_column < len(row) else UNDEFINED
        valid = (
            value is None
            or isinstance(value, str | bool)
            or (is_number(value) and math.isfinite(value))
        )
        response_ids.append(value if valid else UNDEFINED)

    return {
        "responses": responses,
        "issues": issues,
        "columns": mapping,
        "unmappedValues": unmapped,
        "responseIds": response_ids,
    }


def _to_response_value(value: Any) -> Any:
    if value is None or isinstance(value, str | bool):
        return value
    if is_number(value) and math.isfinite(value):
        return value
    if isinstance(value, list):
        return [_to_response_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_response_value(value[key]) for key in js_keys(value)}
    raise TypeError("Tabular response data must contain JSON-safe values.")


def _index_dictionary_keys(dictionary: SurveyDictionary) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for field in dictionary["fields"]:
        for key in (field["responseKey"], *field.get("aliases", [])):
            entries = result.setdefault(normalize_header(key), [])
            if field["responseKey"] not in entries:
                entries.append(field["responseKey"])
    return result
