"""Translate the supported LimeSurvey condition subset into portable condition trees."""

from __future__ import annotations

import json
import math
import operator as comparison_operator
import re
from collections.abc import Mapping
from html import unescape
from typing import Any

from .condition_aggregates import parse_aggregate
from .condition_references import (
    ConditionReference,
    ConditionReferenceIndex,
    UnsupportedConditionError,
)
from .condition_references import resolve_reference as _resolve_reference
from .condition_tokens import split_arguments
from .condition_tokens import split_logical as _split_logical
from .condition_tokens import strip_outer_parentheses as _strip_outer_parentheses
from .field_values import _options
from .validation_pattern import portable_text_pattern

_COMPARISON = re.compile(
    r"^([A-Za-z0-9_]+(?:X[0-9]+X[0-9]+X[0-9]+)?(?:_[A-Za-z0-9]+)*(?:#[01])?)"
    r"(?:\.(?:NAOK|code))?\s*(==|!=|>=|<=|>|<)\s*(.+)$",
    re.IGNORECASE,
)

_OPERATORS = {
    "==": "equals",
    "!=": "not-equals",
    ">": "greater-than",
    ">=": "greater-than-or-equal",
    "<": "less-than",
    "<=": "less-than-or-equal",
}

_MACRO_TARGET = r"((?:that|self)(?:\.[A-Za-z0-9_]+)*)"
_COUNT = re.compile(
    rf"^count\s*\(\s*{_MACRO_TARGET}\s*\)\s*(==|!=|>=|<=|>|<)\s*([0-9]+)$",
    re.IGNORECASE,
)
_COUNTIF = re.compile(
    rf"^countif\s*\(\s*['\"](?:Y|1)['\"]\s*,\s*{_MACRO_TARGET}\s*\)"
    r"\s*(==|!=|>=|<=|>|<)\s*([0-9]+)$",
    re.IGNORECASE,
)
_COUNTIFOP = re.compile(
    rf"^countifop\s*\(\s*['\"]==['\"]\s*,\s*['\"](?:Y|1)['\"]\s*,\s*{_MACRO_TARGET}\s*\)"
    r"\s*(==|!=|>=|<=|>|<)\s*([0-9]+)$",
    re.IGNORECASE,
)


def parse_limesurvey_condition(
    expression: str,
    references: Mapping[str, ConditionReference],
    current_field_code: str | None = None,
) -> dict[str, Any] | None:
    # Match LimeSurvey _ProcessRelevance: htmlspecialchars_decode(ENT_QUOTES),
    # once before parsing, including quoted values. Other HTML entities stay literal.
    decoded = _decode_condition_entities(expression or "")
    return _parse_condition(decoded, references, current_field_code)


def _decode_condition_entities(expression: str) -> str:
    def decode(match: re.Match[str]) -> str:
        try:
            value = unescape(match[0])
        except ValueError:  # Extremely long numeric references are not valid special characters.
            return match[0]
        return value if value in {"&", "<", ">", '"', "'"} else match[0]

    return re.sub(r"&(?:amp|lt|gt|quot|#(?:[0-9]+|[xX][0-9a-fA-F]+));", decode, expression)


def _parse_condition(
    expression: str,
    references: Mapping[str, ConditionReference],
    current_field_code: str | None = None,
    *,
    _allow_if: bool = True,
) -> dict[str, Any] | None:
    """Return a neutral condition tree, or ``None`` for an unconditional expression."""
    normalized = _strip_outer_parentheses((expression or "").strip())
    if not normalized or normalized.lower() in {"1", "true"}:
        return None
    if normalized.lower() in {"0", "false"}:
        return {
            "type": "constant",
            "value": False,
        }
    if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", normalized):
        # LimeSurvey ProcessBooleanExpression casts the evaluated number to bool.
        return None if _literal(normalized) != 0 else {"type": "constant", "value": False}

    parts = _split_logical(normalized, "or")
    if len(parts) > 1:
        return {
            "type": "any",
            "conditions": [
                _required(
                    _parse_condition(part, references, current_field_code, _allow_if=_allow_if),
                    part,
                )
                for part in parts
            ],
        }

    parts = _split_logical(normalized, "and")
    if len(parts) > 1:
        return {
            "type": "all",
            "conditions": [
                _required(
                    _parse_condition(part, references, current_field_code, _allow_if=_allow_if),
                    part,
                )
                for part in parts
            ],
        }

    if re.match(r"^not\b", normalized, re.IGNORECASE):
        nested = re.sub(r"^not\b", "", normalized, count=1, flags=re.IGNORECASE).strip()
        return {
            "type": "not",
            "condition": _required(
                _parse_condition(nested, references, current_field_code, _allow_if=_allow_if),
                nested,
            ),
        }
    if normalized.startswith("!"):
        nested = normalized[1:].strip()
        return {
            "type": "not",
            "condition": _required(
                _parse_condition(nested, references, current_field_code, _allow_if=_allow_if),
                nested,
            ),
        }

    conditional = re.fullmatch(r"if\s*\((.*)\)", normalized, re.I | re.S)
    if conditional:
        # ponytail: one-level lowering only; nesting needs a bounded conditional AST.
        if not _allow_if:
            raise UnsupportedConditionError(
                "Nested if is unsupported; boolean expansion is limited to one level."
            )
        arguments = split_arguments(conditional.group(1))
        if len(arguments) != 3:
            raise UnsupportedConditionError("Boolean if requires exactly three arguments.")
        branches = [
            _required(
                _parse_condition(argument, references, current_field_code, _allow_if=False),
                argument,
            )
            for argument in arguments
        ]
        if any(_contains_bare_response(branch) for branch in branches):
            raise UnsupportedConditionError(
                "Boolean if requires explicit conditions, not response-value branches."
            )
        test, when_true, when_false = branches
        return {
            "type": "any",
            "conditions": [
                {"type": "all", "conditions": [test, when_true]},
                {"type": "all", "conditions": [{"type": "not", "condition": test}, when_false]},
            ],
        }

    pattern_condition = _parse_pattern_condition(normalized, references)
    if pattern_condition:
        return pattern_condition

    aggregate = parse_aggregate(normalized, references, current_field_code, _OPERATORS)
    if aggregate:
        return aggregate

    selection_count = next(
        (
            pattern.match(normalized)
            for pattern in (_COUNT, _COUNTIF, _COUNTIFOP)
            if pattern.match(normalized)
        ),
        None,
    )
    if selection_count:
        selector, operator, value = selection_count.groups()
        parts = selector.split(".")
        macro = parts.pop(0)
        referenced_field = parts.pop(0) if macro.lower() == "that" and parts else None
        subselectors = parts[:-1] if parts and parts[-1].lower() in {"naok", "code"} else parts
        if any(part.lower() != "nocomments" for part in subselectors):
            raise UnsupportedConditionError(
                f"Unsupported LimeSurvey count selector: {selector}. Use explicit .NAOK response cells; sq_ requires the source runtime field map."
            )
        target = _resolve_macro_reference(macro, referenced_field, references, current_field_code)
        count_type = _count_type(normalized, target[0], parts, references)
        return {
            "type": count_type,
            "responseReference": _reference_payload(target),
            "operator": _OPERATORS[operator],
            "value": int(value),
        }

    empty_match = re.match(r"^(?:is_empty|empty)\s*\(([^)]+)\)$", normalized, re.IGNORECASE)
    if empty_match:
        reference = empty_match.group(1).strip()
        if re.fullmatch(r"this(?:\.(?:NAOK|code))?", reference, re.I):
            reference = _current_scalar_reference(current_field_code, references)
        return {
            "type": "not-answered",
            "responseReference": _reference_payload(_resolve_reference(reference, references)),
        }

    comparison = _COMPARISON.match(normalized)
    if comparison:
        reference, operator, raw_value = comparison.groups()
        if reference.lower() == "this":
            reference = _current_scalar_reference(current_field_code, references)
        target = _resolve_reference(reference, references)
        fixed_scale = _fixed_scale_comparison(operator, raw_value, target, references)
        if fixed_scale is not None:
            return fixed_scale
        return {
            "type": "comparison",
            "responseReference": _reference_payload(target),
            "operator": _OPERATORS[operator],
            "value": _comparison_literal(raw_value, target, references),
        }

    bare_reference = re.match(
        r"^([A-Za-z0-9_]+(?:X[0-9]+X[0-9]+X[0-9]+)?(?:_[A-Za-z0-9]+)*)(?:\.(?:NAOK|code))?$",
        normalized,
    )
    if bare_reference:
        return {
            "type": "answered",
            "responseReference": _reference_payload(
                _resolve_reference(bare_reference.group(1), references)
            ),
        }

    raise UnsupportedConditionError(f"Unsupported LimeSurvey condition: {expression}")


def _count_type(
    expression: str, code: str, selectors: list[str], references: Mapping[str, ConditionReference]
) -> str:
    """Distinguish selected options from answered cells before building the tree."""
    selected_match = re.match(
        r"^countif(?:op)?\s*\(\s*(?:[\'\"]==[\'\"]\s*,\s*)?[\'\"]([Y1])[\'\"]", expression, re.I
    )
    selected_value = selected_match.group(1) if selected_match else None
    if selected_value not in {None, "Y", "1"}:
        raise UnsupportedConditionError(
            "Count criteria are case-sensitive; only selected codes Y and 1 are supported."
        )
    if not isinstance(references, ConditionReferenceIndex):
        if selected_value == "1":
            raise UnsupportedConditionError(
                "Counting value 1 requires numeric-checkbox matrix metadata."
            )
        return "selection-count"
    question = references.questions.get(code, {})
    native = question.get("type")
    selected_only = selected_match is not None
    other = str(question.get("other", "")).upper() == "Y"
    excludes_comments = "nocomments" in [part.lower() for part in selectors]
    if (
        native in {"M", "P"}
        and selected_value != "1"
        and not other
        and (native == "M" or excludes_comments)
    ):
        return "selection-count"
    if native == "M" and other and not selected_only:
        return "answered-count"
    if native == "R" and not selected_only:
        return "selection-count"
    attributes = (
        (question.get("result") or {}).get("attributes") or question.get("attributes") or {}
    )
    if (
        native == ":"
        and selected_value == "1"
        and str(attributes.get("multiflexible_checkbox", "")).upper() in {"1", "Y"}
    ):
        return "selection-count"
    if (
        native in {"Q", ";", ":", "F", "H", "A", "B", "C", "E", "1"}
        and not selected_only
        and (
            native != ":"
            or str(attributes.get("multiflexible_checkbox", "")).upper() not in {"1", "Y"}
        )
    ):
        return "answered-count"
    raise UnsupportedConditionError(
        f'Count expression for "{code}" (LimeSurvey type {native}) includes responses or filters '
        "that cannot be counted faithfully by the supported neutral condition. The condition was omitted."
    )


def _contains_bare_response(condition: dict[str, Any]) -> bool:
    if condition["type"] == "answered":
        return True
    if condition["type"] in {"all", "any"}:
        return any(_contains_bare_response(child) for child in condition["conditions"])
    return condition["type"] == "not" and _contains_bare_response(condition["condition"])


def _current_scalar_reference(
    current: str | None, references: Mapping[str, ConditionReference]
) -> str:
    if not current:
        raise UnsupportedConditionError(
            'The "this" variable requires a current scalar question context.'
        )
    if isinstance(references, ConditionReferenceIndex):
        native = references.questions.get(current, {}).get("type")
        if native not in {"S", "T", "U", "5", "N", "D", "Y", "G", "L", "!"}:
            raise UnsupportedConditionError(
                'The "this" variable requires a specific response cell; question-level context is insufficient.'
            )
    return current


def _resolve_macro_reference(
    macro: str,
    referenced_field: str | None,
    references: Mapping[str, ConditionReference],
    current_field_code: str | None,
) -> ConditionReference:
    if macro.lower() == "that":
        if not referenced_field:
            raise UnsupportedConditionError('The "that" macro requires a question code.')
        reference = _resolve_reference(referenced_field, references)
        if reference[1]:
            raise UnsupportedConditionError(
                'The "that" macro requires a whole question, not a response cell.'
            )
        return reference
    if not current_field_code:
        raise UnsupportedConditionError(
            'The "self" macro requires the current question context, which is not available here.'
        )
    if referenced_field and referenced_field.lower() not in {"naok", "code"}:
        raise UnsupportedConditionError(
            f"Unsupported LimeSurvey self sub-selector: {referenced_field}"
        )
    return _resolve_reference(current_field_code, references)


def _reference_payload(reference: ConditionReference) -> dict[str, str]:
    field_code, response_item_code = reference
    payload = {"fieldCode": field_code}
    if response_item_code:
        payload["responseItemCode"] = response_item_code
    return payload


def _fixed_scale_comparison(
    operator: str, raw_value: str, target: ConditionReference, references: Any
) -> dict[str, Any] | None:
    if not isinstance(references, ConditionReferenceIndex) or operator not in {
        ">",
        ">=",
        "<",
        "<=",
    }:
        return None
    native = references.questions.get(target[0], {}).get("type")
    if not ((native == "5" and target[1] is None) or (native == "A" and target[1])):
        return None
    value = _literal(raw_value)
    if isinstance(value, str):
        value = _literal(value)
    if type(value) not in {int, float} or not (
        (operator == ">" and value >= 0) or (operator == ">=" and value > 0)
    ):
        # ponytail: only thresholds where a blank response is false in PHP and JS.
        # Wider comparisons require an explicit empty-value policy, not coercion.
        raise UnsupportedConditionError(
            "Fixed five-point scales support > nonnegative or >= positive numeric thresholds; other ordered comparisons have unsupported empty-value semantics."
        )
    compare = {">": comparison_operator.gt, ">=": comparison_operator.ge}[operator]
    conditions = [
        {
            "type": "comparison",
            "responseReference": _reference_payload(target),
            "operator": "equals",
            "value": str(point),
        }
        for point in range(1, 6)
        if compare(point, value)
    ]
    if not conditions:
        return {"type": "constant", "value": False}
    return conditions[0] if len(conditions) == 1 else {"type": "any", "conditions": conditions}


def _comparison_literal(raw_value: str, target: ConditionReference, references: Any) -> Any:
    """Normalize numeric literals against the source response type, not globally.

    LimeSurvey emits both N > "0" and list == 22. The portable contract uses
    numbers for numeric responses and exact string codes for list options.
    """
    value = _literal(raw_value)
    if not isinstance(references, ConditionReferenceIndex):
        return value
    question = references.questions.get(target[0], {})
    if question.get("type") in {"5", "A"} and type(value) in {int, float} and value in range(1, 6):
        return str(int(value))
    if target[1]:
        return value
    if (
        question.get("type") == "N"
        and isinstance(value, str)
        and re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", value.strip())
    ):
        return _literal(value)
    if question.get("type") in {"L", "!", "O"} and type(value) in {int, float}:
        code = str(int(value)) if value == int(value) else str(value)
        result = question.get("result") or {}
        options = _options(result.get("answeroptions") or question.get("answeroptions"))
        if any(option["code"] == code for option in options):
            return code
    return value


def _literal(raw_value: str) -> Any:
    value = _strip_outer_parentheses(raw_value.strip())
    if re.fullmatch(r'"(?:[^"\\]|\\.)*"', value):
        try:
            return json.loads(value)
        except ValueError as error:
            raise UnsupportedConditionError(
                f"Unsupported quoted condition value: {raw_value}"
            ) from error
    if re.fullmatch(r"'(?:[^'\\]|\\.)*'", value):
        return value[1:-1].replace("\\'", "'").replace("\\\\", "\\")
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    try:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Non-finite numeric literal")
        return int(number) if number.is_integer() else number
    except ValueError as error:
        raise UnsupportedConditionError(f"Unsupported condition literal: {raw_value}") from error


def _required(condition: dict[str, Any] | None, expression: str) -> dict[str, Any]:
    if condition is None:
        return {"type": "constant", "value": True}
    return condition


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _parse_pattern_condition(
    expression: str, references: Mapping[str, ConditionReference]
) -> dict[str, Any] | None:
    """Convert one regex comparison with a direct scalar text reference."""
    function = re.fullmatch(r"regexMatch\s*\((.*)\)", expression, re.I | re.S)
    if function:
        raw_arguments = function.group(1).strip()
        if raw_arguments and raw_arguments[0] in "/#~%!@":
            end = raw_arguments.rfind(raw_arguments[0])
            tail = re.fullmatch(r"([ims]*)\s*,\s*(.+)", raw_arguments[end + 1 :], re.S)
            arguments = [raw_arguments[: end + 1] + tail.group(1), tail.group(2)] if tail else []
        else:
            arguments = split_arguments(raw_arguments)
        if len(arguments) != 2:
            raise UnsupportedConditionError(
                "regexMatch requires one pattern and one direct response reference."
            )
        pattern, reference = arguments
    else:
        operator = re.fullmatch(
            r"([A-Za-z0-9_]+(?:\.NAOK)?)\s*(?:REGEXP|=~)\s*(.+)", expression, re.I | re.S
        )
        if not operator:
            return None
        reference, pattern = operator.groups()
    if not re.fullmatch(r"[A-Za-z0-9_]+(?:\.NAOK)?", reference.strip(), re.I):
        raise UnsupportedConditionError("Regex conditions require a direct response reference.")
    raw = pattern.strip()
    if len(raw) >= 2 and raw[0] in {"'", '"'} and raw[-1] == raw[0]:
        raw = raw[1:-1]
    if not function and raw and raw[0] not in "/#~%!@":
        delimiter = next((d for d in "/#~%!@" if d not in raw), None)
        if delimiter:
            raw = delimiter + raw + delimiter
    portable = portable_text_pattern(raw)
    if not portable:
        raise UnsupportedConditionError(
            "Regex pattern is outside the supported PCRE/JavaScript subset."
        )
    code, item = _resolve_reference(
        re.sub(r"\.NAOK$", "", reference.strip(), flags=re.I), references
    )
    if not isinstance(references, ConditionReferenceIndex):
        raise UnsupportedConditionError("Regex conditions require source question metadata.")
    question = references.questions.get(code, {})
    if item is not None or question.get("type") not in {"S", "T", "U"}:
        raise UnsupportedConditionError("Regex conditions support one scalar text question.")
    return {
        "type": "pattern-match",
        "responseReference": {"fieldCode": code},
        "pattern": portable["responseFormatPattern"],
        **({"patternFlags": portable["patternFlags"]} if "patternFlags" in portable else {}),
    }
