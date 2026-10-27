"""SurveyStructure 2.1.0 and SurveyLoadResult schemas, in the reference definition order."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from survey_structure._field_rules import validate_field_rules
from survey_structure._invariants import validate_survey_invariants
from survey_structure._js import JS_WHITESPACE, strict_equal
from survey_structure._schema import (
    Array,
    Boolean,
    DiscriminatedUnion,
    Enum,
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
)
from survey_structure.language import is_valid_language_tag
from survey_structure.patterns import is_valid_pattern

SURVEY_STRUCTURE_VERSION = "2.1.0"

_SPACE = re.escape(JS_WHITESPACE)
code_schema = (
    String()
    .min(1)
    .regex(
        re.compile(rf"^[^{_SPACE}](?:[\s\S]*[^{_SPACE}])?\Z"),
        "Codes cannot contain leading or trailing whitespace.",
    )
)
json_scalar_schema = Union(String(), Number().finite(), Boolean())
json_primitive_schema = Union(json_scalar_schema, Null())
json_value_schema: Schema = Lazy(
    lambda: Union(json_primitive_schema, Array(json_value_schema), Record(json_value_schema))
)
platform_schema = String().regex(
    re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z"),
    "platform must be a lowercase kebab-case identifier.",
)
language_schema = (
    String().min(1).refine(is_valid_language_tag, "Use a language tag such as es, es-MX or en.")
)

# Grading
grading_schema = Object(
    {
        "points": Number().finite().nonnegative(),
        "correctAnswers": Array(json_primitive_schema).min(1),
        "whenRight": String().optional(),
        "whenWrong": String().optional(),
        "generalFeedback": String().optional(),
    }
)

# Conditions
_OPERATORS = (
    "equals",
    "not-equals",
    "greater-than",
    "greater-than-or-equal",
    "less-than",
    "less-than-or-equal",
)
_PATTERN_FLAGS = re.compile(r"^(?!.*(.).*\1)[ims]*\Z")
condition_reference_schema = Object(
    {
        "fieldCode": code_schema,
        "responseItemCode": code_schema.optional(),
    }
)
_comparison = Object(
    {
        "type": LiteralValue("comparison"),
        "responseReference": condition_reference_schema,
        "operator": Enum(*_OPERATORS),
        "value": json_primitive_schema,
    }
)
_answered = Object(
    {
        "type": Enum("answered", "not-answered"),
        "responseReference": condition_reference_schema,
    }
)


def _validate_condition_pattern(
    condition: dict[str, Any], report: Callable[[dict[str, Any]], None]
) -> None:
    if not is_valid_pattern(condition["pattern"], condition.get("patternFlags", "")):
        report({"code": "custom", "path": ["pattern"], "message": "Invalid ECMAScript pattern."})


_pattern_match = Object(
    {
        "type": LiteralValue("pattern-match"),
        "responseReference": condition_reference_schema,
        "pattern": String(),
        "patternFlags": String().regex(_PATTERN_FLAGS).optional(),
    }
).super_refine(_validate_condition_pattern)
_selection_count = Object(
    {
        "type": LiteralValue("selection-count"),
        "responseReference": condition_reference_schema,
        "responseItemCodes": Array(code_schema).min(1).optional(),
        "operator": Enum(*_OPERATORS),
        "value": Number().int().nonnegative(),
    }
)
_answered_count = _selection_count.extend({"type": LiteralValue("answered-count")})
_numeric_aggregate = _selection_count.extend(
    {
        "type": LiteralValue("numeric-aggregate"),
        "aggregation": Enum("sum", "min", "max"),
        "value": Number().finite(),
    }
)
_constant = Object({"type": LiteralValue("constant"), "value": Boolean()})
condition_schema: Schema = Lazy(
    lambda: Union(
        _comparison,
        _answered,
        _pattern_match,
        _selection_count,
        _answered_count,
        _numeric_aggregate,
        _constant,
        Object({"type": Enum("all", "any"), "conditions": Array(condition_schema).min(1)}),
        Object({"type": LiteralValue("not"), "condition": condition_schema}),
    )
)
visibility_schema = Object({"condition": condition_schema})

# Collections
option_schema = Object(
    {
        "code": code_schema,
        "label": String(),
        "commentResponseKey": code_schema.optional(),
        "exclusive": Boolean().optional(),
        "visibility": visibility_schema.optional(),
        "order": Number().int().nonnegative().optional(),
    }
)
subquestion_schema = Object(
    {
        "id": String().optional(),
        "code": code_schema,
        "label": String(),
        "order": Number().int().nonnegative().optional(),
    }
)
_matrix_item = option_schema.omit("exclusive", "commentResponseKey")
basic_matrix_schema = Object(
    {
        "mode": Enum("single", "multiple", "text"),
        "rows": Array(
            _matrix_item.extend(
                {
                    "visibility": visibility_schema.optional(),
                    "grading": grading_schema.optional(),
                    "required": Boolean().optional(),
                }
            )
        ),
        "columns": Array(_matrix_item),
        "cells": Array(
            Object(
                {
                    "rowCode": code_schema,
                    "columnCode": code_schema,
                    "visibility": visibility_schema,
                }
            )
        ).optional(),
    }
)
number_matrix_schema = basic_matrix_schema.extend({"mode": LiteralValue("number")})
dual_matrix_schema = basic_matrix_schema.extend(
    {
        "mode": LiteralValue("dual-single"),
        "columns": Array(_matrix_item.extend({"options": Array(_matrix_item).min(1)})).length(2),
    }
)

# Rendering, responses and validation
rendering_schema = Object(
    {
        "widget": Enum(
            "text-input",
            "text-area",
            "date-picker",
            "checkbox",
            "slider",
            "radio-group",
            "button-group",
            "emoticon-slider",
            "dropdown",
            "toggle",
            "checkbox-group-with-comments",
            "gender-selector",
            "matrix-grid",
            "multiple-input-list",
            "rating",
            "numbered-radio-group",
            "ranking-list",
            "checkbox-group",
            "custom",
        ).optional(),
        "placeholder": String().optional(),
        "showLabel": Boolean().optional(),
        "disabled": Boolean().optional(),
        "hidden": Boolean().optional(),
        "inputType": Enum(
            "text", "email", "number", "date", "datetime", "range", "password"
        ).optional(),
        "inputMode": Enum("text", "numeric", "decimal", "tel", "email", "url", "search").optional(),
        "dateOrder": Enum("date-time", "time-date").optional(),
        "dateFormat": Enum("dmy", "mdy", "ymd").optional(),
        "dateDropdowns": Boolean().optional(),
        "monthLabelStyle": Enum("short", "long", "numeric").optional(),
        "reverseYearOrder": Boolean().optional(),
        "yearMin": Number().int().optional(),
        "yearMax": Number().int().optional(),
        "randomizationGroup": String().min(1).optional(),
        "searchable": Boolean().optional(),
        "optionsLayout": Enum("horizontal", "vertical").optional(),
        "ratingIcon": Enum("star", "heart", "thumb-up").optional(),
        "scaleMinLabel": String().optional(),
        "scaleMaxLabel": String().optional(),
    }
)
response_encoding_schema = Object(
    {
        "selectedValue": json_scalar_schema,
        "unselectedValue": json_scalar_schema,
        "selectedLabel": String().min(1).optional(),
        "unselectedLabel": String().min(1).optional(),
    }
).refine(
    lambda value: not strict_equal(value["selectedValue"], value["unselectedValue"]),
    "selectedValue and unselectedValue must be different.",
)
other_response_schema = Object(
    {
        "code": code_schema,
        "label": String().min(1),
        "textResponseKey": code_schema,
        "commentResponseKey": code_schema.optional(),
        "textRequired": Boolean().optional(),
        "commentRequired": Boolean().optional(),
    }
)


def _is_calendar_date(value: str) -> bool:
    """``new Date(value + "T00:00:00Z")`` round-trips to the same YYYY-MM-DD."""
    if not _ISO_DATE.fullmatch(value):
        return False
    year, month, day = (int(part) for part in value.split("-"))
    if not 1 <= month <= 12:
        return False
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    return 1 <= day <= days[month - 1]


_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)
_date_bound_schema = (
    String()
    .regex(re.compile(r"^\d{4}-\d{2}-\d{2}\Z", re.ASCII))
    .refine(_is_calendar_date, "Use a valid ISO calendar date (YYYY-MM-DD).")
)
_BOUND_RULES = ("itemMin", "itemMax", "sumMin", "sumMax", "sumEquals")


def _validate_rules(validation: dict[str, Any], report: Callable[[dict[str, Any]], None]) -> None:
    date_min, date_max = validation.get("dateMin"), validation.get("dateMax")
    if date_min is not None and date_max is not None and date_min > date_max:
        report(
            {
                "code": "custom",
                "path": ["dateMax"],
                "message": "dateMax must be on or after dateMin.",
            }
        )
    pattern = validation.get("responseFormatPattern")
    if isinstance(pattern, str) and not is_valid_pattern(
        pattern, validation.get("patternFlags", "")
    ):
        report(
            {
                "code": "custom",
                "path": ["responseFormatPattern"],
                "message": "responseFormatPattern must be valid ECMAScript regular expression source without flags.",
                "params": {"reason": "invalid-validation-pattern"},
            }
        )
    if pattern is None and "patternFlags" in validation:
        report(
            {
                "code": "custom",
                "path": ["responseFormatPattern"],
                "message": "Pattern options require a pattern.",
            }
        )
    for rule in _BOUND_RULES:
        if rule in validation and f"{rule}Reference" in validation:
            report(
                {
                    "code": "custom",
                    "path": [f"{rule}Reference"],
                    "message": f"Use a fixed {rule} or a reference, not both.",
                }
            )
    for minimum, maximum in (
        ("min", "max"),
        ("minLength", "maxLength"),
        ("minSelections", "maxSelections"),
        ("minAnswers", "maxAnswers"),
        ("itemMin", "itemMax"),
        ("sumMin", "sumMax"),
    ):
        low, high = validation.get(minimum), validation.get(maximum)
        if low is not None and high is not None and low > high:
            report(
                {
                    "code": "custom",
                    "path": [maximum],
                    "message": f"{maximum} must be greater than or equal to {minimum}.",
                }
            )
    total = validation.get("sumEquals")
    if total is not None and (
        ("sumMin" in validation and total < validation["sumMin"])
        or ("sumMax" in validation and total > validation["sumMax"])
    ):
        report(
            {
                "code": "custom",
                "path": ["sumEquals"],
                "message": "sumEquals must satisfy the sum bounds.",
            }
        )


response_validation_schema = Object(
    {
        "min": Number().finite().optional(),
        "max": Number().finite().optional(),
        "dateMin": _date_bound_schema.optional(),
        "dateMax": _date_bound_schema.optional(),
        "rangeBehavior": Enum("warning", "error").optional(),
        "minLength": Number().int().nonnegative().optional(),
        "maxLength": Number().int().nonnegative().optional(),
        "minSelections": Number().int().nonnegative().optional(),
        "maxSelections": Number().int().nonnegative().optional(),
        "minAnswers": Number().int().nonnegative().optional(),
        "maxAnswers": Number().int().nonnegative().optional(),
        "integer": Boolean().optional(),
        "numericText": Boolean().optional(),
        "itemMin": Number().finite().optional(),
        "itemMax": Number().finite().optional(),
        "sumMin": Number().finite().optional(),
        "sumMax": Number().finite().optional(),
        "sumEquals": Number().finite().optional(),
        "itemMinReference": String().min(1).optional(),
        "itemMaxReference": String().min(1).optional(),
        "sumMinReference": String().min(1).optional(),
        "sumMaxReference": String().min(1).optional(),
        "sumEqualsReference": String().min(1).optional(),
        "sumAllowsMissing": Boolean().optional(),
        "responseFormatPattern": String().optional(),
        "patternFlags": String().regex(_PATTERN_FLAGS).optional(),
        "messages": Record(String()).optional(),
    }
).super_refine(_validate_rules)

# Source traceability
_native_validation = Object(
    {
        name: String().optional()
        for name in (
            "minimumNumericValueExpression",
            "maximumNumericValueExpression",
            "minimumAnswerExpression",
            "maximumAnswerExpression",
            "minimumAnswersExpression",
            "maximumAnswersExpression",
            "questionValidationExpression",
            "subquestionValidationExpression",
            "minimumCellValueExpression",
            "maximumCellValueExpression",
            "cellStepExpression",
            "minimumDateExpression",
            "maximumDateExpression",
            "maximumCharactersExpression",
            "maximumRankingItemsExpression",
            "regularExpression",
            "minimumNumericAnswerValueExpression",
            "maximumNumericAnswerValueExpression",
        )
    }
)
_limesurvey_question = Object(
    {
        "type": LiteralValue("limesurvey-question"),
        "version": LiteralValue("1.0.0"),
        "questionRelevanceExpression": String().optional(),
        "questionAndGroupRelevanceExpression": String().optional(),
        "dateTimeFormat": String().optional(),
        "nativeValidation": _native_validation.optional(),
        "unconvertedAttributes": Record(json_primitive_schema).optional(),
    }
)
_limesurvey_group = Object(
    {
        "type": LiteralValue("limesurvey-group"),
        "version": LiteralValue("1.0.0"),
        "groupRelevanceExpression": String().optional(),
    }
)
_limesurvey_survey = Object(
    {
        "type": LiteralValue("limesurvey-survey"),
        "version": LiteralValue("1.0.0"),
        "databaseSchemaVersion": String().optional(),
    }
)
_redcap_question = Object(
    {
        "type": LiteralValue("redcap-question"),
        "version": LiteralValue("1.0.0"),
        "identifier": Boolean().optional(),
        "customAlignment": String().optional(),
        "sectionHeader": String().optional(),
        "requiredField": String().optional(),
        "validationType": String().optional(),
        "validationMin": String().optional(),
        "validationMax": String().optional(),
        "branchingLogic": String().optional(),
        "questionNumber": String().optional(),
        "fieldAnnotation": String().optional(),
        "nativeMetadata": Record(String()).optional(),
    }
)
_redcap_survey = Object(
    {
        "type": LiteralValue("redcap-survey"),
        "version": LiteralValue("1.0.0"),
        "targetCollectionMode": Enum("survey", "data-entry", "unknown").optional(),
    }
)
field_source_schema = Object(
    {
        "platform": platform_schema,
        "surveyId": String().optional(),
        "groupId": String().optional(),
        "questionId": String().optional(),
        "nativeType": String().optional(),
        "responseAliases": Array(
            Object(
                {
                    "responseItemCode": String().min(1).optional(),
                    "aliases": Array(String().min(1)).min(1),
                }
            )
        ).optional(),
        "originDetails": Array(
            DiscriminatedUnion("type", [_limesurvey_question, _redcap_question])
        ).optional(),
    }
)
group_source_schema = Object(
    {
        "platform": platform_schema,
        "groupId": String().optional(),
        "originDetails": Array(DiscriminatedUnion("type", [_limesurvey_group])).optional(),
    }
)
survey_source_schema = Object(
    {
        "platform": platform_schema,
        "format": String().optional(),
        "version": String().optional(),
        "importedAt": String().datetime_with_offset().optional(),
        "originDetails": Array(
            DiscriminatedUnion("type", [_limesurvey_survey, _redcap_survey])
        ).optional(),
    }
)

# Fields
_FIELD_TYPES = (
    "short-text",
    "long-text",
    "number",
    "date",
    "yes-no",
    "gender",
    "single-choice",
    "list-with-comment",
    "multiple-choice",
    "multiple-choice-with-comments",
    "matrix",
    "multiple-input",
    "ranking",
    "display",
    "boolean",
    "range",
    "custom",
)
_field_base = Object(
    {
        "id": String().min(1),
        "code": code_schema,
        "type": Enum(*_FIELD_TYPES),
        "label": String(),
        "groupId": String().optional(),
        "parentId": String().optional(),
        "help": String().optional(),
        "images": Array(Object({"url": String().url(), "alt": String()})).optional(),
        "required": Boolean().optional(),
        "grading": grading_schema.optional(),
        "order": Number().int().nonnegative().optional(),
        "responseValidation": response_validation_schema.optional(),
        "visibility": visibility_schema.optional(),
        "rendering": rendering_schema.optional(),
        "responseEncoding": response_encoding_schema.optional(),
        "source": field_source_schema.optional(),
    }
)
field_schema: Schema = Lazy(
    lambda: Union(
        _field_base.extend(
            {
                "type": Enum("yes-no", "gender", "single-choice", "list-with-comment"),
                "options": Array(option_schema),
                "commentResponseKey": code_schema.optional(),
                "defaultValue": String().optional(),
                "other": other_response_schema.optional(),
            }
        ),
        _field_base.extend(
            {
                "type": Enum("multiple-choice", "multiple-choice-with-comments", "ranking"),
                "options": Array(option_schema),
                "defaultValue": Array(String()).optional(),
                "other": other_response_schema.optional(),
            }
        ),
        _field_base.extend(
            {
                "type": LiteralValue("matrix"),
                "matrix": basic_matrix_schema.extend({"mode": LiteralValue("single")}),
                "defaultValue": Record(String()).optional(),
            }
        ),
        _field_base.extend(
            {
                "type": LiteralValue("matrix"),
                "matrix": basic_matrix_schema.extend({"mode": LiteralValue("multiple")}),
                "defaultValue": Record(Record(Boolean())).optional(),
            }
        ),
        _field_base.extend(
            {
                "type": LiteralValue("matrix"),
                "matrix": basic_matrix_schema.extend({"mode": LiteralValue("text")}),
                "defaultValue": Record(Record(String())).optional(),
            }
        ),
        _field_base.extend(
            {
                "type": LiteralValue("matrix"),
                "matrix": number_matrix_schema,
                "defaultValue": Record(Record(Number().finite())).optional(),
            }
        ),
        _field_base.extend(
            {
                "type": LiteralValue("matrix"),
                "matrix": dual_matrix_schema,
                "defaultValue": Record(Record(String())).optional(),
            }
        ),
        _field_base.extend(
            {
                "type": LiteralValue("multiple-input"),
                "subquestions": Array(subquestion_schema),
                "defaultValue": Record(json_scalar_schema).optional(),
            }
        ),
        _field_base.extend(
            {"type": Enum("short-text", "long-text"), "defaultValue": String().optional()}
        ),
        _field_base.extend(
            {
                "type": Enum("number", "range"),
                "responseValueType": Enum("number", "text").optional(),
                "defaultValue": Union(Number().finite(), String()).optional(),
            }
        ),
        _field_base.extend(
            {
                "type": LiteralValue("date"),
                "dateValueType": Enum(
                    "date", "month-year", "month-day", "date-time", "time", "year"
                ),
                "defaultValue": String().optional(),
            }
        ),
        _field_base.extend({"type": LiteralValue("boolean"), "defaultValue": Boolean().optional()}),
        _field_base.extend({"type": LiteralValue("display")}),
        Lazy(
            lambda: _field_base.extend(
                {
                    "type": LiteralValue("custom"),
                    "childrenFields": Array(field_schema).min(1),
                }
            )
        ),
    ).super_refine(validate_field_rules)
)

# Survey
group_schema = Object(
    {
        "id": String().min(1),
        "title": String().optional(),
        "description": String().optional(),
        "order": Number().int().nonnegative(),
        "randomizationGroup": String().min(1).optional(),
        "visibility": visibility_schema.optional(),
        "source": group_source_schema.optional(),
        "navigation": Array(
            Object(
                {
                    "condition": condition_schema,
                    "destination": Union(
                        Object({"action": Enum("next", "end", "start")}),
                        Object({"groupId": String().min(1)}),
                    ),
                }
            )
        ).optional(),
    }
)
settings_schema = Object(
    {
        "layout": Enum("all", "group", "question").optional(),
        "showWelcome": Boolean().optional(),
        "showProgress": Boolean().optional(),
        "allowPrevious": Boolean().optional(),
        "showGroupName": Boolean().optional(),
        "showGroupDescription": Boolean().optional(),
        "questionIndex": Enum("inherit", "disabled", "incremental", "full").optional(),
        "navigationDelay": Number().nonnegative().optional(),
        "welcomeText": String().optional(),
        "endText": String().optional(),
        "policyNotice": String().optional(),
    }
)
survey_structure_schema = Object(
    {
        "surveyStructureVersion": LiteralValue(SURVEY_STRUCTURE_VERSION),
        "id": String().min(1),
        "title": String().optional(),
        "description": String().optional(),
        "language": language_schema.optional(),
        "availableLanguages": Array(language_schema).optional(),
        "groups": Array(group_schema).optional(),
        "fields": Array(field_schema),
        "settings": settings_schema.optional(),
        "source": survey_source_schema.optional(),
    }
).super_refine(validate_survey_invariants)

# Load result
_issue_base = Object(
    {
        "level": Enum("warning", "error"),
        "message": String().min(1),
        "fieldId": String().optional(),
        "questionCode": String().optional(),
    }
)
survey_structure_issue_schema = DiscriminatedUnion(
    "code",
    [
        _issue_base.extend(
            {
                "code": Enum(
                    "UNCONVERTED_SOURCE_PROPERTY",
                    "UNSUPPORTED_TIMER_SETTING",
                    "UNSUPPORTED_LOCATION_SETTING",
                ),
                "details": Object({"propertyName": String(), "sourceValue": String()}),
            }
        ),
        _issue_base.extend(
            {
                "code": LiteralValue("UNSUPPORTED_TYPE"),
                "details": Object({"sourceType": String()}),
            }
        ),
        _issue_base.extend(
            {
                "code": Enum(
                    "INVALID_EXPRESSION",
                    "MISSING_CONDITION_REFERENCE",
                    "UNSUPPORTED_SOURCE_EXPRESSION",
                    "SOURCE_SCRIPT_NOT_EXECUTED",
                ),
                "details": Object(
                    {
                        "sourceExpression": String(),
                        "rule": String().optional(),
                        "scope": Enum("survey", "group", "field").optional(),
                        "rowCode": String().optional(),
                        "childQuestionId": String().optional(),
                    }
                ),
            }
        ),
        _issue_base.extend(
            {
                "code": LiteralValue("UNSUPPORTED_SOURCE_VERSION"),
                "details": Object({"sourceVersion": String()}),
            }
        ),
        _issue_base.extend(
            {
                "code": Enum("INVALID_VALIDATION", "UNSUPPORTED_TIMER"),
                "details": Object(
                    {
                        "rule": String(),
                        "sourceValue": Union(
                            String(), Number().finite(), Boolean(), Null()
                        ).optional(),
                    }
                ),
            }
        ),
        _issue_base.extend(
            {
                "code": LiteralValue("EMPTY_OPTIONS"),
                "details": Object(
                    {
                        "omitted": Boolean(),
                        "rows": Number().int().nonnegative().optional(),
                        "columns": Number().int().nonnegative().optional(),
                    }
                ).optional(),
            }
        ),
        _issue_base.extend(
            {
                "code": Enum(
                    "INVALID_SOURCE",
                    "MISSING_QUESTION_CODE",
                    "DUPLICATE_QUESTION_CODE",
                    "MISSING_PARENT",
                ),
            }
        ),
    ],
)
response_state_schema = Object(
    {
        "active": Boolean(),
        "canSaveResponses": Boolean(),
        "submitMode": Enum("submit", "submit_preview"),
        "language": String().optional(),
        "endText": String().optional(),
        "warningCodes": Array(String()),
        "didNotSaveCode": Nullable(String()),
    }
)
_count = Number().int().nonnegative()
source_metrics_schema = Object(
    {
        "topLevelQuestions": _count,
        "childQuestions": _count,
        "integratedChildren": _count,
        "detectedTypes": Array(String()),
        "conditionsDetected": _count,
        "validationQuestions": _count,
    }
).refine(
    lambda value: value["integratedChildren"] <= value["childQuestions"],
    "Integrated children cannot exceed source children.",
    path=["integratedChildren"],
)
survey_load_result_schema = Object(
    {
        "survey": survey_structure_schema,
        "issues": Array(survey_structure_issue_schema),
        "responseState": response_state_schema.optional(),
        "sourceMetrics": source_metrics_schema.optional(),
    }
)
survey_response_record_schema = Record(json_value_schema)
