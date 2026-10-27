"""Runtime validators for dictionaries and response datasets (port of ``schemas.ts``)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from survey_structure import SURVEY_STRUCTURE_VERSION, ParseResult
from survey_structure.engine import (
    Array,
    Boolean,
    Default,
    Enum,
    Issue,
    Lazy,
    LiteralValue,
    Null,
    Nullable,
    Number,
    Object,
    Record,
    Schema,
    String,
    Union,
    Unknown,
)

dictionary_issue_schema = Object(
    {
        "level": Enum("warning", "error"),
        "code": Enum(
            "MISSING_QUESTION_CODE",
            "DUPLICATE_QUESTION_CODE",
            "DUPLICATE_RESPONSE_KEY",
            "MISSING_OPTION_CODE",
            "MISSING_MATRIX_ROW_CODE",
            "MISSING_MATRIX_COLUMN_CODE",
            "UNKNOWN_RESPONSE_KEY",
            "UNKNOWN_RESPONSE_VALUE",
            "UNKNOWN_RESPONSE_ALIAS",
            "AMBIGUOUS_RESPONSE_ALIAS",
            "EXPORT_FORMAT_MISMATCH",
            "SOURCE_ADAPTATION_ISSUE",
            "SOURCE_PARSE_ISSUE",
        ),
        "message": String(),
        "questionCode": String().optional(),
        "responseKey": String().optional(),
        "responseIndex": Number().int().positive().optional(),
        "details": Record(Unknown()).optional(),
    }
)

dictionary_field_schema = Object(
    {
        "questionCode": String(),
        "questionLabel": String(),
        "responseKey": String().min(1),
        "dataType": Enum("string", "number", "date", "boolean", "code"),
        "cardinality": Enum("single", "multiple"),
        "values": Array(Object({"code": String(), "label": String()})).optional(),
        "aliases": Array(String()).optional(),
        "parentCode": String().optional(),
        "qid": String().optional(),
        "groupId": String().optional(),
    }
)


def _unique_response_keys(dictionary: dict[str, Any], report: Callable[[Issue], None]) -> None:
    seen: set[str] = set()
    for index, field in enumerate(dictionary["fields"]):
        key = field["responseKey"]
        if key in seen:
            report(
                {
                    "code": "custom",
                    "path": ["fields", index, "responseKey"],
                    "message": f'Duplicate response key "{key}" would overwrite another dictionary field.',
                }
            )
        seen.add(key)


survey_dictionary_schema = Object(
    {
        "surveyStructureVersion": LiteralValue(SURVEY_STRUCTURE_VERSION),
        "surveyId": String(),
        "surveyTitle": String().optional(),
        "language": String().optional(),
        "fields": Array(dictionary_field_schema),
        "issues": Default(Array(dictionary_issue_schema), list),
    }
).super_refine(_unique_response_keys)

survey_response_value_schema: Schema = Lazy(
    lambda: Union(
        String(),
        Number().finite(),
        Boolean(),
        Null(),
        Array(survey_response_value_schema),
        Record(survey_response_value_schema),
    )
)
survey_response_record_schema = Record(survey_response_value_schema)
survey_response_dataset_schema = Object(
    {
        "surveyId": String(),
        "language": Nullable(String()).optional(),
        "responses": Array(survey_response_record_schema),
        "responseIds": Array(String()).optional(),
    }
).refine(
    lambda value: (
        "responseIds" not in value or len(value["responseIds"]) == len(value["responses"])
    ),
    "Each response must have a corresponding source identifier.",
    path=["responseIds"],
)


def _safe_parse(schema: Schema, value: Any) -> ParseResult:
    issues: list[Issue] = []
    outcome = schema.parse(value, [], issues)
    if outcome.status == "valid":
        return ParseResult(True, outcome.value, [])
    return ParseResult(False, None, issues)


def safe_parse_survey_dictionary(value: Any) -> ParseResult:
    return _safe_parse(survey_dictionary_schema, value)


def safe_parse_survey_response_record(value: Any) -> ParseResult:
    return _safe_parse(survey_response_record_schema, value)


def safe_parse_survey_response_dataset(value: Any) -> ParseResult:
    return _safe_parse(survey_response_dataset_schema, value)
