"""Normalize field visibility and report unsupported syntax without executing it."""

import logging
import os
import re
from typing import Any

from .condition_parser import parse_limesurvey_condition
from .condition_references import UnsupportedConditionError
from .source_values import _issue, _text

logger = logging.getLogger(__name__)


def field_visibility_expression(question: dict[str, Any]) -> str:
    """Select the field rule once for both conversion and source counting."""
    return next(
        (
            value
            for key in ("relevance", "condition", "full_condition")
            if (value := _text(question.get(key)).strip()) and value != "1"
        ),
        "",
    )


def report_child_relevance(
    children: list[dict[str, Any]], issues: list[dict[str, Any]], field_id: str, question_code: str
) -> None:
    """Retain unsupported per-item relevance as a diagnostic, not parent visibility."""
    spanish = (
        os.environ.get("APP_LOCALE", "es").strip().lower().replace("_", "-").split("-")[0] == "es"
    )
    for child in children:
        expression = _text(child.get("relevance"))
        if expression.strip().lower() in {"", "1", "true"}:
            continue
        identity = f"{_text(child.get('title'))} (qid={_text(child.get('qid'))})"
        message = (
            f"La relevancia de la subpregunta {identity} no se ejecuta; se conserva en este diagnóstico."
            if spanish
            else f"Relevance for subquestion {identity} is not executed; it is retained in this diagnostic."
        )
        log_unsupported_condition(expression, scope="field", owner=question_code)
        issues.append(
            _issue(
                "warning",
                "UNSUPPORTED_SOURCE_EXPRESSION",
                message,
                field_id=field_id,
                question_code=question_code,
                details={"sourceExpression": expression},
            )
        )


def normalize_field_visibility(
    question: dict[str, Any],
    condition_references: dict[str, tuple[str, str | None]],
    issues: list[dict[str, Any]],
    field_id: str,
    question_code: str,
    *,
    row_code: str | None = None,
    child_question_id: str | None = None,
) -> dict[str, Any]:
    # Group relevance is represented once on SurveyStructure.groups. Formly
    # combines it with this field-level condition when producing the runtime
    # projection, so it must not be copied into every field here.
    expression = field_visibility_expression(question)
    if not expression:
        return {}
    try:
        condition = parse_limesurvey_condition(
            expression,
            condition_references,
            # Row this/self need an explicit response-cell context. A synthetic
            # parent_row code could instead name an unrelated real question.
            current_field_code=None if row_code else question_code,
        )
        return {
            "condition": condition if condition is not None else {"type": "constant", "value": True}
        }
    except UnsupportedConditionError as error:
        log_unsupported_condition(expression, scope="field", owner=question_code)
        issues.append(
            _issue(
                "warning",
                error.issue_code,
                str(error),
                field_id=field_id,
                question_code=question_code,
                details={
                    "sourceExpression": expression,
                    **(
                        {"rowCode": row_code, "childQuestionId": child_question_id or ""}
                        if row_code
                        else {}
                    ),
                },
            )
        )
        return {}


def log_unsupported_condition(expression: str, scope: str, owner: str) -> None:
    """Record the unsupported syntax family without logging survey answer data."""
    function_match = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", expression)
    suffixes = sorted(set(re.findall(r"\.([A-Za-z_][A-Za-z0-9_]*)", expression)))
    logger.warning(
        "unsupported_expression_script scope=%s owner=%s function=%s suffixes=%s",
        scope,
        owner,
        function_match.group(1).lower() if function_match else "none",
        ",".join(suffix.lower() for suffix in suffixes) or "none",
    )
