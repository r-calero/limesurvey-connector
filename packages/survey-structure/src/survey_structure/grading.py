"""Automatic grading of normalized responses (``grading.ts``)."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, NotRequired, TypedDict

from survey_structure import _js
from survey_structure._js import UNDEFINED

_CHECKBOX_TYPES = ("multiple-choice", "multiple-choice-with-comments")


class SurveyAnswerGrade(TypedDict):
    points: float
    earned: float
    correct: bool
    feedback: NotRequired[str]


class SurveyScoreItem(SurveyAnswerGrade):
    fieldCode: str
    rowCode: NotRequired[str]


class SurveyScore(TypedDict):
    earned: float
    maximum: float
    items: list[SurveyScoreItem]


def object_is(left: object, right: object) -> bool:
    """``Object.is`` for JSON values."""
    if _js.is_number(left) and _js.is_number(right):
        a, b = float(left), float(right)  # type: ignore[arg-type]
        if math.isnan(a) or math.isnan(b):
            return math.isnan(a) and math.isnan(b)
        if a == 0 and b == 0:
            return math.copysign(1, a) == math.copysign(1, b)
        return a == b
    return _js.strict_equal(left, right)


def _is_object(value: object) -> bool:
    return isinstance(value, dict | list)


def _member(container: object, key: str) -> Any:
    if isinstance(container, dict):
        return container.get(key, UNDEFINED)
    if (
        isinstance(container, list)
        and key.isdigit()
        and str(int(key)) == key
        and int(key) < len(container)
    ):
        return container[int(key)]
    return UNDEFINED


def grade_survey_answer(
    grading: Mapping[str, Any], value: Any, multiple: bool = False, selected_value: Any = True
) -> SurveyAnswerGrade:
    if multiple:
        if isinstance(value, list):
            actual = list(value)
        elif isinstance(value, dict):
            actual = [code for code in _js.keys(value) if object_is(value[code], selected_value)]
        else:
            actual = []
    expected = grading["correctAnswers"]
    if multiple:
        correct = len(actual) == len(expected) and all(
            any(object_is(answer, item) for answer in actual) for item in expected
        )
    else:
        correct = (
            value is not None
            and value is not UNDEFINED
            and value != ""
            and any(object_is(value, item) for item in expected)
        )
    result: SurveyAnswerGrade = {
        "points": grading["points"],
        "earned": grading["points"] if correct else 0,
        "correct": correct,
    }
    feedback = grading.get("whenRight" if correct else "whenWrong")
    if feedback is None:
        feedback = grading.get("generalFeedback")
    if feedback is not None:
        result["feedback"] = feedback
    return result


def calculate_survey_score(
    survey: Mapping[str, Any], answers: Mapping[str, Any], field_codes: Sequence[str] | None = None
) -> SurveyScore:
    """Pure scoring for normalized responses. No partial credit, no automatic subjective marking."""
    items: list[SurveyScoreItem] = []

    def grade(
        field: Mapping[str, Any],
        grading: Mapping[str, Any],
        value: Any,
        multiple: bool,
        row_code: str | None = None,
    ) -> None:
        selected = field.get("responseEncoding", {}).get("selectedValue", True)
        result = grade_survey_answer(grading, value, multiple, selected)
        item: SurveyScoreItem = {"fieldCode": field["code"], **result}  # type: ignore[typeddict-item]
        if row_code:
            item = {"fieldCode": field["code"], "rowCode": row_code, **result}
        items.append(item)

    def visit(fields: Sequence[Mapping[str, Any]], model: object) -> None:
        for field in fields:
            if field_codes is not None and field["code"] not in field_codes:
                continue
            code = field["code"]
            value = _member(model, code)
            if value is UNDEFINED and "options" in field and field["type"] in _CHECKBOX_TYPES:
                value = {
                    option["code"]: _member(model, f"{code}_{option['code']}")
                    for option in field["options"]
                }
            if field.get("grading"):
                grade(field, field["grading"], value, field["type"] in _CHECKBOX_TYPES)
            if field["type"] == "matrix":
                for row in field["matrix"]["rows"]:
                    if row.get("grading"):
                        row_value = (
                            _member(value, row["code"])
                            if _is_object(value)
                            else _member(model, f"{code}_{row['code']}")
                        )
                        grade(
                            field,
                            row["grading"],
                            row_value,
                            field["matrix"]["mode"] == "multiple",
                            row["code"],
                        )
            if field["type"] == "custom":
                visit(field["childrenFields"], value if _is_object(value) else {})

    visit(survey["fields"], answers)
    earned: float = 0
    maximum: float = 0
    for item in items:
        earned += item["earned"]
    for item in items:
        maximum += item["points"]
    return {"earned": earned, "maximum": maximum, "items": items}
