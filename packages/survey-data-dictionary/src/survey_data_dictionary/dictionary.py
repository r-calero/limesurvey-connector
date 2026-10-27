"""Build a data dictionary from a SurveyStructure (port of ``dictionary.ts``)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from survey_data_dictionary.contracts import (
    DictionaryField,
    DictionaryValue,
    SurveyDictionary,
    SurveyDictionaryValidationError,
)
from survey_structure import parse_survey_structure
from survey_structure._js import keys as js_keys
from survey_structure._js import to_string, trim

Field = dict[str, Any]


def build_survey_dictionary(
    structure: Any,
    *,
    aliases: Mapping[str, str] | None = None,
    source_issues: Sequence[Mapping[str, Any]] | None = None,
    strict: bool = False,
) -> SurveyDictionary:
    """Turn a SurveyStructure into response columns, allowed values and aliases.

    The input is validated first; an invalid survey raises
    ``SurveyStructureValidationError`` instead of producing a partial dictionary.
    """
    form: dict[str, Any] = dict(parse_survey_structure(structure))
    generated: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    _visit_fields(form["fields"], "", generated, issues, set(), form.get("language"))
    fields = _remove_duplicate_response_keys(generated, issues)
    # SGQA is a LimeSurvey export address, not a generic combination of source IDs.
    if (form.get("source") or {}).get("platform") == "limesurvey":
        _add_generated_aliases(fields, _text(form["id"]))
    _add_manual_aliases(fields, aliases or {}, issues)
    for issue in source_issues or []:
        entry: dict[str, Any] = {
            "level": issue["level"],
            "code": "SOURCE_ADAPTATION_ISSUE",
            "message": issue["message"],
        }
        if issue.get("questionCode") is not None:
            entry["questionCode"] = issue["questionCode"]
        details: dict[str, Any] = {"sourceCode": issue["code"]}
        if issue.get("fieldId") is not None:
            details["fieldId"] = issue["fieldId"]
        details.update(issue.get("details") or {})
        entry["details"] = details
        issues.append(entry)

    if strict and any(issue["level"] == "error" for issue in issues):
        raise SurveyDictionaryValidationError(issues)  # type: ignore[arg-type]

    dictionary: dict[str, Any] = {
        "surveyStructureVersion": form["surveyStructureVersion"],
        "surveyId": _text(form["id"]),
    }
    for key, source in (("surveyTitle", form.get("title")), ("language", form.get("language"))):
        value = _optional_text(source)
        if value is not None:
            dictionary[key] = value
    dictionary["fields"] = fields
    dictionary["issues"] = issues
    return dictionary  # type: ignore[return-value]


def get_question_dictionary(
    dictionary: SurveyDictionary, question_code: str
) -> list[DictionaryField]:
    code = trim(_text(question_code))
    return [field for field in dictionary["fields"] if field["questionCode"] == code]


def _remove_duplicate_response_keys(
    fields: list[dict[str, Any]], issues: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    kept = []
    for field in fields:
        key = field["responseKey"]
        if key not in seen:
            seen.add(key)
            kept.append(field)
            continue
        issues.append(
            {
                "level": "error",
                "code": "DUPLICATE_RESPONSE_KEY",
                "message": f"Response key {key} is produced more than once; the duplicate dictionary entry was omitted.",
                "questionCode": field["questionCode"],
                "responseKey": key,
            }
        )
    return kept


def _visit_fields(
    source_fields: list[Field],
    parent_key: str,
    output: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    seen_codes: set[str],
    language: str | None,
) -> None:
    for field in source_fields:
        question_code = trim(_text(field["code"]))
        if not question_code:
            issues.append(
                {
                    "level": "error",
                    "code": "MISSING_QUESTION_CODE",
                    "message": f"Question {_text(field['id']) or '(without id)'} has no code and was skipped.",
                }
            )
            continue
        identity = f"{parent_key}::{question_code}" if parent_key else question_code
        if identity in seen_codes:
            issues.append(
                {
                    "level": "error",
                    "code": "DUPLICATE_QUESTION_CODE",
                    "message": f"Question code {question_code} is repeated at the same dictionary level and was skipped.",
                    "questionCode": question_code,
                }
            )
            continue
        seen_codes.add(identity)
        response_key = _join(parent_key, question_code)
        if field["type"] not in ("display", "custom"):
            _append_field_entries(field, response_key, output, issues, language)
        if field["type"] == "custom":
            _visit_fields(
                field["childrenFields"], response_key, output, issues, seen_codes, language
            )


def _append_field_entries(
    field: Field,
    response_key: str,
    output: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    language: str | None,
) -> None:
    field_type = field["type"]
    label = field["label"]
    if field_type == "matrix":
        _append_matrix_entries(field, response_key, output, issues, language)
        return

    if field_type == "ranking":
        values = _normalize_values(field["options"], field, issues)
        rank = "Posición" if (language or "").startswith("es") else "Rank"
        for index in range(len(field["options"])):
            position = index + 1
            output.append(
                _entry(
                    field,
                    _join(response_key, str(position)),
                    question_label=f"{label} — {rank} {position}",
                    data_type="code",
                    values=values,
                    parent_code=response_key,
                )
            )
        return

    if field_type == "multiple-input" and field["subquestions"]:
        for subquestion in field["subquestions"]:
            code = trim(_text(subquestion["code"]))
            if not code:
                issues.append(
                    {
                        "level": "error",
                        "code": "MISSING_OPTION_CODE",
                        "message": f"A subquestion of {field['code']} has no code and was skipped.",
                        "questionCode": field["code"],
                    }
                )
                continue
            sub_label = _text(subquestion["label"])
            output.append(
                _entry(
                    field,
                    _join(response_key, code),
                    question_label=sub_label or label,
                    data_type="string",
                    parent_code=response_key,
                    aliases=[f"{label} [{sub_label or code}]"],
                )
            )
        return

    values = _normalize_values(field.get("options"), field, issues)
    other = field.get("other")
    multiple = field_type in ("multiple-choice", "multiple-choice-with-comments")
    if not multiple and other:
        values = [*values, {"code": other["code"], "label": other["label"]}]

    if multiple and values:
        for value in values:
            item_key = _join(response_key, value["code"])
            output.append(
                _entry(
                    field,
                    item_key,
                    question_label=f"{label} — {value['label']}",
                    data_type="boolean",
                    cardinality="multiple",
                    values=_boolean_values(field, language),
                    parent_code=response_key,
                    aliases=[f"{label} [{value['label']}]"],
                )
            )
            if field_type == "multiple-choice-with-comments":
                option = next(item for item in field["options"] if item["code"] == value["code"])
                output.append(
                    _entry(
                        field,
                        option.get("commentResponseKey") or f"{item_key}_comment",
                        question_label=f"{label} — {value['label']} — {_comment(language)}",
                        data_type="string",
                        cardinality="multiple",
                        parent_code=item_key,
                        aliases=[f"{label} [{_comment(language)}]"],
                    )
                )
        if other:
            output.append(
                _entry(
                    field,
                    other["textResponseKey"],
                    question_label=f"{label} — {other['label']} — {_other_text(language)}",
                    data_type="string",
                    cardinality="multiple",
                    parent_code=response_key,
                    aliases=[
                        f"{label} [{other['label']}]",
                        f"{label} [{other['label']} {_other_text(language)}]",
                    ],
                )
            )
            if other.get("commentResponseKey"):
                output.append(
                    _entry(
                        field,
                        other["commentResponseKey"],
                        question_label=f"{label} — {other['label']} — {_comment(language)}",
                        data_type="string",
                        cardinality="multiple",
                        parent_code=other["textResponseKey"],
                        aliases=_other_comment_aliases(label, other["label"], language),
                    )
                )
        return

    if field_type == "boolean":
        entry_values: list[DictionaryValue] | None = _boolean_values(field, language)
    else:
        entry_values = values or None
    output.append(
        _entry(
            field,
            response_key,
            data_type=_scalar_data_type(field),
            cardinality="multiple" if multiple else "single",
            values=entry_values,
            aliases=[label],
        )
    )
    if field_type == "list-with-comment":
        output.append(
            _entry(
                field,
                field.get("commentResponseKey") or f"{response_key}_comment",
                question_label=f"{label} — {_comment(language)}",
                data_type="string",
                parent_code=response_key,
                aliases=[f"{label} [{_comment(language)}]"],
            )
        )
    if other:
        output.append(
            _entry(
                field,
                other["textResponseKey"],
                question_label=f"{label} — {other['label']}",
                data_type="string",
                parent_code=response_key,
                aliases=[f"{label} [{other['label']}]"],
            )
        )


def _append_matrix_entries(
    field: Field,
    response_key: str,
    output: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    language: str | None,
) -> None:
    matrix = field["matrix"]
    label = field["label"]
    rows = _normalize_axis(matrix["rows"], field, "row", issues)
    columns = _normalize_axis(matrix["columns"], field, "column", issues)
    mode = matrix["mode"]
    data_types = {"text": "string", "number": "number", "dual-single": "code"}
    for row in rows:
        row_key = _join(response_key, row["code"])
        if mode == "single":
            output.append(
                _entry(
                    field,
                    row_key,
                    question_label=f"{label} — {row['label']}",
                    data_type="code",
                    values=columns,
                    parent_code=response_key,
                    aliases=[f"{label} [{row['label']}]"],
                )
            )
            continue
        for column in columns:
            scale = (
                next((item for item in matrix["columns"] if item["code"] == column["code"]), None)
                if mode == "dual-single"
                else None
            )
            if scale is not None:
                cell_values: list[Any] | None = scale["options"]
            elif mode == "multiple":
                cell_values = _boolean_values(field, language)
            else:
                cell_values = None
            output.append(
                _entry(
                    field,
                    _join(row_key, column["code"]),
                    question_label=f"{label} — {row['label']} — {column['label']}",
                    data_type=data_types.get(mode, "boolean"),
                    cardinality="multiple" if mode == "multiple" else "single",
                    values=cell_values,
                    parent_code=row_key,
                    aliases=[
                        f"{label} [{row['label']}] [{column['label']}]",
                        f"{label} [{row['label']}][{column['label']}]",
                    ],
                )
            )


def _normalize_values(
    options: list[dict[str, Any]] | None, field: Field, issues: list[dict[str, Any]]
) -> list[DictionaryValue]:
    values: list[DictionaryValue] = []
    for option in options or []:
        code = trim(_text(option["code"]))
        if not code:
            issues.append(
                {
                    "level": "error",
                    "code": "MISSING_OPTION_CODE",
                    "message": f"An option of {field['code']} has no code and was skipped.",
                    "questionCode": field["code"],
                }
            )
            continue
        values.append({"code": code, "label": _text(option["label"]) or code})
    return values


def _normalize_axis(
    options: list[dict[str, Any]], field: Field, axis: str, issues: list[dict[str, Any]]
) -> list[DictionaryValue]:
    values: list[DictionaryValue] = []
    for option in options:
        code = trim(_text(option["code"]))
        if not code:
            issues.append(
                {
                    "level": "error",
                    "code": "MISSING_MATRIX_ROW_CODE"
                    if axis == "row"
                    else "MISSING_MATRIX_COLUMN_CODE",
                    "message": f"A matrix {axis} of {field['code']} has no code and was skipped.",
                    "questionCode": field["code"],
                }
            )
            continue
        values.append({"code": code, "label": _text(option["label"]) or code})
    return values


def _entry(
    field: Field,
    response_key: str,
    *,
    question_label: str | None = None,
    data_type: str | None = None,
    cardinality: str = "single",
    values: list[Any] | None = None,
    parent_code: str | None = None,
    aliases: list[str] | None = None,
) -> dict[str, Any]:
    source_aliases = [
        alias
        for item in (field.get("source") or {}).get("responseAliases", [])
        if _alias_targets(field, item, response_key)
        for alias in item["aliases"]
    ]
    entry: dict[str, Any] = {
        "questionCode": field["code"],
        "questionLabel": field["label"] if question_label is None else question_label,
        "responseKey": response_key,
        "dataType": data_type or _scalar_data_type(field),
        "cardinality": cardinality,
    }
    if values is not None:
        entry["values"] = values
    entry["aliases"] = _unique_texts([*(aliases or []), *source_aliases])
    if parent_code is not None:
        entry["parentCode"] = parent_code
    for key, value in (
        ("qid", _optional_text((field.get("source") or {}).get("questionId"))),
        ("groupId", _optional_text(field.get("groupId"))),
    ):
        if value is not None:
            entry[key] = value
    return entry


def _alias_targets(field: Field, item: Mapping[str, Any], response_key: str) -> bool:
    item_code = item.get("responseItemCode")
    key = field["code"] if item_code is None else f"{field['code']}_{item_code}"
    return response_key == key or response_key.endswith(f"_{key}")


def _scalar_data_type(field: Field) -> str:
    """Numbers kept as text stay strings, so leading zeroes survive."""
    if field["type"] == "number" and field.get("responseValueType") == "text":
        return "string"
    return _data_type(field["type"])


def _add_generated_aliases(fields: list[dict[str, Any]], survey_id: str) -> None:
    for field in fields:
        aliases = list(dict.fromkeys(field.get("aliases", [])))
        sgqa = _sgqa_alias(field, survey_id)
        if sgqa and sgqa not in aliases:
            aliases.append(sgqa)
        if aliases:
            field["aliases"] = aliases
        else:
            field.pop("aliases", None)


def _add_manual_aliases(
    fields: list[dict[str, Any]], aliases: Mapping[str, str], issues: list[dict[str, Any]]
) -> None:
    by_key = {field["responseKey"]: field for field in fields}
    for alias in js_keys(dict(aliases)):
        response_key = aliases[alias]
        normalized = trim(alias)
        field = by_key.get(trim(response_key))
        if not normalized or field is None:
            issues.append(
                {
                    "level": "warning",
                    "code": "UNKNOWN_RESPONSE_ALIAS",
                    "message": f"Alias {normalized or '(empty)'} points to unknown response key {response_key}.",
                    "responseKey": response_key,
                }
            )
            continue
        field["aliases"] = _unique_texts([*field.get("aliases", []), normalized])


def _sgqa_alias(field: dict[str, Any], survey_id: str) -> str | None:
    group_id, qid = field.get("groupId"), field.get("qid")
    if not survey_id or not group_id or not qid:
        return None
    base = f"{survey_id}X{group_id}X{qid}"
    if field["responseKey"] == field["questionCode"]:
        return base
    marker = f"{field['questionCode']}_"
    marker_index = field["responseKey"].rfind(marker)
    if marker_index < 0:
        return None
    suffix = field["responseKey"][marker_index + len(marker) :]
    if not suffix:
        return base
    first, *rest = suffix.split("_")
    return f"{base}{first}{'_' + '_'.join(rest) if rest else ''}"


def _unique_texts(values: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in (trim(value) for value in values) if item))


def _data_type(field_type: str) -> str:
    if field_type in ("number", "range"):
        return "number"
    if field_type == "date":
        return "date"
    if field_type == "boolean":
        return "boolean"
    if field_type in ("yes-no", "gender", "single-choice", "list-with-comment", "ranking"):
        return "code"
    return "string"


def _is_spanish(language: str | None) -> bool:
    return trim(language or "").lower().startswith("es")


def _boolean_values(field: Field, language: str | None) -> list[DictionaryValue]:
    encoding = field.get("responseEncoding") or {}
    selected = encoding["selectedValue"] if encoding.get("selectedValue") is not None else True
    unselected = (
        encoding["unselectedValue"] if encoding.get("unselectedValue") is not None else False
    )
    spanish = _is_spanish(language)
    return [
        {
            "code": _text(selected),
            "label": encoding.get("selectedLabel", "Sí" if spanish else "Yes"),
        },
        {"code": _text(unselected), "label": encoding.get("unselectedLabel", "No")},
    ]


def _comment(language: str | None) -> str:
    return "Comentario" if _is_spanish(language) else "Comment"


def _other_text(language: str | None) -> str:
    return "Texto" if _is_spanish(language) else "Text"


def _other_comment_aliases(
    question_label: str, other_label: str, language: str | None
) -> list[str]:
    comment = _comment(language)
    return _unique_texts(
        [
            f"{question_label} [{other_label} {comment}]",
            f"{question_label} [{other_label} {comment.lower()}]",
        ]
    )


def _join(parent: str, child: str) -> str:
    return "_".join(part for part in (parent, child) if part)


def _text(value: object) -> str:
    return "" if value is None else to_string(value)


def _optional_text(value: object) -> str | None:
    normalized = trim(_text(value))
    return normalized or None
