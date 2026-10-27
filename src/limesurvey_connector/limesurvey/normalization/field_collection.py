"""Assemble ordered fields from LimeSurvey parent/child rows and report source counts."""

from collections import defaultdict
from typing import Any

from .field_normalizer import QUESTION_TYPES, normalize_field
from .field_values import _has_source_validation
from .source_values import _issue, _number, _record, _text
from .visibility_normalizer import field_visibility_expression


def normalize_fields(
    questions: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    survey_id: str,
    language: str,
    issues: list[dict[str, Any]],
    condition_references: dict[str, tuple[str, str | None]],
    remote_url: str = "",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Keep source diagnostics/counts even when a question cannot become a field."""
    children_by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    top_level: list[dict[str, Any]] = []
    for question in questions:
        parent_id = _text(question.get("parent_qid") or "0").strip()
        if parent_id in {"", "0"}:
            top_level.append(question)
        else:
            children_by_parent[parent_id].append(question)

    top_level_ids = {_text(question.get("qid")) for question in top_level}
    for parent_id, children in children_by_parent.items():
        if parent_id not in top_level_ids:
            for child in children:
                issues.append(
                    _issue(
                        "warning",
                        "MISSING_PARENT",
                        f"Subquestion {_text(child.get('qid'))} references missing parent {parent_id}.",
                        field_id=_text(child.get("qid")),
                    )
                )

    group_order = {
        _text(group.get("gid")): _number(group.get("group_order"), _number(group.get("gid"), 0))
        for group in groups
    }
    top_level.sort(
        key=lambda question: (
            group_order.get(_text(question.get("gid")), _number(question.get("gid"), 0)),
            _number(question.get("question_order"), 0),
        )
    )

    fields: list[dict[str, Any]] = []
    integrated_children = 0
    seen_codes = set()
    for question in top_level:
        code = _text(question.get("title")).strip()
        qid = _text(question.get("qid")).strip()
        if not code:
            issues.append(
                _issue(
                    "error",
                    "MISSING_QUESTION_CODE",
                    f"Question {qid or '(without id)'} has no code and was skipped.",
                    field_id=qid,
                )
            )
            continue
        if code in seen_codes:
            issues.append(
                _issue(
                    "error",
                    "DUPLICATE_QUESTION_CODE",
                    f"Question code {code} is duplicated and the later question was skipped.",
                    field_id=qid,
                    question_code=code,
                )
            )
            continue
        seen_codes.add(code)
        field = normalize_field(
            question,
            children_by_parent.get(qid, []),
            survey_id,
            language,
            issues,
            condition_references,
            remote_url,
        )
        if field:
            field["order"] = len(fields)
            fields.append(field)
            children = children_by_parent.get(qid, [])
            if field["type"] in {
                "multiple-choice",
                "multiple-choice-with-comments",
                "multiple-input",
            }:
                integrated_children += len(children)
            elif field["type"] == "matrix":
                # Matrix rows use scale 0; only text/number matrices also consume scale 1.
                has_rows = any(_text(child.get("scale_id") or "0") == "0" for child in children)
                integrated_children += sum(
                    not has_rows
                    or _text(child.get("scale_id") or "0") == "0"
                    or (
                        _text(question.get("type")) in {";", ":"}
                        and _text(child.get("scale_id")) == "1"
                    )
                    for child in children
                )
            elif field["type"] == "ranking" and not (
                _record(question.get("result")).get("answeroptions")
                or question.get("answeroptions")
            ):
                integrated_children += len(children)

    unconverted_validation_ids = {
        issue.get("fieldId")
        for issue in issues
        if issue.get("code") in {"INVALID_VALIDATION", "UNSUPPORTED_TIMER"}
    }
    unconverted_visibility_rules = sum(
        issue.get("code")
        in {"INVALID_EXPRESSION", "MISSING_CONDITION_REFERENCE", "UNSUPPORTED_SOURCE_EXPRESSION"}
        and issue.get("details", {}).get("rule") == "hidden"
        for issue in issues
    )
    return fields, {
        "topLevelQuestions": len(top_level),
        "childQuestions": len(questions) - len(top_level),
        "integratedChildren": integrated_children,
        "detectedTypes": sorted({_text(question.get("type")).strip() for question in top_level}),
        "conditionsDetected": sum(
            bool(field_visibility_expression(question)) for question in top_level
        )
        + sum(
            bool(field_visibility_expression({"relevance": child.get("relevance")}))
            for question in top_level
            if QUESTION_TYPES.get(_text(question.get("type"))) == "matrix"
            for child in children_by_parent[_text(question.get("qid"))]
            if _text(child.get("scale_id") or "0") == "0"
        )
        + sum(_text(group.get("grelevance")).strip() not in {"", "1"} for group in groups)
        + unconverted_visibility_rules,
        "validationQuestions": sum(
            _has_source_validation(question)
            or _text(question.get("qid")) in unconverted_validation_ids
            for question in top_level
        ),
    }
