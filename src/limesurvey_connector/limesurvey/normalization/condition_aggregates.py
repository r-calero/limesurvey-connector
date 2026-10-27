"""Only aggregates whose inputs have an unambiguous portable response shape."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any

from .condition_references import (
    ConditionReference,
    ConditionReferenceIndex,
    UnsupportedConditionError,
    resolve_reference,
)
from .condition_tokens import split_arguments

_AGGREGATE = re.compile(r"^(count|sum|min|max)\s*\((.*)\)\s*(==|!=|>=|<=|>|<)\s*(.+)$", re.I | re.S)


def parse_aggregate(
    expression: str,
    references: Mapping[str, ConditionReference],
    current_field_code: str | None,
    operators: Mapping[str, Any],
) -> dict[str, Any] | None:
    if re.match(r"^(?:avg|mean)\s*\(", expression, re.I):
        raise UnsupportedConditionError(
            "avg and mean are not built-in functions in the verified LimeSurvey ExpressionScript core; no alias is assumed."
        )
    match = _AGGREGATE.fullmatch(expression)
    if not match:
        return None
    function, raw_arguments, operator, raw_value = match.groups()
    function = function.lower()
    arguments = split_arguments(raw_arguments)
    macro = re.fullmatch(r"(?:self|that)(?:\.[A-Za-z0-9_]+)*", arguments[0], re.I)
    if function == "count" and len(arguments) == 1 and macro:
        # Existing whole-question count checks also distinguish comments/other.
        return None
    if not isinstance(references, ConditionReferenceIndex):
        raise UnsupportedConditionError(
            "An aggregate requires imported question and response-cell metadata."
        )
    try:
        if not re.fullmatch(
            r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", raw_value.strip()
        ):
            raise ValueError
        value = float(raw_value)
        if not math.isfinite(value) or (
            function == "count" and (value < 0 or not value.is_integer())
        ):
            raise ValueError
    except ValueError as error:
        raise UnsupportedConditionError(
            "Aggregate comparison requires a finite numeric literal (count: non-negative integer)."
        ) from error

    if function in {"min", "max"} and not (
        (operator == "==" and value != 0)
        or (operator == ">" and value >= 0)
        or (operator == ">=" and value > 0)
        or (operator in {"<", "<="} and value < 0)
    ):
        # ponytail: only comparisons whose blank result is false in PHP and JS;
        # wider support needs a versioned source empty-value/coercion policy.
        raise UnsupportedConditionError(
            "min/max require == nonzero, > nonnegative, >= positive, or < / <= negative: other comparisons have unsupported empty-value semantics."
        )

    items = None
    if macro:
        if len(arguments) != 1:
            raise UnsupportedConditionError(
                "Mixed macro and explicit aggregate arguments are unsupported."
            )
        parts = arguments[0].split(".")
        code = parts.pop(1) if parts[0].lower() == "that" and len(parts) > 1 else current_field_code
        selectors = parts[1:]
        if (
            not code
            or not selectors
            or selectors[-1].lower() != "naok"
            or any(part.lower() != "nocomments" for part in selectors[:-1])
        ):
            raise UnsupportedConditionError(
                "Numeric aggregate macros require a question context and .NAOK; filtered/comment selectors are unsupported."
            )
        code, item = resolve_reference(code, references)
        if item:
            raise UnsupportedConditionError("Aggregate macros must name a whole question.")
    else:
        if any(
            not re.fullmatch(r"[A-Za-z0-9_]+(?:#[01])?\.NAOK", argument, re.I)
            for argument in arguments
        ):
            raise UnsupportedConditionError(
                "Explicit aggregate inputs must be response-cell references with .NAOK."
            )
        resolved = [resolve_reference(argument, references) for argument in arguments]
        code = resolved[0][0]
        items = [item for _, item in resolved]
        if any(field != code or not item for field, item in resolved):
            raise UnsupportedConditionError(
                "An aggregate must use response cells from one question, not whole or different questions."
            )
        if len(set(items)) != len(items):
            raise UnsupportedConditionError(
                "Repeated aggregate arguments cannot be represented as a response subset."
            )
        if any(item not in references.response_items.get(code, []) for item in items):
            raise UnsupportedConditionError(
                "Aggregate reference does not identify an imported response cell."
            )

    question = references.questions[code]
    native = question.get("type")
    attributes = (
        (question.get("result") or {}).get("attributes") or question.get("attributes") or {}
    )
    numeric_matrix = native == ":" and str(
        attributes.get("multiflexible_checkbox", "")
    ).upper() not in {"1", "Y"}
    if function != "count":
        # ponytail: numeric cells only; wider aggregates need explicit source-coercion semantics.
        if not numeric_matrix:
            raise UnsupportedConditionError(
                f"{function} is supported only for numeric matrix cells, not text, options or checkbox coercion."
            )
        condition_type = "numeric-aggregate"
    elif native in {"M", "P"}:
        condition_type = "selection-count"
    elif native in {"Q", ";", "F", "H", "A", "B", "C", "E", "1"} or numeric_matrix:
        condition_type = "answered-count"
    else:
        raise UnsupportedConditionError(
            "Count inputs must have one supported, homogeneous response-cell type."
        )
    condition = {
        "type": condition_type,
        "responseReference": {"fieldCode": code},
        "operator": operators[operator],
        "value": int(value) if value.is_integer() else value,
    }
    if items is not None:
        condition["responseItemCodes"] = items
    if function != "count":
        condition["aggregation"] = function
    return condition
