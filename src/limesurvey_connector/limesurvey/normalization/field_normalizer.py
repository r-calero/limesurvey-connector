"""Convert one LimeSurvey question, its options and field rules into SurveyStructure."""

import re
from typing import Any

from .condition_references import (
    ConditionReferenceIndex,
    UnsupportedConditionError,
    resolve_reference,
)
from .field_values import (
    _date_order,
    _date_value_type,
    _default_value,
    _localized_fixed_labels,
    _native_validation,
    _normalize_answer_count_validation,
    _options,
    _validation,
    _validation_number,
)
from .response_encoding import selection_encoding
from .row_filters import apply_exclusive_options, apply_matrix_filters
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
from .text_sanitizer import question_images
from .unconverted_field_rules import report_unconverted_field_rules
from .validation_pattern import portable_text_pattern
from .visibility_normalizer import normalize_field_visibility, report_child_relevance

QUESTION_TYPES = {
    "S": "short-text",
    "T": "long-text",
    "U": "long-text",
    "5": "single-choice",
    "D": "date",
    "Y": "yes-no",
    "G": "gender",
    "L": "single-choice",
    "!": "single-choice",
    "O": "list-with-comment",
    "M": "multiple-choice",
    "P": "multiple-choice-with-comments",
    "N": "number",
    "F": "matrix",
    ":": "matrix",
    "1": "matrix",
    "H": "matrix",
    "E": "matrix",
    "B": "matrix",
    "A": "matrix",
    "C": "matrix",
    ";": "matrix",
    "Q": "multiple-input",
    "K": "multiple-input",
    "R": "ranking",
    "X": "display",
}


def normalize_field(
    question: dict[str, Any],
    children: list[dict[str, Any]],
    survey_id: str,
    language: str,
    issues: list[dict[str, Any]],
    condition_references: dict[str, tuple[str, str | None]],
    remote_url: str = "",
) -> dict[str, Any] | None:
    original_type = _text(question.get("type")).strip()
    field_type = QUESTION_TYPES.get(original_type)
    qid = _text(question.get("qid")).strip()
    code = _text(question.get("title")).strip()
    if not field_type:
        issues.append(
            _issue(
                "warning",
                "UNSUPPORTED_TYPE",
                f"LimeSurvey question type {original_type or '(missing)'} is not supported and was skipped.",
                field_id=qid,
                question_code=code,
                details={"sourceType": original_type},
            )
        )
        return None

    result = _record(question.get("result"))
    attributes = _record(result.get("attributes") or question.get("attributes"))
    native_validation = _native_validation(attributes)
    original_pattern = _text(result.get("preg", question.get("preg")))
    if original_pattern.strip():
        native_validation = {**(native_validation or {}), "regularExpression": original_pattern}
    localized = _localized_fixed_labels(language)
    label = _clean_html(question.get("question") or result.get("question") or "")
    images = question_images(question.get("question") or result.get("question") or "", remote_url)
    help_text = _clean_html(question.get("help") or result.get("help") or "")
    options = _options(result.get("answeroptions") or question.get("answeroptions"))
    # Pair each option with its own source row, even when scales interleave by order.
    children = sorted(children, key=lambda item: _number(item.get("question_order"), 0))
    report_child_relevance(
        [
            child
            for child in children
            if field_type not in {"matrix", "multiple-choice", "multiple-choice-with-comments"}
            or (field_type == "matrix" and _text(child.get("scale_id") or "0") != "0")
        ],
        issues,
        qid,
        code,
    )
    child_options = [
        {
            "code": _text(child.get("title")).strip() or f"SQ{index + 1:03d}",
            "label": _clean_html(
                child.get("question")
                or _record(child.get("result")).get("question")
                or child.get("title")
            ),
            "order": index,
        }
        for index, child in enumerate(children)
    ]
    subquestions = [
        {
            "id": _text(child.get("qid")).strip() or None,
            "code": option["code"],
            "label": option["label"],
            "order": option["order"],
        }
        for child, option in zip(children, child_options, strict=True)
    ]

    if original_type in {"M", "P"}:
        for child, option in zip(children, child_options, strict=False):
            visibility = normalize_field_visibility(
                {"relevance": child.get("relevance")},
                condition_references,
                issues,
                qid,
                code,
                row_code=str(option["code"]),
                child_question_id=_text(child.get("qid")),
            )
            if visibility:
                option["visibility"] = visibility
    if original_type == "5":
        options = [
            {"code": str(value), "label": str(value), "order": value - 1} for value in range(1, 6)
        ]
    elif original_type in {"M", "P"} or (original_type == "R" and not options):
        options = child_options
    elif original_type == "Y":
        options = [
            {"code": "Y", "label": localized["yes"], "order": 0},
            {"code": "N", "label": localized["no"], "order": 1},
        ]
    elif original_type == "G" and not options:
        options = [
            {"code": "F", "label": localized["female"], "order": 0},
            {"code": "M", "label": localized["male"], "order": 1},
        ]

    field: dict[str, Any] = {
        "id": qid or code,
        "code": code,
        "type": field_type,
        "label": label,
        "required": _yes(question.get("mandatory")),
        "order": _number(question.get("question_order"), 0),
        "source": _compact(
            {
                "platform": "limesurvey",
                "surveyId": survey_id,
                "groupId": _text(question.get("gid")).strip() or None,
                "questionId": qid or None,
                "nativeType": original_type,
                "originDetails": (
                    [
                        _compact(
                            {
                                "type": "limesurvey-question",
                                "version": "1.0.0",
                                "questionRelevanceExpression": _text(
                                    question.get("relevance")
                                ).strip()
                                or None,
                                "questionAndGroupRelevanceExpression": _text(
                                    question.get("full_condition")
                                ).strip()
                                or None,
                                "dateTimeFormat": _text(attributes.get("date_time_format")).strip()
                                or None,
                                "nativeValidation": native_validation,
                            }
                        )
                    ]
                    if any(
                        question.get(key) not in {None, ""}
                        for key in ("relevance", "full_condition")
                    )
                    or attributes.get("date_time_format") not in {None, ""}
                    or native_validation
                    else None
                ),
            }
        ),
    }
    if original_type == "5":
        presentation = _text(attributes.get("slider_rating", "0")).strip()
        field["rendering"] = {
            "widget": {"0": "radio-group", "1": "rating", "2": "emoticon-slider"}.get(
                presentation, "radio-group"
            )
        }
    elif original_type in {"Y", "G"}:
        presentation = _text(attributes.get("display_type", "0")).strip()
        field["rendering"] = {"widget": "radio-group" if presentation == "1" else "button-group"}
    if _yes(attributes.get("hidden")):
        field.setdefault("rendering", {})["hidden"] = True
    if _text(attributes.get("random_group")).strip():
        field.setdefault("rendering", {})["randomizationGroup"] = _text(
            attributes["random_group"]
        ).strip()
    if images:
        field["images"] = images
    if field_type == "date":
        field["dateValueType"] = _date_value_type(attributes.get("date_time_format"))
        date_order = _date_order(attributes.get("date_time_format"))
        if date_order:
            field.setdefault("rendering", {})["dateOrder"] = date_order
        if field["dateValueType"] in {"date", "month-day", "year", "month-year"} and (
            _yes(attributes.get("dropdown_dates")) or "dropdown_dates_month_style" in attributes
        ):
            rendering = field.setdefault("rendering", {})
            rendering["dateDropdowns"] = True
            style = _text(attributes.get("dropdown_dates_month_style", "1"))
            if style in {"0", "1", "2"}:
                rendering["monthLabelStyle"] = {"0": "short", "1": "long", "2": "numeric"}[style]
            rendering["reverseYearOrder"] = _yes(attributes.get("reverse"))
            for source, target in (
                ("dropdown_dates_year_min", "yearMin"),
                ("dropdown_dates_year_max", "yearMax"),
            ):
                limit = _optional_number(attributes.get(source))
                if limit is not None and limit == int(limit) and 1 <= limit <= 9999:
                    rendering[target] = int(limit)
    group_id = _text(question.get("gid")).strip()
    parent_id = _text(question.get("parent_qid")).strip()
    if group_id:
        field["groupId"] = group_id
    if parent_id and parent_id != "0":
        field["parentId"] = parent_id
    if help_text:
        field["help"] = help_text
    default_value = _default_value(
        field_type,
        result.get("defaultvalue", question.get("defaultvalue")),
    )
    if default_value is not None:
        field["defaultValue"] = default_value
    visibility = normalize_field_visibility(question, condition_references, issues, qid, code)
    if visibility:
        field["visibility"] = visibility
    validation = _validation(attributes, field_type, issues, qid, code, original_type)
    if field_type == "date" and field.get("dateValueType") not in {"date", "date-time"}:
        # Calendar bounds cannot constrain a time-only, year or month-year field.
        validation.pop("dateMin", None)
        validation.pop("dateMax", None)
    if original_type == "K":
        # K has one numeric text box per subquestion. Keep its response keys and
        # original text; the neutral renderer and server both check numericText.
        validation["numericText"] = True
        for source_rule, target in (
            ("min_num_value_n", "itemMin"),
            ("max_num_value_n", "itemMax"),
            ("min_num_value", "sumMin"),
            ("max_num_value", "sumMax"),
            ("equals_num_value", "sumEquals"),
        ):
            raw_bound = _text(attributes.get(source_rule)).strip()
            fixed = _optional_number(raw_bound)
            if fixed is not None:
                validation[target] = fixed
            elif raw_bound and isinstance(condition_references, ConditionReferenceIndex):
                direct = re.fullmatch(r"\{?([A-Za-z][A-Za-z0-9_]*)(?:\.NAOK)?\}?", raw_bound, re.I)
                if direct:
                    try:
                        bound_code, item_code = resolve_reference(
                            direct.group(1), condition_references
                        )
                        bound_question = condition_references.questions.get(bound_code, {})
                        if (
                            item_code is None
                            and bound_code != code
                            and bound_question.get("type") == "N"
                        ):
                            validation[f"{target}Reference"] = bound_code
                    except UnsupportedConditionError:
                        pass
        for minimum, maximum in (("itemMin", "itemMax"), ("sumMin", "sumMax")):
            if (
                minimum in validation
                and maximum in validation
                and validation[minimum] > validation[maximum]
            ):
                validation.pop(minimum)
                validation.pop(maximum)
        if "sumEquals" in validation and (
            validation["sumEquals"] < validation.get("sumMin", float("-inf"))
            or validation["sumEquals"] > validation.get("sumMax", float("inf"))
        ):
            validation.pop("sumEquals")
        if _yes(attributes.get("num_value_int_only")):
            validation["integer"] = True
        if _text(attributes.get("value_range_allows_missing")).strip().upper() in {"N", "0"}:
            validation["sumAllowsMissing"] = False
    if field_type in {"short-text", "long-text"} and original_pattern:
        validation.update(portable_text_pattern(original_pattern) or {})
    if original_type == "N" and original_pattern:
        portable_pattern = portable_text_pattern(original_pattern)
        if portable_pattern:
            field["responseValueType"] = "text"
            validation.update(portable_pattern)
            original_default = result.get("defaultvalue", question.get("defaultvalue"))
            if original_default is not None and _text(original_default) != "":
                field["defaultValue"] = _text(original_default)
    if validation:
        field["responseValidation"] = validation
    if _yes(question.get("other")):
        field["other"] = {
            "code": "-oth-",
            "label": localized["other"],
            # LimeSurvey's own column names (limesurvey-column-names): Q_other, not Qother.
            "textResponseKey": f"{code}_other",
        }
        if original_type == "P":
            field["other"]["commentResponseKey"] = f"{code}_othercomment"
        if field["required"] and _yes(attributes.get("other_comment_mandatory")):
            if original_type == "P":
                field["other"]["commentRequired"] = True
            elif original_type in {"L", "!"}:
                field["other"]["textRequired"] = True
    if original_type in {"M", "P"}:
        field["responseEncoding"] = selection_encoding("Y", "N", localized)

    if original_type == "O":
        field["commentResponseKey"] = f"{code}_comment"
    if original_type == "P":
        for option in options:
            option["commentResponseKey"] = f"{code}_{option['code']}comment"
    if field_type in {
        "yes-no",
        "gender",
        "single-choice",
        "list-with-comment",
        "multiple-choice",
        "multiple-choice-with-comments",
        "ranking",
    }:
        field["options"] = options
        if field_type == "ranking":
            field["source"]["responseAliases"] = [
                {
                    "responseItemCode": str(index + 1),
                    "aliases": [f"{code}{index + 1}", f"{label} [Rank {index + 1}]"]
                    + ([f"{survey_id}X{group_id}X{qid}{index + 1}"] if group_id else []),
                }
                for index in range(len(options))
            ]
        if not options:
            issues.append(
                _issue(
                    "warning",
                    "EMPTY_OPTIONS",
                    f"Question {code} has no answer options."
                    + (
                        " Only its Other response remains usable."
                        if field.get("other")
                        else " It was omitted because it has no usable input."
                    ),
                    field_id=qid,
                    question_code=code,
                    details={"omitted": not bool(field.get("other"))},
                )
            )
            if not field.get("other"):
                return None
    elif field_type == "multiple-input":
        field["subquestions"] = subquestions
        if not subquestions:
            issues.append(
                _issue(
                    "warning",
                    "EMPTY_OPTIONS",
                    f"Question {code} was omitted because it has no usable subquestions.",
                    field_id=qid,
                    question_code=code,
                    details={"omitted": True},
                )
            )
            return None
    elif field_type == "matrix":
        rows = [
            option
            for child, option in zip(children, child_options, strict=True)
            if _text(child.get("scale_id") or "0") == "0"
        ]
        for child, row in (
            (child, option)
            for child, option in zip(children, child_options, strict=False)
            if _text(child.get("scale_id") or "0") == "0"
        ):
            visibility = normalize_field_visibility(
                {"relevance": child.get("relevance")},
                condition_references,
                issues,
                qid,
                code,
                row_code=str(row["code"]),
                child_question_id=_text(child.get("qid")),
            )
            if visibility:
                row["visibility"] = visibility
        columns_from_children = [
            option
            for child, option in zip(children, child_options, strict=True)
            if _text(child.get("scale_id")) == "1"
        ]
        if original_type in {"A", "B"}:
            columns = [
                {"code": str(value), "label": str(value), "order": value - 1}
                for value in range(1, 6 if original_type == "A" else 11)
            ]
        elif original_type == "C":
            columns = [
                {"code": code, "label": localized[label], "order": order}
                for order, (code, label) in enumerate(
                    (("Y", "yes"), ("U", "uncertain"), ("N", "no"))
                )
            ]
        elif original_type == "E":
            columns = [
                {"code": value, "label": localized[label], "order": order}
                for order, (value, label) in enumerate(
                    (("I", "increase"), ("S", "same"), ("D", "decrease"))
                )
            ]
        elif original_type in {";", ":"}:
            columns = columns_from_children
        elif original_type == "E":
            columns = [
                {"code": value, "label": localized[label], "order": index}
                for index, (value, label) in enumerate(
                    (("I", "increase"), ("S", "same"), ("D", "decrease"))
                )
            ]
        elif original_type == "1":
            scales = _dual_scales(result, question)
            columns = [
                {
                    "code": str(scale),
                    "label": _clean_html(
                        attributes.get("dualscale_headerA" if scale == 0 else "dualscale_headerB")
                        or f"{'Escala' if language.startswith('es') else 'Scale'} {scale + 1}"
                    ),
                    "order": scale,
                    "options": _options(_record(scales).get(str(scale))),
                }
                for scale in (0, 1)
            ]
            if any(not column["options"] for column in columns):
                issues.append(
                    _issue(
                        "warning",
                        "UNSUPPORTED_TYPE",
                        "Dual-scale question omitted: both scales must have separate answer options. "
                        "LimeSurvey versions that key answer options only by code return a single scale "
                        "when both scales share codes; import the .lss file to keep this question.",
                        field_id=qid,
                        question_code=code,
                        details={"sourceType": original_type},
                    )
                )
                return None
        else:
            columns = options
        field["matrix"] = {
            "mode": {";": "text", ":": "number", "1": "dual-single"}.get(original_type, "single"),
            "rows": rows,
            "columns": columns,
        }
        if not rows or not columns:
            issues.append(
                _issue(
                    "warning",
                    "EMPTY_OPTIONS",
                    f"Matrix question {code} was omitted because it has no usable rows or columns.",
                    field_id=qid,
                    question_code=code,
                    details={"omitted": True, "rows": len(rows), "columns": len(columns)},
                )
            )
            return None
        for collection in (field["matrix"]["rows"], field["matrix"]["columns"]):
            for order, option in enumerate(collection):
                option["order"] = order
        if original_type == "1":
            field["source"]["responseAliases"] = [
                {
                    "responseItemCode": f"{row['code']}_{column['code']}",
                    "aliases": [f"{code}_{row['code']}#{column['code']}"]
                    + (
                        [f"{survey_id}X{question['gid']}X{qid}{row['code']}#{column['code']}"]
                        if question.get("gid")
                        else []
                    )
                    + (
                        [f"{label} [{row['label']}][Scale {int(str(column['code'])) + 1}]"]
                        if language.startswith("en")
                        else []
                    ),
                }
                for row in field["matrix"]["rows"]
                for column in columns
            ]
        if original_type == ":" and _yes(attributes.get("multiflexible_checkbox")):
            field["matrix"]["mode"] = "multiple"
            field["responseEncoding"] = selection_encoding("1", "0", localized)
        elif original_type == ":":
            for native, neutral in (("multiflexible_min", "min"), ("multiflexible_max", "max")):
                limit = _validation_number(attributes.get(native), native, issues, qid, code)
                if limit is not None:
                    field.setdefault("responseValidation", {})[neutral] = limit
            step = attributes.get("multiflexible_step")
            if step is not None and _text(step).strip() not in {"", "1"}:
                issues.append(
                    _issue(
                        "warning",
                        "INVALID_VALIDATION",
                        "Numeric matrix cell increments are preserved in the source but are not enforced by the portable renderer.",
                        field_id=qid,
                        question_code=code,
                        details={"rule": "multiflexible_step", "sourceValue": step},
                    )
                )
    _normalize_answer_count_validation(field, attributes, issues, qid, code)
    converted_rules = apply_matrix_filters(
        field, attributes, condition_references
    ) | apply_exclusive_options(field, attributes)
    if original_type in {"Y", "G"} and _text(attributes.get("display_type", "0")).strip() in {
        "0",
        "1",
    }:
        converted_rules.add("display_type")
    if original_type == "5" and _text(attributes.get("slider_rating", "0")).strip() in {
        "0",
        "1",
        "2",
    }:
        converted_rules.add("slider_rating")
    if field.get("rendering", {}).get("randomizationGroup"):
        converted_rules.add("random_group")
    if field.get("rendering", {}).get("dateDropdowns"):
        converted_rules.update({"dropdown_dates_month_style", "reverse"})
    unconverted_attributes = report_unconverted_field_rules(
        field, question, attributes, issues, converted_rules
    )
    if unconverted_attributes:
        extensions = field["source"].setdefault("originDetails", [])
        if not extensions:
            extensions.append({"type": "limesurvey-question", "version": "1.0.0"})
        extensions[0]["unconvertedAttributes"] = unconverted_attributes
    return _compact(field)


def _dual_scales(result: dict[str, Any], question: dict[str, Any]) -> Any:
    """Answer options of a dual-scale question, keyed by scale id.

    RemoteControl returns them as answeroptions_multiscale (current LimeSurvey) at the
    question level, or as answeroptions keyed by code with a scale_id per option.
    """
    multiscale = result.get("answeroptions_multiscale") or question.get("answeroptions_multiscale")
    if multiscale:
        return (
            {str(index): scale for index, scale in enumerate(multiscale)}
            if isinstance(multiscale, list)
            else multiscale
        )
    options = result.get("answeroptions") or question.get("answeroptions") or {}
    if isinstance(options, list):
        return {str(index): scale for index, scale in enumerate(options)}
    rows = _record(options)
    if rows and all(isinstance(row, dict) and "scale_id" in row for row in rows.values()):
        grouped: dict[str, dict[str, Any]] = {}
        for code, row in rows.items():
            grouped.setdefault(_text(row.get("scale_id")), {})[code] = row
        return grouped
    return rows
