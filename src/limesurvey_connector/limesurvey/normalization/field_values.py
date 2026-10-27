"""Read field options, typed validation limits and default/date values."""

import math
import re
from datetime import date
from typing import Any

from .source_values import (
    _clean_html,
    _compact,
    _issue,
    _number,
    _optional_number,
    _record,
    _text,
    _yes,
)


def _has_source_validation(question: dict[str, Any]) -> bool:
    """Count questions with required or recognized source validation attributes, not rules."""
    attributes = _record(
        _record(question.get("result")).get("attributes") or question.get("attributes")
    )
    validation = _native_validation(attributes) or {}
    if _optional_number(attributes.get("min_answers")) == 0:
        validation.pop("minimumAnswersExpression", None)
    if _optional_number(attributes.get("maximum_chars")) == 0:
        validation.pop("maximumCharactersExpression", None)
    if _optional_number(attributes.get("max_subquestions")) == 0:
        validation.pop("maximumRankingItemsExpression", None)
    # A zero answer-count minimum adds no restriction. Numeric questions instead
    # use minimum_answer as a numeric lower bound, where zero is meaningful.
    if question.get("type") != "N" and _optional_number(attributes.get("minimum_answer")) == 0:
        validation.pop("minimumAnswerExpression", None)
    pattern = _record(question.get("result")).get("preg", question.get("preg"))
    numeric_text = question.get("type") in {"S", "Q", ";"} and _yes(attributes.get("numbers_only"))
    return (
        _yes(question.get("mandatory"))
        or bool(validation)
        or bool(_text(pattern).strip())
        or _yes(attributes.get("num_value_int_only"))
        or numeric_text
    )


def _native_validation(attributes: dict[str, Any]) -> dict[str, str] | None:
    """Retain LimeSurvey-only validation text without treating it as portable behavior.

    Fixed numeric limits are also normalized into ``field.responseValidation`` when the
    semantic field type supports them. Original expressions remain here so an
    importer report, diagnostic tool or future exporter can explain their
    source without forcing neutral consumers to understand ExpressionScript.
    """
    values = _compact(
        {
            "minimumNumericValueExpression": _text(attributes.get("min_num_value")).strip() or None,
            "maximumNumericValueExpression": _text(attributes.get("max_num_value")).strip() or None,
            "minimumAnswerExpression": _text(attributes.get("minimum_answer")).strip() or None,
            "maximumAnswerExpression": _text(attributes.get("maximum_answer")).strip() or None,
            "minimumCellValueExpression": _text(attributes.get("multiflexible_min")).strip()
            or None,
            "maximumCellValueExpression": _text(attributes.get("multiflexible_max")).strip()
            or None,
            "cellStepExpression": _text(attributes.get("multiflexible_step")).strip() or None,
            "minimumAnswersExpression": _text(attributes.get("min_answers")).strip() or None,
            "maximumAnswersExpression": _text(attributes.get("max_answers")).strip() or None,
            "questionValidationExpression": _text(attributes.get("em_validation_q")).strip()
            or None,
            "subquestionValidationExpression": _text(attributes.get("em_validation_sq")).strip()
            or None,
            "minimumDateExpression": _text(attributes.get("date_min")).strip() or None,
            "maximumDateExpression": _text(attributes.get("date_max")).strip() or None,
            "maximumCharactersExpression": _text(attributes.get("maximum_chars")).strip() or None,
            "maximumRankingItemsExpression": _text(attributes.get("max_subquestions")).strip()
            or None,
            "minimumNumericAnswerValueExpression": _text(attributes.get("min_num_value_n")).strip()
            or None,
            "maximumNumericAnswerValueExpression": _text(attributes.get("max_num_value_n")).strip()
            or None,
        }
    )
    return values or None


def _validation(
    attributes: dict[str, Any],
    field_type: str,
    issues: list[dict[str, Any]],
    field_id: str,
    question_code: str,
    native_type: str = "",
) -> dict[str, Any]:
    """Translate only validation rules that apply to the canonical field type.

    LimeSurvey exports some redundant attributes for field types that already
    enforce the same rule. For example, an ``L`` question can contain
    ``min_answers=1`` and ``max_answers=1`` even though single selection and
    ``mandatory`` already express those constraints. Copying every source
    attribute would create an invalid or misleading SurveyStructure.
    """
    validation: dict[str, Any] = {}
    numeric_limits = {
        rule: _validation_number(attributes.get(rule), rule, issues, field_id, question_code)
        for rule in (
            "min_num_value",
            "minimum_answer",
            "max_num_value",
            "maximum_answer",
            "min_answers",
            "max_answers",
        )
    }
    if field_type in {"number", "range"}:
        for portable, rules in (
            ("min", ("min_num_value", "minimum_answer")),
            ("max", ("max_num_value", "maximum_answer")),
        ):
            for rule in rules:
                value = attributes.get(rule)
                if value is not None and _text(value).strip():
                    validation[portable] = numeric_limits[rule]
                    break
        validation["integer"] = (
            _yes(attributes.get("num_value_int_only"))
            if attributes.get("num_value_int_only") is not None
            else None
        )
        # Current LimeSurvey N bounds validate the individual answer. If legacy
        # bounds are also present, both constraints apply to the same scalar.
        for portable, rule, combine in (
            ("min", "min_num_value_n", max),
            ("max", "max_num_value_n", min),
        ):
            value = _validation_number(attributes.get(rule), rule, issues, field_id, question_code)
            if value is not None:
                previous = validation.get(portable)
                validation[portable] = value if previous is None else combine(previous, value)
    if field_type in {"multiple-choice", "multiple-choice-with-comments", "ranking"}:
        validation.update(
            {
                "minSelections": numeric_limits["min_answers"],
                "maxSelections": numeric_limits["max_answers"],
            }
        )
    if field_type == "ranking":
        capacity = _validation_number(
            attributes.get("max_subquestions"), "max_subquestions", issues, field_id, question_code
        )
        if capacity is not None and capacity > 0 and capacity == int(capacity):
            previous = validation.get("maxSelections")
            validation["maxSelections"] = (
                int(capacity) if previous is None else min(previous, int(capacity))
            )
    if field_type in {"short-text", "long-text", "number", "multiple-input"} or native_type == ";":
        maximum_chars = _optional_number(attributes.get("maximum_chars"))
        if maximum_chars is not None and maximum_chars > 0 and maximum_chars == int(maximum_chars):
            validation["maxLength"] = int(maximum_chars)
    if native_type in {"S", "Q", ";"} and _yes(attributes.get("numbers_only")):
        validation["numericText"] = True
    if field_type == "date":
        for native, neutral in (("date_min", "dateMin"), ("date_max", "dateMax")):
            raw = _text(attributes.get(native)).strip()
            try:
                if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", raw):
                    validation[neutral] = date.fromisoformat(raw).isoformat()
                elif re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", raw):
                    month, day, year = map(int, raw.split("/"))
                    validation[neutral] = date(year, month, day).isoformat()
            except ValueError:
                pass
        if validation.get("dateMin", "") > validation.get("dateMax", "9999-12-31"):
            validation.pop("dateMin", None)
            validation.pop("dateMax", None)
    for rule in ("em_validation_q", "em_validation_sq"):
        value = attributes.get(rule)
        if value is not None and _text(value).strip():
            issues.append(
                _issue(
                    "warning",
                    "INVALID_VALIDATION",
                    f"Question {question_code} retains {rule} in its source, but the portable renderer does not enforce this native validation expression.",
                    field_id=field_id,
                    question_code=question_code,
                    details={"rule": rule, "sourceValue": value},
                )
            )
    return _compact(validation)


def _validation_number(
    value: Any,
    source_rule: str,
    issues: list[dict[str, Any]],
    field_id: str,
    question_code: str,
) -> float | None:
    """Read a numeric LimeSurvey validation value without inventing a fallback.

    LimeSurvey also permits dynamic expressions in some validation attributes.
    SurveyStructure currently represents only fixed numeric limits, so retain a
    visible warning instead of converting an expression to zero or silently
    treating it as a fixed rule.
    """
    if value is None or not _text(value).strip():
        return None
    parsed = _optional_number(value)
    if parsed is not None:
        return parsed
    issues.append(
        _issue(
            "warning",
            "INVALID_VALIDATION",
            f"Question {question_code} uses a dynamic {source_rule} expression that cannot be represented as a fixed numeric SurveyStructure validation.",
            field_id=field_id,
            question_code=question_code,
            details={"rule": source_rule, "sourceValue": value},
        )
    )
    return None


def _normalize_answer_count_validation(
    field: dict[str, Any],
    attributes: dict[str, Any],
    issues: list[dict[str, Any]],
    field_id: str,
    question_code: str,
) -> None:
    """Preserve verified fixed matrix limits; diagnose other nonredundant collection rules."""
    if field["type"] == "multiple-input":
        items, cells_per_item, unit = field["subquestions"], 1, "inputs"
    elif field["type"] == "matrix":
        # The verified LimeSurvey answer-count switch excludes native H;
        # sharing a portable matrix type does not establish native applicability.
        if field.get("source", {}).get("nativeType") == "H":
            return
        matrix = field["matrix"]
        items = matrix["rows"]
        cells_per_item = (
            len(matrix["columns"]) if matrix["mode"] in {"text", "number", "multiple"} else 1
        )
        # LimeSurvey counts single answers and complete dual-scale pairs by row;
        # text/numeric matrices count their individual response cells.
        unit = "rows" if matrix["mode"] in {"single", "dual-single"} else "cells"
    else:
        return
    possible = (
        sum(
            item.get("visibility", {}).get("condition") != {"type": "constant", "value": False}
            for item in items
        )
        * cells_per_item
    )
    always_visible = sum(
        not item.get("visibility")
        or item["visibility"]["condition"] == {"type": "constant", "value": True}
        for item in items
    )
    required_per_item = 1 if field.get("matrix", {}).get("mode") == "multiple" else cells_per_item
    guaranteed = always_visible * required_per_item if field.get("required") else 0
    for rule, relation in (("min_answers", "at least"), ("max_answers", "at most")):
        value = _optional_number(attributes.get(rule))
        # Dynamic expressions already have INVALID_VALIDATION from _validation_number.
        if (
            value is None
            or (rule == "min_answers" and value <= guaranteed)
            or (rule == "max_answers" and value >= possible)
        ):
            continue
        if (
            field["type"] == "matrix"
            and field.get("source", {}).get("nativeType") in {";", "F"}
            and value >= 0
        ):
            # Counts are integers: >=1.5 is >=2, <=1.5 is <=1. Keep expressions
            # diagnosed above, rather than pretending a dynamic rule is fixed.
            key = "minAnswers" if rule == "min_answers" else "maxAnswers"
            field.setdefault("responseValidation", {})[key] = (
                math.ceil(value) if rule == "min_answers" else math.floor(value)
            )
            continue
        issues.append(
            _issue(
                "warning",
                "INVALID_VALIDATION",
                f"Question {question_code} requires {relation} {value} answered {unit} ({rule}); this response-count limit is preserved in the source but is not enforced by the portable renderer.",
                field_id=field_id,
                question_code=question_code,
                details={"rule": rule, "sourceValue": attributes[rule]},
            )
        )


def _options(value: Any) -> list[dict[str, Any]]:
    source = _record(value)
    result = []
    for index, (raw_code, raw_value) in enumerate(source.items()):
        row = _record(raw_value)
        code = _text(raw_code).strip()
        if not code:
            continue
        label = _clean_html(
            row.get("answer") or row.get("question") or row.get("label") or raw_value or code
        )
        result.append(
            {
                "code": code,
                "label": label or code,
                "order": _number(row.get("order", row.get("sortorder")), index),
            }
        )
    ordered = sorted(result, key=lambda item: float(item["order"]))  # type: ignore[arg-type]
    for index, item in enumerate(ordered):
        item["order"] = index
    return ordered


def _localized_fixed_labels(language: str) -> dict[str, str]:
    """Return labels for fixed LimeSurvey values in the selected survey language."""
    if _text(language).lower().startswith("es"):
        return {
            "yes": "Sí",
            "no": "No",
            "uncertain": "No sé",
            "increase": "Aumenta",
            "same": "Igual",
            "decrease": "Disminuye",
            "other": "Otro",
            "female": "Femenino",
            "male": "Masculino",
        }
    return {
        "yes": "Yes",
        "no": "No",
        "uncertain": "Uncertain",
        "increase": "Increase",
        "same": "Same",
        "decrease": "Decrease",
        "other": "Other",
        "female": "Female",
        "male": "Male",
    }


def _date_format_tokens(source_format: Any) -> list[tuple[str, int]]:
    """Distinguish calendar months from minutes following hours/before seconds."""
    value = re.sub(
        r"'[^']*'|\"[^\"]*\"", lambda match: " " * len(match.group()), _text(source_format)
    )
    tokens = [
        (match.group()[0].lower(), match.start())
        for match in re.finditer(r"([dmyhis])\1*", value, re.IGNORECASE)
    ]
    return [
        (
            "i"
            if kind == "m"
            and (
                (index > 0 and tokens[index - 1][0] == "h")
                or (index + 1 < len(tokens) and tokens[index + 1][0] == "s")
            )
            else kind,
            position,
        )
        for index, (kind, position) in enumerate(tokens)
    ]


def _date_value_type(source_format: Any) -> str:
    """Map a LimeSurvey date/time display format to its portable stored-value type."""
    kinds = {kind for kind, _ in _date_format_tokens(source_format)}
    has_day, has_month, has_year, has_time = (kind in kinds for kind in ("d", "m", "y", "h"))
    if has_time and (has_day or has_month or has_year):
        return "date-time"
    if has_time:
        return "time"
    if has_year and has_month and not has_day:
        return "month-year"
    if has_year and not has_month and not has_day:
        return "year"
    return "date"


def _date_order(source_format: Any) -> str | None:
    """Preserve whether a combined date/time control displays time before date."""
    if _date_value_type(source_format) != "date-time":
        return None
    tokens = _date_format_tokens(source_format)
    first_time = next(position for kind, position in tokens if kind == "h")
    date_positions = [position for kind, position in tokens if kind in {"d", "m", "y"}]
    return "time-date" if date_positions and first_time < min(date_positions) else "date-time"


def _default_value(field_type: str, value: Any) -> Any:
    """Return the portable default-value shape required by one field variant."""
    if value is None or value == "":
        return None
    if field_type in {"display", "custom"}:
        return None
    if field_type in {"short-text", "long-text", "date"}:
        return _text(value)
    if field_type in {"number", "range"}:
        try:
            number = float(value)
            return int(number) if number.is_integer() else number
        except (TypeError, ValueError):
            return None
    if field_type == "boolean":
        return value if isinstance(value, bool) else _yes(value)
    if field_type in {"yes-no", "gender", "single-choice", "list-with-comment"}:
        return value if isinstance(value, (str, int, float, bool)) else None
    if field_type in {"multiple-choice", "multiple-choice-with-comments", "ranking"}:
        values = value if isinstance(value, list) else [value]
        return [item for item in values if isinstance(item, (str, int, float, bool))]
    if field_type in {"matrix", "multiple-input"}:
        return value if isinstance(value, dict) else None
    return None
