"""Per-field semantic rules (port of ``field-invariants.ts`` in survey-structure)."""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from typing import Any

from survey_structure import _js
from survey_structure._js import UNDEFINED
from survey_structure.month_day import is_month_day
from survey_structure.numeric_text import is_numeric_text, number_character_length
from survey_structure.patterns import compile_pattern, utf16_units
from survey_structure.validation_pattern import validation_pattern_source

Report = Callable[[dict[str, Any]], None]

FIELD_WIDGET_COMPATIBILITY: dict[str, list[str]] = {
    "short-text": ["text-input"],
    "long-text": ["text-area"],
    "number": ["text-input"],
    "date": ["date-picker"],
    "yes-no": ["radio-group", "button-group", "dropdown"],
    "gender": ["gender-selector", "radio-group", "button-group", "dropdown"],
    "single-choice": [
        "radio-group",
        "button-group",
        "rating",
        "emoticon-slider",
        "dropdown",
        "numbered-radio-group",
    ],
    "list-with-comment": ["dropdown"],
    "multiple-choice": ["dropdown", "checkbox-group", "checkbox-group-with-comments"],
    "multiple-choice-with-comments": ["checkbox-group-with-comments"],
    "matrix": ["matrix-grid"],
    "multiple-input": ["multiple-input-list"],
    "ranking": ["ranking-list"],
    "display": ["text-input"],
    "boolean": ["checkbox", "toggle"],
    "range": ["slider", "rating"],
    "custom": ["custom"],
}

_MULTIPLE_SELECTION = ("multiple-choice", "multiple-choice-with-comments", "ranking")
_CHECKBOX = ("multiple-choice", "multiple-choice-with-comments")
_GRADABLE = (
    "short-text",
    "long-text",
    "number",
    "range",
    "yes-no",
    "gender",
    "single-choice",
    "list-with-comment",
    "multiple-choice",
    "multiple-choice-with-comments",
    "boolean",
    "date",
)
_MULTI_NUMERIC_RULES = (
    "itemMin",
    "itemMax",
    "sumMin",
    "sumMax",
    "sumEquals",
    "itemMinReference",
    "itemMaxReference",
    "sumMinReference",
    "sumMaxReference",
    "sumEqualsReference",
    "sumAllowsMissing",
)


def _matrix_mode(field: dict[str, Any]) -> str | None:
    return field["matrix"]["mode"] if field["type"] == "matrix" else None


def _custom(report: Report, path: list[str], message: str) -> None:
    report({"code": "custom", "path": path, "message": message})


def _pattern_test(rules: dict[str, Any], value: str) -> bool | None:
    """``new RegExp(source, flags).test(value)``; ``None`` when the pattern does not compile."""
    pattern = compile_pattern(validation_pattern_source(rules), rules.get("patternFlags", ""))
    if pattern is None:
        return None
    return pattern.search(utf16_units(value)) is not None


def validate_field_rules(field: dict[str, Any], report: Report) -> None:
    field_type = field["type"]
    code = field["code"]
    if field_type == "range" and field.get("responseValueType") == "text":
        _custom(
            report, ["responseValueType"], "A range control cannot preserve numeric input as text."
        )
    widget = field.get("rendering", {}).get("widget")
    if widget and widget not in FIELD_WIDGET_COMPATIBILITY[field_type]:
        report(
            {
                "code": "custom",
                "path": ["rendering", "widget"],
                "message": f'Widget "{widget}" is not compatible with field type "{field_type}".',
                "params": {
                    "reason": "widget-not-compatible-with-field-type",
                    "fieldCode": code,
                    "semanticFieldType": field_type,
                    "widget": widget,
                    "allowedWidgets": FIELD_WIDGET_COMPATIBILITY[field_type],
                },
            }
        )

    if field.get("commentResponseKey") and field_type != "list-with-comment":
        _custom(
            report, ["commentResponseKey"], "commentResponseKey requires a list-with-comment field."
        )
    options = field.get("options")
    if options is not None:
        if field_type != "multiple-choice-with-comments" and any(
            option.get("commentResponseKey") for option in options
        ):
            _custom(
                report,
                ["options"],
                "Option commentResponseKey requires multiple-choice-with-comments.",
            )
        if any(option.get("exclusive") for option in options) and field_type not in _CHECKBOX:
            _custom(report, ["options"], "Exclusive options require a checkbox question.")
        if any(option.get("visibility") for option in options) and field_type not in _CHECKBOX:
            _custom(report, ["options"], "Option visibility is supported for checkbox questions.")

    validation = field.get("responseValidation")
    if widget == "rating" and field_type == "range":
        rules = validation or {}
        maximum = rules.get("max", UNDEFINED)
        if (
            not _js.strict_equal(rules.get("min", UNDEFINED), 1)
            or not (_js.is_number(maximum) and _js.is_integer(maximum))
            or maximum > 10
            or maximum < 1
            or rules.get("integer") is not True
        ):
            _custom(
                report, ["rendering"], "Rating requires integer values from 1 to a maximum of 10."
            )
    if field.get("grading") and field_type not in _GRADABLE:
        _custom(
            report,
            ["grading"],
            "Automatic grading requires a scalar or checkbox question; matrices use grading per row.",
        )

    if validation:
        _validate_rule_applicability(field, validation, report)

    other = field.get("other")
    if other and any(option["code"] == other["code"] for option in field["options"]):
        report(
            {
                "code": "custom",
                "path": ["other", "code"],
                "message": "The Other response must use a code distinct from ordinary options.",
                "params": {"reason": "other-option-code-collision", "fieldCode": code},
            }
        )
    if other and other.get("commentResponseKey") and field_type != "multiple-choice-with-comments":
        report(
            {
                "code": "custom",
                "path": ["other", "commentResponseKey"],
                "message": "commentResponseKey applies only to multiple-choice-with-comments fields.",
                "params": {
                    "reason": "other-comment-key-incompatible-field-type",
                    "fieldCode": code,
                    "semanticFieldType": field_type,
                },
            }
        )
    if (
        other
        and "commentRequired" in other
        and (field_type != "multiple-choice-with-comments" or not other.get("commentResponseKey"))
    ):
        _custom(
            report,
            ["other", "commentRequired"],
            "commentRequired requires a multiple-choice-with-comments field and commentResponseKey.",
        )
    if other and field_type in ("yes-no", "gender", "ranking"):
        report(
            {
                "code": "custom",
                "path": ["other"],
                "message": f'Field type "{field_type}" cannot declare an Other response.',
                "params": {
                    "reason": "other-response-incompatible-field-type",
                    "fieldCode": code,
                    "semanticFieldType": field_type,
                },
            }
        )
    _validate_response_encoding(field, report)
    _validate_default_value(field, report)
    default = field.get("defaultValue", UNDEFINED)
    if (
        field_type == "date"
        and default is not UNDEFINED
        and not _is_date_default(field["dateValueType"], default)
    ):
        report(
            {
                "code": "custom",
                "path": ["defaultValue"],
                "message": f"defaultValue does not match dateValueType {field['dateValueType']}.",
                "params": {
                    "reason": "date-default-value-format-mismatch",
                    "fieldCode": code,
                    "dateValueType": field["dateValueType"],
                },
            }
        )


def _validate_rule_applicability(
    field: dict[str, Any], validation: dict[str, Any], report: Report
) -> None:
    field_type = field["type"]
    code = field["code"]
    mode = _matrix_mode(field)
    if ("dateMin" in validation or "dateMax" in validation) and not (
        field_type == "date" and field["dateValueType"] in ("date", "date-time")
    ):
        _custom(
            report,
            ["responseValidation"],
            f'Field "{code}" can only declare dateMin/dateMax for a calendar date or date-time.',
        )
    if "rangeBehavior" in validation and not any(
        key in validation for key in ("min", "max", "dateMin", "dateMax")
    ):
        _custom(
            report,
            ["responseValidation", "rangeBehavior"],
            "rangeBehavior requires a numeric or date bound.",
        )
    numeric = (
        "min" in validation
        or "max" in validation
        or ("integer" in validation and field_type != "multiple-input")
    )
    if (
        "integer" in validation
        and field_type == "multiple-input"
        and validation.get("numericText") is not True
    ):
        _rule_issue(
            report,
            f'Field "{code}" requires numericText for integer multiple inputs.',
            field,
            ["integer"],
        )
    multi_numeric = any(key in validation for key in _MULTI_NUMERIC_RULES)
    if multi_numeric and (
        field_type != "multiple-input" or validation.get("numericText") is not True
    ):
        _rule_issue(
            report,
            f'Field "{code}" can only declare multiple numeric rules for numeric multiple inputs.',
            field,
            ["itemMin", "itemMax", "sumMin", "sumMax", "sumEquals", "sumAllowsMissing"],
        )
    text_rules = "minLength" in validation or "responseFormatPattern" in validation
    text_field = field_type in ("short-text", "long-text")
    numeric_text_field = field_type == "number" and field.get("responseValueType") == "text"
    if (
        "numericText" in validation
        and not text_field
        and field_type != "multiple-input"
        and mode != "text"
    ):
        _rule_issue(
            report,
            f'Field "{code}" cannot require numeric text for this response type.',
            field,
            ["numericText"],
        )
    if (
        "maxLength" in validation
        and not text_field
        and field_type not in ("number", "multiple-input")
        and mode != "text"
    ):
        _rule_issue(
            report,
            f'Field "{code}" cannot declare maxLength for this response type.',
            field,
            ["maxLength"],
        )
    selection = "minSelections" in validation or "maxSelections" in validation
    answers = "minAnswers" in validation or "maxAnswers" in validation
    if answers and mode not in ("single", "text"):
        _rule_issue(
            report,
            f'Field "{code}" cannot declare minAnswers or maxAnswers. These rules count answered rows '
            "in single matrices or cells in text matrices.",
            field,
            ["minAnswers", "maxAnswers"],
        )
    if numeric and field_type not in ("number", "range") and mode != "number":
        _rule_issue(
            report,
            f'Field "{code}" has type "{field_type}", so it cannot declare numeric '
            "min, max or integer rules.",
            field,
            ["min", "max", "integer"],
        )
    if text_rules and not text_field and not (numeric_text_field and "minLength" not in validation):
        _rule_issue(
            report,
            f'Field "{code}" has type "{field_type}", so it cannot declare minLength or pattern rules.',
            field,
            ["minLength", "responseFormatPattern"],
        )
    if selection and field_type not in _MULTIPLE_SELECTION:
        _rule_issue(
            report,
            f'Field "{code}" has type "{field_type}", so it cannot declare minSelections '
            "or maxSelections. These rules apply only to fields that allow multiple selections.",
            field,
            ["minSelections", "maxSelections"],
        )


def _validate_response_encoding(field: dict[str, Any], report: Report) -> None:
    encoding = field.get("responseEncoding")
    if not encoding:
        return
    field_type = field["type"]
    supported = field_type in ("multiple-choice", "multiple-choice-with-comments", "boolean") or (
        field_type == "matrix" and field["matrix"]["mode"] == "multiple"
    )
    if not supported:
        report(
            {
                "code": "custom",
                "path": ["responseEncoding"],
                "message": f'Field type "{field_type}" does not produce selected/unselected response values.',
                "params": {
                    "reason": "response-encoding-incompatible-field-type",
                    "fieldCode": field["code"],
                    "semanticFieldType": field_type,
                },
            }
        )
    if _js.typeof(encoding["selectedValue"]) != _js.typeof(encoding["unselectedValue"]):
        report(
            {
                "code": "custom",
                "path": ["responseEncoding"],
                "message": "selectedValue and unselectedValue must use the same JSON primitive type.",
                "params": {
                    "reason": "response-encoding-value-type-mismatch",
                    "fieldCode": field["code"],
                },
            }
        )
    if ("selectedLabel" in encoding) != ("unselectedLabel" in encoding):
        report(
            {
                "code": "custom",
                "path": ["responseEncoding"],
                "message": "selectedLabel and unselectedLabel must be provided together or both omitted.",
                "params": {
                    "reason": "response-encoding-label-pair-incomplete",
                    "fieldCode": field["code"],
                },
            }
        )


def _invalid_number(
    value: float, rules: dict[str, Any], check_character_length: bool = True
) -> bool:
    out_of_range = rules.get("rangeBehavior") != "warning" and (
        ("min" in rules and value < rules["min"]) or ("max" in rules and value > rules["max"])
    )
    return (
        out_of_range
        or (rules.get("integer") is True and not _js.is_integer(value))
        or (
            check_character_length
            and "maxLength" in rules
            and number_character_length(value) > rules["maxLength"]
        )
    )


def _validate_default_value(field: dict[str, Any], report: Report) -> None:
    default = field.get("defaultValue", UNDEFINED)
    if default is UNDEFINED:
        return
    field_type = field["type"]
    rules = field.get("responseValidation", {})

    def invalid(path: list[str | int] | None = None) -> None:
        report(
            {
                "code": "custom",
                "path": ["defaultValue", *(path or [])],
                "message": "defaultValue violates its field validation.",
                "params": {
                    "reason": "default-value-validation-mismatch",
                    "fieldCode": field["code"],
                },
            }
        )

    if field_type in ("number", "range"):
        if field_type == "number" and field.get("responseValueType") == "text":
            matches = True
            if isinstance(default, str) and "responseFormatPattern" in rules:
                matches = _pattern_test(rules, default) is not False
            if (
                not isinstance(default, str)
                or not is_numeric_text(default)
                or not math.isfinite(float(_js.trim(default)))
                or _invalid_number(float(_js.trim(default)), rules, False)
                or ("maxLength" in rules and _js.length(default) > rules["maxLength"])
                or not matches
            ):
                invalid()
        elif not _js.is_number(default) or _invalid_number(default, rules):
            invalid()
    if field_type == "date" and rules.get("rangeBehavior") != "warning":
        day = _utf16_prefix(default, 10)
        if ("dateMin" in rules and day < rules["dateMin"]) or (
            "dateMax" in rules and day > rules["dateMax"]
        ):
            invalid()
    if field_type in ("short-text", "long-text"):
        if ("minLength" in rules and _js.length(default) < rules["minLength"]) or (
            "maxLength" in rules and _js.length(default) > rules["maxLength"]
        ):
            invalid()
        if "responseFormatPattern" in rules and _pattern_test(rules, default) is False:
            invalid()

    if "options" in field:
        allowed = [option["code"] for option in field["options"]]
        if field.get("other"):
            allowed.append(field["other"]["code"])
        is_list = isinstance(default, list)
        for index, code in enumerate(default if is_list else [default]):
            if not any(_js.strict_equal(code, item) for item in allowed):
                _unknown_default(report, field, [index] if is_list else [], code)
        if is_list:
            if ("minSelections" in rules and len(default) < rules["minSelections"]) or (
                "maxSelections" in rules and len(default) > rules["maxSelections"]
            ):
                invalid()
            duplicate = _first_duplicate(default)
            if duplicate:
                report(
                    {
                        "code": "custom",
                        "path": ["defaultValue"],
                        "message": f'defaultValue repeats option code "{duplicate}".',
                        "params": {
                            "reason": "duplicate-default-option-code",
                            "fieldCode": field["code"],
                            "optionCode": duplicate,
                        },
                    }
                )
            if field_type == "ranking" and (
                len(default) != len(field["options"])
                or any(option["code"] not in default for option in field["options"])
            ):
                report(
                    {
                        "code": "custom",
                        "path": ["defaultValue"],
                        "message": "A ranking defaultValue must contain every declared option exactly once.",
                        "params": {
                            "reason": "ranking-default-not-a-complete-order",
                            "fieldCode": field["code"],
                        },
                    }
                )
        return

    if field_type == "multiple-input":
        codes = {item["code"] for item in field["subquestions"]}
        for key in _js.keys(default):
            if key not in codes:
                _unknown_default(report, field, [key], key, "subquestion")
        for key in _js.keys(default):
            value = default[key]
            if (
                "maxLength" in rules
                and isinstance(value, str)
                and _js.length(value) > rules["maxLength"]
            ):
                invalid([key])
        return
    if field_type != "matrix":
        return

    matrix = field["matrix"]
    rows = {row["code"] for row in matrix["rows"]}
    columns = {column["code"] for column in matrix["columns"]}
    for row_code in _js.keys(default):
        row_value = default[row_code]
        if row_code not in rows:
            _unknown_default(report, field, [row_code], row_code, "matrix row")
        if matrix["mode"] == "single":
            if row_value not in columns:
                _unknown_default(report, field, [row_code], row_value, "matrix column")
            continue
        for column_code in _js.keys(row_value):
            if column_code not in columns:
                _unknown_default(
                    report, field, [row_code, column_code], column_code, "matrix column"
                )
            value = row_value[column_code]
            if (
                matrix["mode"] == "text"
                and isinstance(value, str)
                and "maxLength" in rules
                and _js.length(value) > rules["maxLength"]
            ):
                invalid([row_code, column_code])
            if matrix["mode"] == "dual-single":
                scale = next(
                    (column for column in matrix["columns"] if column["code"] == column_code), None
                )
                if scale and not any(
                    _js.strict_equal(option["code"], value) for option in scale["options"]
                ):
                    _unknown_default(report, field, [row_code, column_code], value, "scale option")
            if (
                matrix["mode"] == "number"
                and _js.is_number(value)
                and _invalid_number(value, rules)
            ):
                invalid([row_code, column_code])


def _utf16_prefix(value: str, units: int) -> str:
    """``value.slice(0, units)`` measured in UTF-16 code units."""
    encoded = value.encode("utf-16-le", "surrogatepass")[: units * 2]
    return encoded.decode("utf-16-le", "surrogatepass")


def _unknown_default(
    report: Report,
    field: dict[str, Any],
    suffix: list[str | int],
    value: object,
    item: str = "option",
) -> None:
    text = _js.to_string(value)
    report(
        {
            "code": "custom",
            "path": ["defaultValue", *suffix],
            "message": f'defaultValue references unknown {item} code "{text}" in field "{field["code"]}".',
            "params": {
                "reason": "default-value-reference-missing",
                "fieldCode": field["code"],
                "responseItemCode": text,
                "itemType": item,
            },
        }
    )


def _first_duplicate(values: list[str]) -> str | None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None


def _rule_issue(report: Report, message: str, field: dict[str, Any], rules: list[str]) -> None:
    report(
        {
            "code": "custom",
            "path": ["responseValidation"],
            "message": message,
            "params": {
                "reason": "validation-rule-not-applicable",
                "fieldCode": field["code"],
                "semanticFieldType": field["type"],
                "rules": rules,
            },
        }
    )


_DATE_PATTERNS = {
    "date": re.compile(r"^\d{4}-\d{2}-\d{2}\Z", re.ASCII),
    "month-year": re.compile(r"^\d{4}-\d{2}\Z", re.ASCII),
    "date-time": re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?\Z", re.ASCII
    ),
    "time": re.compile(r"^\d{2}:\d{2}(?::\d{2})?\Z", re.ASCII),
    "year": re.compile(r"^\d{4}\Z", re.ASCII),
}
_OFFSET = re.compile(r"[+-](\d{2}):(\d{2})\Z", re.ASCII)
_OFFSET_OR_ZONE = re.compile(r"Z|[+-].*\Z", re.ASCII | re.DOTALL)


def _is_date_default(kind: str, value: str) -> bool:
    if kind == "month-day":
        return is_month_day(value)
    if not _DATE_PATTERNS[kind].search(value):
        return False
    if kind == "year":
        return int(value) >= 1
    if kind != "time":
        parts = [int(part) for part in value.split("T")[0].split("-")]
        year, month = parts[0], parts[1]
        day = parts[2] if len(parts) > 2 else 1
        if year < 1 or month < 1 or month > 12:
            return False
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        days = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if day < 1 or day > days[month - 1]:
            return False
    if kind in ("time", "date-time"):
        time = value if kind == "time" else value.split("T")[1]
        pieces = _OFFSET_OR_ZONE.sub("", time, count=1).split(":")
        hour, minute = pieces[0], pieces[1]
        second = pieces[2] if len(pieces) > 2 else "0"
        if int(hour) > 23 or int(minute) > 59 or float(second) >= 60:
            return False
        offset = _OFFSET.search(time)
        if offset and (int(offset.group(1)) > 23 or int(offset.group(2)) > 59):
            return False
    return True
