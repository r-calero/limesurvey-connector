"""SurveyStructure contract validation, ported from the survey-structure npm package."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from survey_structure._field_rules import FIELD_WIDGET_COMPATIBILITY
from survey_structure._schema import Issue, Schema
from survey_structure.diagnostics import (
    localize_survey_validation_issue,
    resolve_survey_diagnostic_locale,
)
from survey_structure.grading import SurveyScoreItem, calculate_survey_score, grade_survey_answer
from survey_structure.month_day import is_month_day, month_day_count
from survey_structure.numeric_text import is_numeric_text, number_character_length
from survey_structure.patterns import test_pattern, to_python_pattern
from survey_structure.readiness import get_survey_execution_issues
from survey_structure.response_keys import field_response_keys
from survey_structure.schemas import (
    SURVEY_STRUCTURE_VERSION,
    survey_load_result_schema,
    survey_response_record_schema,
    survey_structure_schema,
)
from survey_structure.types import (
    SurveyCondition,
    SurveyGrading,
    SurveyLoadResult,
    SurveyResponseRecord,
    SurveyResponseScalar,
    SurveyResponseValue,
    SurveyStructure,
    SurveyStructureField,
    SurveyStructureIssue,
)
from survey_structure.validation_pattern import validation_pattern_source

try:
    __version__ = version("survey-structure")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

# The npm release and commit whose behavior this package reproduces.
UPSTREAM = {
    "package": "survey-structure",
    "version": "2.1.0",
    "commit": "0148e3f7779b86a6b43b68e682da648fe296bc96",
    "repository": "https://github.com/JJKid/survey-structure",
}


@dataclass(frozen=True, slots=True)
class ParseResult:
    """Outcome of a validation; ``data`` is set only when ``success`` is true."""

    success: bool
    data: Any = None
    issues: list[Issue] = field(default_factory=list)


class SurveyStructureValidationError(ValueError):
    def __init__(self, issues: list[Issue]) -> None:
        self.issues = issues
        first = issues[0] if issues else {"path": [], "message": "Invalid input"}
        location = ".".join(str(part) for part in first["path"]) or "<root>"
        super().__init__(
            f"{len(issues)} contract issue(s); first at {location}: {first['message']}"
        )


def _safe_parse(schema: Schema, value: Any) -> ParseResult:
    issues: list[Issue] = []
    outcome = schema.parse(value, [], issues)
    if outcome.status == "valid":
        return ParseResult(True, outcome.value, [])
    return ParseResult(False, None, issues)


def safe_parse_survey_structure(value: Any) -> ParseResult:
    """Validate untrusted input against SurveyStructure without raising."""
    return _safe_parse(survey_structure_schema, value)


def parse_survey_structure(value: Any) -> SurveyStructure:
    result = safe_parse_survey_structure(value)
    if not result.success:
        raise SurveyStructureValidationError(result.issues)
    return result.data  # type: ignore[no-any-return]


def safe_parse_survey_load_result(value: Any) -> ParseResult:
    """Validate an import or load envelope without raising."""
    return _safe_parse(survey_load_result_schema, value)


def parse_survey_load_result(value: Any) -> SurveyLoadResult:
    result = safe_parse_survey_load_result(value)
    if not result.success:
        raise SurveyStructureValidationError(result.issues)
    return result.data  # type: ignore[no-any-return]


def parse_survey_response_record(value: Any) -> SurveyResponseRecord:
    """Check the value received from storage, a form or HTTP before accepting it as answers."""
    result = _safe_parse(survey_response_record_schema, value)
    if not result.success:
        raise SurveyStructureValidationError(result.issues)
    return result.data  # type: ignore[no-any-return]


__all__ = [
    "FIELD_WIDGET_COMPATIBILITY",
    "SURVEY_STRUCTURE_VERSION",
    "UPSTREAM",
    "ParseResult",
    "SurveyCondition",
    "SurveyGrading",
    "SurveyLoadResult",
    "SurveyResponseRecord",
    "SurveyResponseScalar",
    "SurveyResponseValue",
    "SurveyScoreItem",
    "SurveyStructure",
    "SurveyStructureField",
    "SurveyStructureIssue",
    "SurveyStructureValidationError",
    "calculate_survey_score",
    "field_response_keys",
    "get_survey_execution_issues",
    "grade_survey_answer",
    "is_month_day",
    "is_numeric_text",
    "localize_survey_validation_issue",
    "month_day_count",
    "number_character_length",
    "parse_survey_load_result",
    "parse_survey_response_record",
    "parse_survey_structure",
    "resolve_survey_diagnostic_locale",
    "safe_parse_survey_load_result",
    "safe_parse_survey_structure",
    "survey_response_record_schema",
    "test_pattern",
    "to_python_pattern",
    "validation_pattern_source",
]
