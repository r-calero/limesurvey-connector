"""Whole-survey rules (port of ``validateSurveyInvariants`` in survey-structure)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

from survey_structure import _js
from survey_structure.response_keys import field_response_keys

Report = Callable[[dict[str, Any]], None]
Field = dict[str, Any]
Path = list[str | int]

_MISSING_FIELD = "condition-reference-missing-field"
_MISSING_ITEM = "condition-reference-missing-response-item"
_ORDERED = ("greater-than", "greater-than-or-equal", "less-than", "less-than-or-equal")
_BOUND_RULES = ("itemMin", "itemMax", "sumMin", "sumMax", "sumEquals")
_NO_SCALAR_ALIAS = (
    "display",
    "multiple-choice",
    "multiple-choice-with-comments",
    "matrix",
    "multiple-input",
    "ranking",
    "custom",
)
_COLLECTIONS = (
    "custom",
    "display",
    "multiple-input",
    "multiple-choice",
    "multiple-choice-with-comments",
    "ranking",
    "matrix",
)


def validate_survey_invariants(survey: dict[str, Any], report: Report) -> None:
    groups: set[str] = set()
    for index, group in enumerate(survey.get("groups", [])):
        if group["id"] in groups:
            report(
                {
                    "code": "custom",
                    "path": ["groups", index, "id"],
                    "message": f"Group id {group['id']} is duplicated.",
                    "params": {"reason": "duplicate-group-id", "groupId": group["id"]},
                }
            )
        groups.add(group["id"])

    fields_by_code: dict[str, Field] = {}
    response_keys: set[str] = set()
    for index, field in enumerate(survey["fields"]):
        for response_key in field_response_keys(field):
            if response_key in response_keys:
                report(
                    {
                        "code": "custom",
                        "path": ["fields", index],
                        "message": f'Response key "{response_key}" is produced more than once and would '
                        "overwrite an answer.",
                        "params": {
                            "reason": "duplicate-response-key",
                            "fieldCode": field["code"],
                            "responseKey": response_key,
                        },
                    }
                )
            response_keys.add(response_key)

    field_ids: set[str] = set()
    for field, path, parent in _visit(survey["fields"]):
        if field["id"] in field_ids:
            report(
                {
                    "code": "custom",
                    "path": [*path, "id"],
                    "message": f"Field id {field['id']} is duplicated.",
                    "params": {"reason": "duplicate-field-id", "fieldId": field["id"]},
                }
            )
        field_ids.add(field["id"])
        if field["code"] in fields_by_code:
            report(
                {
                    "code": "custom",
                    "path": [*path, "code"],
                    "message": f"Field code {field['code']} is duplicated.",
                    "params": {"reason": "duplicate-field-code", "fieldCode": field["code"]},
                }
            )
        fields_by_code[field["code"]] = field
        group_id = field.get("groupId")
        if group_id and group_id not in groups:
            report(
                {
                    "code": "custom",
                    "path": [*path, "groupId"],
                    "message": f"groupId {group_id} does not reference a declared group.",
                    "params": {
                        "reason": "field-group-reference-missing",
                        "fieldCode": field["code"],
                        "groupId": group_id,
                    },
                }
            )
        parent_id = field.get("parentId")
        if parent is None and parent_id:
            report(
                {
                    "code": "custom",
                    "path": [*path, "parentId"],
                    "message": f'Top-level field "{field["code"]}" cannot declare parentId "{parent_id}".',
                    "params": {
                        "reason": "top-level-field-has-parent",
                        "fieldCode": field["code"],
                        "parentId": parent_id,
                    },
                }
            )
        if parent is not None and parent_id and parent_id != parent["id"]:
            report(
                {
                    "code": "custom",
                    "path": [*path, "parentId"],
                    "message": f'Child field "{field["code"]}" declares parentId "{parent_id}", but its '
                    f'containing field has id "{parent["id"]}".',
                    "params": {
                        "reason": "child-parent-reference-mismatch",
                        "fieldCode": field["code"],
                        "parentId": parent_id,
                        "expectedParentId": parent["id"],
                    },
                }
            )
        _validate_response_item_identities(field, path, report)

    for field, path, _ in _visit(survey["fields"]):
        _validate_field_references(survey, field, path, fields_by_code, report)
        condition = field.get("visibility", {}).get("condition")
        if condition:
            _validate_condition(
                condition,
                fields_by_code,
                report,
                [*path, "visibility", "condition"],
                f'field "{field["code"]}"',
            )
    for index, group in enumerate(survey.get("groups", [])):
        for rule_index, rule in enumerate(group.get("navigation", [])):
            _validate_condition(
                rule["condition"],
                fields_by_code,
                report,
                ["groups", index, "navigation", rule_index, "condition"],
                f'navigation of group "{group["id"]}"',
            )
            destination = rule["destination"]
            if "groupId" in destination and destination["groupId"] not in groups:
                report(
                    {
                        "code": "custom",
                        "path": ["groups", index, "navigation", rule_index, "destination"],
                        "message": "Navigation destination must reference a declared group.",
                    }
                )
        condition = group.get("visibility", {}).get("condition")
        if condition:
            title = group["title"] if group.get("title") is not None else group["id"]
            _validate_condition(
                condition,
                fields_by_code,
                report,
                ["groups", index, "visibility", "condition"],
                f'group "{title}"',
            )


def _validate_field_references(
    survey: dict[str, Any],
    field: Field,
    path: Path,
    fields_by_code: dict[str, Field],
    report: Report,
) -> None:
    code = field["code"]
    if field["type"] == "multiple-input":
        rules = field.get("responseValidation", {})
        for rule in _BOUND_RULES:
            reference = rules.get(f"{rule}Reference")
            if not reference:
                continue
            target = fields_by_code.get(reference)
            top_level = any(candidate["code"] == reference for candidate in survey["fields"])
            if target is None or target["type"] != "number" or not top_level:
                report(
                    {
                        "code": "custom",
                        "path": [*path, "responseValidation", f"{rule}Reference"],
                        "message": f"The {rule} reference must identify an existing numeric question.",
                        "params": {
                            "reason": "numeric-bound-reference-incompatible",
                            "fieldCode": reference,
                        },
                    }
                )
    for index, option in enumerate(field.get("options", [])):
        if option.get("visibility"):
            _validate_condition(
                option["visibility"]["condition"],
                fields_by_code,
                report,
                [*path, "options", index, "visibility", "condition"],
                f'option "{option["code"]}" of field "{code}"',
            )
    if field["type"] != "matrix":
        return
    matrix = field["matrix"]
    for index, row in enumerate(matrix["rows"]):
        if row.get("visibility"):
            _validate_condition(
                row["visibility"]["condition"],
                fields_by_code,
                report,
                [*path, "matrix", "rows", index, "visibility", "condition"],
                f'row "{row["code"]}" of field "{code}"',
            )
    for index, column in enumerate(matrix["columns"]):
        if column.get("visibility"):
            _validate_condition(
                column["visibility"]["condition"],
                fields_by_code,
                report,
                [*path, "matrix", "columns", index, "visibility", "condition"],
                f'column "{column["code"]}" of field "{code}"',
            )
    if matrix["mode"] == "dual-single":
        for column_index, column in enumerate(matrix["columns"]):
            for option_index, option in enumerate(column["options"]):
                if option.get("visibility"):
                    _validate_condition(
                        option["visibility"]["condition"],
                        fields_by_code,
                        report,
                        [
                            *path,
                            "matrix",
                            "columns",
                            column_index,
                            "options",
                            option_index,
                            "visibility",
                            "condition",
                        ],
                        f'option "{option["code"]}" of scale "{column["code"]}" of field "{code}"',
                    )
    cells: set[tuple[str, str]] = set()
    row_codes = {row["code"] for row in matrix["rows"]}
    column_codes = {column["code"] for column in matrix["columns"]}
    for index, cell in enumerate(matrix.get("cells", [])):
        cell_path: Path = [*path, "matrix", "cells", index]
        identity = (cell["rowCode"], cell["columnCode"])
        if (
            identity in cells
            or cell["rowCode"] not in row_codes
            or cell["columnCode"] not in column_codes
        ):
            report(
                {
                    "code": "custom",
                    "path": cell_path,
                    "message": "Matrix cell rules require unique, declared row and column codes.",
                }
            )
        cells.add(identity)
        _validate_condition(
            cell["visibility"]["condition"],
            fields_by_code,
            report,
            [*cell_path, "visibility", "condition"],
            f'cell "{cell["rowCode"]}/{cell["columnCode"]}" of field "{code}"',
        )


def _visit(
    fields: list[Field], parent_path: Path | None = None, parent: Field | None = None
) -> Iterator[tuple[Field, Path, Field | None]]:
    for index, field in enumerate(fields):
        path: Path = [*(parent_path or ["fields"]), index]
        yield field, path, parent
        if field["type"] == "custom":
            yield from _visit(field["childrenFields"], [*path, "childrenFields"], field)


def _validate_response_item_identities(field: Field, path: Path, report: Report) -> None:
    if "options" in field:
        _unique_codes(field["options"], [*path, "options"], "option", field["code"], report)
    if field["type"] == "multiple-input":
        _unique_codes(
            field["subquestions"], [*path, "subquestions"], "subquestion", field["code"], report
        )
        ids: set[str] = set()
        for index, subquestion in enumerate(field["subquestions"]):
            identifier = subquestion.get("id")
            if not identifier:
                continue
            if identifier in ids:
                report(
                    {
                        "code": "custom",
                        "path": [*path, "subquestions", index, "id"],
                        "message": f"Subquestion id {identifier} is duplicated inside field {field['code']}.",
                        "params": {
                            "reason": "duplicate-subquestion-id",
                            "fieldCode": field["code"],
                            "subquestionId": identifier,
                        },
                    }
                )
            ids.add(identifier)
    if field["type"] == "matrix":
        matrix = field["matrix"]
        _unique_codes(
            matrix["rows"], [*path, "matrix", "rows"], "matrix row", field["code"], report
        )
        _unique_codes(
            matrix["columns"], [*path, "matrix", "columns"], "matrix column", field["code"], report
        )
        if matrix["mode"] == "dual-single":
            for index, column in enumerate(matrix["columns"]):
                _unique_codes(
                    column["options"],
                    [*path, "matrix", "columns", index, "options"],
                    "scale option",
                    field["code"],
                    report,
                )
    aliases = field.get("source", {}).get("responseAliases")
    if aliases:
        items = _field_response_item_codes(field)
        for index, item in enumerate(aliases):
            item_code = item.get("responseItemCode")
            valid = (
                field["type"] not in _NO_SCALAR_ALIAS if item_code is None else item_code in items
            )
            if not valid:
                report(
                    {
                        "code": "custom",
                        "path": [*path, "source", "responseAliases", index, "responseItemCode"],
                        "message": f'Source alias refers to an unknown response item in field "{field["code"]}".',
                    }
                )


def _unique_codes(
    items: list[dict[str, Any]], path: Path, item_name: str, field_code: str, report: Report
) -> None:
    codes: set[str] = set()
    for index, item in enumerate(items):
        if item["code"] in codes:
            report(
                {
                    "code": "custom",
                    "path": [*path, index, "code"],
                    "message": f"{item_name} code {item['code']} is duplicated inside field {field_code}.",
                    "params": {
                        "reason": "duplicate-response-item-code",
                        "fieldCode": field_code,
                        "responseItemCode": item["code"],
                        "itemType": item_name,
                    },
                }
            )
        codes.add(item["code"])


def _field_response_item_codes(field: Field) -> set[str]:
    if field["type"] == "ranking":
        return {str(index + 1) for index in range(len(field["options"]))}
    if "options" in field:
        return {option["code"] for option in field["options"]}
    if field["type"] == "multiple-input":
        return {item["code"] for item in field["subquestions"]}
    if field["type"] == "matrix":
        values: set[str] = set()
        for row in field["matrix"]["rows"]:
            values.add(row["code"])
            values.update(
                f"{row['code']}_{column['code']}" for column in field["matrix"]["columns"]
            )
        return values
    return set()


def _condition_response_item_codes(field: Field) -> set[str]:
    if field["type"] in ("multiple-choice", "multiple-choice-with-comments"):
        codes = {option["code"] for option in field["options"]}
        if field.get("other"):
            codes.add(field["other"]["code"])
        return codes
    if field["type"] == "matrix":
        matrix = field["matrix"]
        if matrix["mode"] == "single":
            return {row["code"] for row in matrix["rows"]}
        return {
            f"{row['code']}_{column['code']}"
            for row in matrix["rows"]
            for column in matrix["columns"]
        }
    if field["type"] in ("ranking", "multiple-input"):
        return _field_response_item_codes(field)
    return set()


def _comparison_value_matches(field: Field, item: str | None, value: object) -> bool:
    if value is None:
        return True
    field_type = field["type"]
    mode = field["matrix"]["mode"] if field_type == "matrix" else None
    if field_type in ("number", "range") or mode == "number":
        return _js.is_number(value)
    if field_type == "multiple-input":
        return True
    if (
        field_type in ("boolean", "multiple-choice", "multiple-choice-with-comments")
        or mode == "multiple"
    ):
        encoding = field.get("responseEncoding", {})
        return (
            isinstance(value, bool)
            or _js.strict_equal(value, encoding.get("selectedValue", _js.UNDEFINED))
            or _js.strict_equal(value, encoding.get("unselectedValue", _js.UNDEFINED))
        )
    if mode == "single":
        return any(_js.strict_equal(column["code"], value) for column in field["matrix"]["columns"])
    if mode == "dual-single":
        matrix = field["matrix"]
        scale = next(
            (
                column
                for column in matrix["columns"]
                if any(f"{row['code']}_{column['code']}" == item for row in matrix["rows"])
            ),
            None,
        )
        return scale is not None and any(
            _js.strict_equal(option["code"], value) for option in scale["options"]
        )
    if "options" in field:
        other = field.get("other")
        return any(_js.strict_equal(option["code"], value) for option in field["options"]) or (
            other is not None and _js.strict_equal(value, other["code"])
        )
    return isinstance(value, str)


def _validate_condition(
    condition: dict[str, Any],
    fields_by_code: dict[str, Field],
    report: Report,
    path: Path,
    owner: str,
) -> None:
    kind = condition["type"]
    if kind == "constant":
        return
    if kind in ("all", "any"):
        for index, child in enumerate(condition["conditions"]):
            _validate_condition(child, fields_by_code, report, [*path, "conditions", index], owner)
        return
    if kind == "not":
        _validate_condition(
            condition["condition"], fields_by_code, report, [*path, "condition"], owner
        )
        return
    if "responseReference" not in condition:
        return
    reference = condition["responseReference"]
    field = fields_by_code.get(reference["fieldCode"])
    if field is None:
        report(
            {
                "code": "custom",
                "path": [*path, "responseReference", "fieldCode"],
                "message": f"The visibility condition of {owner} cannot be evaluated because it references "
                f'field code "{reference["fieldCode"]}", but no field with that code exists in the '
                "normalized survey.",
                "params": {
                    "reason": _MISSING_FIELD,
                    "fieldCode": reference["fieldCode"],
                    "owner": owner,
                },
            }
        )
        return
    field_type = field["type"]
    mode = field["matrix"]["mode"] if field_type == "matrix" else None
    item = reference.get("responseItemCode")
    item_codes = condition.get("responseItemCodes")
    if item_codes:
        allowed = _condition_response_item_codes(field)
        seen: set[str] = set()
        for index, code in enumerate(item_codes):
            if code not in allowed:
                report(
                    {
                        "code": "custom",
                        "path": [*path, "responseItemCodes", index],
                        "message": f'The aggregate condition of {owner} references response item "{code}", '
                        f'which field "{field["code"]}" does not produce.',
                        "params": {
                            "reason": _MISSING_ITEM,
                            "fieldCode": field["code"],
                            "responseItemCode": code,
                            "owner": owner,
                        },
                    }
                )
            if code in seen:
                report(
                    {
                        "code": "custom",
                        "path": [*path, "responseItemCodes", index],
                        "message": f'Response item "{code}" occurs more than once in the aggregate condition '
                        f"of {owner}. Each response may contribute only once.",
                        "params": {
                            "reason": "duplicate-aggregate-response-item-code",
                            "fieldCode": field["code"],
                            "responseItemCode": code,
                            "owner": owner,
                        },
                    }
                )
            seen.add(code)
    if item and item not in _condition_response_item_codes(field):
        report(
            {
                "code": "custom",
                "path": [*path, "responseReference", "responseItemCode"],
                "message": f'The visibility condition of {owner} references response item code "{item}", '
                f'but field "{field["code"]}" does not produce that scalar response item in this variant.',
                "params": {
                    "reason": _MISSING_ITEM,
                    "fieldCode": field["code"],
                    "responseItemCode": item,
                    "owner": owner,
                },
            }
        )
    if kind == "comparison":
        if field_type in _COLLECTIONS and not item:
            report(
                {
                    "code": "custom",
                    "path": [*path, "responseReference"],
                    "message": "A comparison requires one scalar response, not an entire collection or display field.",
                    "params": {
                        "reason": "comparison-requires-scalar-response",
                        "fieldCode": field["code"],
                        "owner": owner,
                    },
                }
            )
        if not _comparison_value_matches(field, item, condition["value"]):
            params: dict[str, Any] = {
                "reason": "comparison-value-type-mismatch",
                "fieldCode": field["code"],
            }
            if item is not None:
                params["responseItemCode"] = item
            params["owner"] = owner
            report(
                {
                    "code": "custom",
                    "path": [*path, "value"],
                    "message": "The comparison value does not match the referenced response type or its "
                    "declared options.",
                    "params": params,
                }
            )
    if kind == "pattern-match":
        scalar_text = (
            field_type in ("short-text", "long-text")
            or (field_type == "number" and field.get("responseValueType") == "text")
            or (field_type == "multiple-input" and bool(item))
            or (mode == "text" and bool(item))
        )
        if not scalar_text:
            report(
                {
                    "code": "custom",
                    "path": [*path, "responseReference"],
                    "message": "A pattern condition requires one text response.",
                    "params": {
                        "reason": "pattern-requires-text-response",
                        "fieldCode": field["code"],
                        "owner": owner,
                    },
                }
            )
    if kind == "selection-count" and not (
        field_type in ("multiple-choice", "multiple-choice-with-comments", "ranking")
        or mode == "multiple"
    ):
        report(
            {
                "code": "custom",
                "path": [*path, "responseReference", "fieldCode"],
                "message": f"The selection-count condition of {owner} requires a field that can contain "
                f'multiple selected responses; field "{field["code"]}" has type "{field_type}".',
                "params": {
                    "reason": "selection-count-incompatible-field-type",
                    "fieldCode": field["code"],
                    "semanticFieldType": field_type,
                    "owner": owner,
                },
            }
        )
    if kind == "answered-count" and not (
        field_type in ("multiple-input", "multiple-choice")
        or (field_type == "matrix" and mode != "multiple")
    ):
        report(
            {
                "code": "custom",
                "path": [*path, "responseReference", "fieldCode"],
                "message": f'Answered-count requires multiple inputs or matrix response cells in field "{field["code"]}".',
                "params": {
                    "reason": "answered-count-incompatible-field-type",
                    "fieldCode": field["code"],
                    "owner": owner,
                },
            }
        )
    if kind in ("selection-count", "answered-count") and item:
        report(
            {
                "code": "custom",
                "path": [*path, "responseReference", "responseItemCode"],
                "message": "A count refers to the entire question, not an individual response item.",
                "params": {
                    "reason": "count-requires-whole-field",
                    "fieldCode": field["code"],
                    "owner": owner,
                },
            }
        )
    if kind == "numeric-aggregate":
        if mode != "number":
            report(
                {
                    "code": "custom",
                    "path": [*path, "responseReference", "fieldCode"],
                    "message": f'A numeric aggregate requires numeric matrix cells; field "{field["code"]}" '
                    "does not declare numeric cells.",
                    "params": {
                        "reason": "numeric-aggregate-incompatible-field-type",
                        "fieldCode": field["code"],
                        "owner": owner,
                    },
                }
            )
        if item:
            report(
                {
                    "code": "custom",
                    "path": [*path, "responseReference", "responseItemCode"],
                    "message": "An aggregate identifies its question with responseReference and any subset "
                    "with responseItemCodes.",
                    "params": {
                        "reason": "aggregate-requires-whole-field",
                        "fieldCode": field["code"],
                        "owner": owner,
                    },
                }
            )
    if (
        kind == "comparison"
        and condition["operator"] in _ORDERED
        and field_type not in ("number", "range", "date")
        and not (
            mode == "number"
            and any(
                f"{row['code']}_{column['code']}" == item
                for row in field["matrix"]["rows"]
                for column in field["matrix"]["columns"]
            )
        )
    ):
        report(
            {
                "code": "custom",
                "path": [*path, "operator"],
                "message": f'The visibility condition of {owner} uses operator "{condition["operator"]}" with '
                f'field "{field["code"]}" of type "{field_type}", which is not compatible with ordered comparison.',
                "params": {
                    "reason": "ordered-comparison-incompatible-field-type",
                    "fieldCode": field["code"],
                    "semanticFieldType": field_type,
                    "operator": condition["operator"],
                    "owner": owner,
                },
            }
        )
