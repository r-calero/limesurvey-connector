"""LimeSurvey response exports: CSV reading, system columns and translation.

Reproduces ``csv-dataset.ts`` and the translate route of limesurvey-dictionary-api,
with the intentional ``system-columns`` change (ADR 6): no column is dropped by
default and LimeSurvey system columns are translated as typed fields.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Sequence
from functools import cache
from importlib.resources import files
from typing import Any, Literal, TypedDict, cast

from limesurvey_connector.limesurvey import _papaparse
from limesurvey_connector.limesurvey.naming import underscore_column, underscore_record
from survey_data_dictionary import (
    ABSENT,
    DictionaryIssue,
    SurveyDictionary,
    TranslatedDataset,
    map_tabular_dataset,
    normalize_header,
    translate_dataset,
)

type ExportFormat = Literal["auto", "question-code", "full-heading", "sgqa", "vv"]

DEFAULT_MISSING_VALUES = ("N/A",)
# vv exports write this placeholder for questions hidden by relevance.
NOT_SHOWN_VALUES = ("{question_not_shown}",)
_BOM = chr(0xFEFF)
_SGQA = re.compile(r"^\d+X\d+X\d+", re.IGNORECASE | re.ASCII)


class SystemColumn(TypedDict, total=False):
    code: str
    dataType: str
    labels: dict[str, str]
    headers: list[str]
    verifiedHeaders: list[str]
    codeVerified: bool
    role: str
    pattern: str
    requiresQuestion: bool
    timing: bool


class CsvDatasetResult(TypedDict):
    responses: list[dict[str, Any]]
    issues: list[dict[str, Any]]
    columns: list[str | None]
    unmappedValues: list[list[dict[str, Any]]]
    responseIds: list[Any]
    headers: list[str]


class CsvTranslation(TypedDict):
    canonical: CsvDatasetResult
    translated: TranslatedDataset


class CsvParseError(ValueError):
    status_code = 400


@cache
def system_columns() -> tuple[SystemColumn, ...]:
    """LimeSurvey response-table columns that are not survey questions."""
    catalog = json.loads(
        files(__package__).joinpath("system_columns.json").read_text(encoding="utf-8")
    )
    return tuple(catalog["columns"])


def system_columns_in(
    keys: Iterable[str], question_codes: Iterable[str] = ()
) -> list[SystemColumn]:
    """System columns whose code or visible header appears among ``keys``.

    Pattern columns (timings) yield one entry per matching key; a per-question timing
    column is recognized only for a code in ``question_codes``.
    """
    keys = list(keys)
    present = {normalize_header(key) for key in keys}
    questions = set(question_codes)
    found: list[SystemColumn] = []
    for column in system_columns():
        pattern = column.get("pattern")
        if pattern is None:
            if column["code"] in present or any(
                normalize_header(header) in present for header in column["headers"]
            ):
                found.append(column)
            continue
        for key in keys:
            match = re.match(pattern, key)
            if match and (not column.get("requiresQuestion") or match["id"] in questions):
                found.append(_expand(column, key, match["id"]))
    return found


def _expand(column: SystemColumn, code: str, identifier: str) -> SystemColumn:
    expanded = cast(SystemColumn, {key: value for key, value in column.items() if key != "pattern"})
    expanded["code"] = code
    expanded["labels"] = {
        language: label.format(id=identifier) for language, label in column["labels"].items()
    }
    return expanded


def timing_columns(dictionary: SurveyDictionary) -> list[SystemColumn]:
    """Timing columns LimeSurvey writes when the survey saves timings."""
    catalog = {column["code"]: column for column in system_columns()}
    groups = list(
        dict.fromkeys(field["groupId"] for field in dictionary["fields"] if field.get("groupId"))
    )
    questions = list(dict.fromkeys(field["questionCode"] for field in dictionary["fields"]))
    return [
        catalog["interviewtime"],
        *(_expand(catalog["groupTime"], f"groupTime{group}", group) for group in groups),
        *(_expand(catalog["questionTime"], f"{code}Time", code) for code in questions),
    ]


def with_system_fields(
    dictionary: SurveyDictionary,
    columns: Iterable[SystemColumn] | None = None,
    *,
    include_timing: bool = False,
) -> SurveyDictionary:
    """Dictionary with entries for system columns, placed before the question fields.

    By default the fixed columns (id, dates, language...) are added; ``include_timing`` adds
    the timing columns. Columns whose code is already a response key are left to the survey field.
    """
    taken = {field["responseKey"] for field in dictionary["fields"]}
    language = "es" if _is_spanish(dictionary.get("language")) else "en"
    if columns is None:
        columns = [
            column
            for column in system_columns()
            if "pattern" not in column and not column.get("timing")
        ]
        if include_timing:
            columns = [*columns, *timing_columns(dictionary)]
    entries = []
    for column in columns:
        if column["code"] in taken:
            continue
        entry: dict[str, Any] = {
            "questionCode": column["code"],
            "questionLabel": column["labels"][language],
            "responseKey": column["code"],
            "dataType": column["dataType"],
            "cardinality": "single",
        }
        if column["headers"]:
            entry["aliases"] = list(column["headers"])
        entries.append(entry)
    extended = dict(dictionary)
    extended["fields"] = [*entries, *dictionary["fields"]]
    return cast(SurveyDictionary, extended)


def default_response_id_headers(dictionary: SurveyDictionary) -> list[str]:
    """Headers read as the response id, except any that is also a response key."""
    taken = {field["responseKey"] for field in dictionary["fields"]}
    column = next(item for item in system_columns() if item.get("role") == "response-id")
    return [header for header in (*column["headers"], column["code"]) if header not in taken]


def csv_to_canonical_responses(
    csv: str,
    dictionary: SurveyDictionary,
    *,
    delimiter: str | None = None,
    ignored_headers: Iterable[str] = (),
    missing_values: Sequence[str] | None = None,
    format: ExportFormat = "auto",
    response_id_header: str | None = None,
    response_id_headers: Sequence[str] | None = None,
    default_ignored_headers: Iterable[str] = (),
) -> CsvDatasetResult:
    """Read a LimeSurvey CSV export into response records keyed by the dictionary."""
    parsed = _papaparse.parse(csv, delimiter)
    fatal = next((error for error in parsed.errors if error.code != "UndetectableDelimiter"), None)
    if fatal is not None:
        raise CsvParseError(f"CSV parsing failed: {fatal.message or 'unknown error'}")
    rows = parsed.data
    visible = rows.pop(0) if rows else []
    source = (rows.pop(0) if rows else []) if format == "vv" else visible
    headers = [
        underscore_column(header.removeprefix(_BOM) if index == 0 else header)
        for index, header in enumerate(source)
    ]
    # vv header lines end with a tab, which adds an empty last header.
    if format == "vv" and len(headers) > 1 and headers[-1] == "":
        width = len(headers) - 1
        if all(len(row) == width or (len(row) == width + 1 and row[-1] == "") for row in rows):
            headers.pop()
            rows = [row[:width] for row in rows]
    if response_id_header:
        identifiers: Sequence[str] = [response_id_header]
    elif response_id_headers is not None:
        identifiers = response_id_headers
    else:
        identifiers = default_response_id_headers(dictionary)
    mapping = map_tabular_dataset(
        dictionary,
        headers,
        rows,
        [*default_ignored_headers, *ignored_headers],
        list(DEFAULT_MISSING_VALUES if missing_values is None else missing_values),
        identifiers,
    )
    format_issues = _validate_declared_format(format, headers, dictionary, mapping["columns"])
    return {
        "responses": mapping["responses"],
        "issues": [*format_issues, *mapping["issues"]],
        "columns": mapping["columns"],
        "unmappedValues": mapping["unmappedValues"],
        "responseIds": mapping["responseIds"],
        "headers": headers,
    }


def translate_csv(
    dictionary: SurveyDictionary,
    csv: str,
    *,
    delimiter: str | None = None,
    ignored_headers: Iterable[str] = (),
    missing_values: Sequence[str] | None = None,
    format: ExportFormat = "auto",
    response_id_header: str | None = None,
) -> CsvTranslation:
    """Translate a LimeSurvey CSV export, keeping and typing its system columns."""
    ignored = list(ignored_headers)
    options: dict[str, Any] = {
        "delimiter": delimiter,
        "ignored_headers": ignored,
        "missing_values": missing_values,
        "format": format,
        "response_id_header": response_id_header,
        "response_id_headers": default_response_id_headers(dictionary),
    }
    headers = csv_to_canonical_responses(csv, dictionary, **options)["headers"]
    present = [header for header in headers if header not in ignored]
    target = with_system_fields(
        dictionary, _answer_columns(system_columns_in(present, _question_codes(dictionary)))
    )
    canonical = csv_to_canonical_responses(csv, target, **options)
    translated = translate_dataset(
        target,
        canonical["responses"],
        unmapped_values=canonical["unmappedValues"],
        response_ids=canonical["responseIds"],
    )
    _mark_not_shown(translated)
    translated["issues"][:0] = cast(list[DictionaryIssue], canonical["issues"])
    return {"canonical": canonical, "translated": translated}


def _mark_not_shown(translated: TranslatedDataset) -> None:
    """Treat vv's "question not shown" placeholder as missing, keeping it as the source value."""

    def placeholder(value: Any) -> bool:
        return isinstance(value, str) and value in NOT_SHOWN_VALUES

    def keep(issue: DictionaryIssue) -> bool:
        return not (
            issue["code"] == "UNKNOWN_RESPONSE_VALUE"
            and placeholder(issue.get("details", {}).get("sourceValue"))
        )

    for response in translated["responses"]:
        for cell in response["fields"]:
            if placeholder(cell["sourceValue"]):
                cell["displayValue"] = None
                cell["missing"] = True
        response["issues"] = [issue for issue in response["issues"] if keep(issue)]
    translated["issues"] = [issue for issue in translated["issues"] if keep(issue)]


def translate_records(
    dictionary: SurveyDictionary,
    responses: Sequence[dict[str, Any]],
    *,
    response_id_key: str | None = None,
    response_ids: Sequence[Any] | None = None,
    ignored_keys: Iterable[str] = (),
    unmapped_values: Sequence[Sequence[dict[str, Any]] | None] | None = None,
) -> TranslatedDataset:
    """Translate JSON response records, keeping and typing any system columns they contain."""
    responses = [underscore_record(response) for response in responses]
    ignored: list[str] = []
    ids: Sequence[Any] | None = response_ids
    if response_id_key:
        ids = [_scalar_or_absent(response.get(response_id_key, ABSENT)) for response in responses]
        ignored.append(response_id_key)
    ignored.extend(ignored_keys)
    keys = list(dict.fromkeys(key for response in responses for key in response))
    target = with_system_fields(
        dictionary,
        _answer_columns(
            system_columns_in(
                (key for key in keys if key not in ignored), _question_codes(dictionary)
            )
        ),
    )
    return translate_dataset(
        target, responses, response_ids=ids, ignored_keys=ignored, unmapped_values=unmapped_values
    )


def _question_codes(dictionary: SurveyDictionary) -> set[str]:
    return {field["questionCode"] for field in dictionary["fields"]}


def _scalar_or_absent(value: Any) -> Any:
    return value if value is None or isinstance(value, str | int | float | bool) else ABSENT


def _answer_columns(columns: Iterable[SystemColumn]) -> list[SystemColumn]:
    return [column for column in columns if column.get("role") != "response-id"]


def _is_spanish(language: str | None) -> bool:
    return bool(re.match(r"^es(?:[-_]|$)", language or "", re.IGNORECASE))


def _validate_declared_format(
    format: ExportFormat,
    headers: list[str],
    dictionary: SurveyDictionary,
    columns: list[str | None],
) -> list[dict[str, Any]]:
    if format == "auto":
        return []
    mapped = [header for index, header in enumerate(headers) if columns[index] is not None]
    response_keys = {normalize_header(field["responseKey"]) for field in dictionary["fields"]}
    full_headings = {
        normalize_header(alias)
        for field in dictionary["fields"]
        for alias in field.get("aliases", [])
        if not _is_sgqa(alias)
    }
    if format == "question-code":
        matches = [header for header in mapped if normalize_header(header) in response_keys]
    elif format == "full-heading":
        matches = [header for header in mapped if normalize_header(header) in full_headings]
    elif format == "sgqa":
        matches = [header for header in mapped if _is_sgqa(header)]
    else:
        matches = mapped
    if matches:
        return []
    return [
        {
            "level": "error",
            "code": "EXPORT_FORMAT_MISMATCH",
            "message": f"The CSV headers do not match the declared {format} LimeSurvey export format.",
            "details": {"format": format, "headers": headers[:20]},
        }
    ]


def _is_sgqa(value: str) -> bool:
    return bool(_SGQA.match(normalize_header(value)))
