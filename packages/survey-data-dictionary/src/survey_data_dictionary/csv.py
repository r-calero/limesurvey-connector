"""CSV serialization of dictionaries and translations (port of ``csv.ts``)."""

from __future__ import annotations

import re
from typing import Any

from survey_data_dictionary.contracts import SurveyDictionary, TranslatedDataset, TranslatedResponse
from survey_structure._js import UNDEFINED, stringify, to_string

_DICTIONARY_HEADERS = [
    "survey_id",
    "qid",
    "group_id",
    "question_code",
    "response_key",
    "question_label",
    "data_type",
    "cardinality",
    "aliases",
    "value_code",
    "value_label",
]
_TRANSLATION_HEADERS = [
    "response_index",
    "response_id",
    "mapped",
    "response_key",
    "question_code",
    "question_label",
    "source_value",
    "display_value",
    "missing",
]
_FORMULA = re.compile(r"^[=+\-@\t\r]")


def dictionary_to_csv(
    dictionary: SurveyDictionary, *, prevent_formula_injection: bool = True
) -> str:
    rows: list[list[Any]] = []
    for field in dictionary["fields"]:
        base = [
            dictionary["surveyId"],
            field.get("qid"),
            field.get("groupId"),
            field["questionCode"],
            field["responseKey"],
            field["questionLabel"],
            field["dataType"],
            field["cardinality"],
            " | ".join(field.get("aliases", [])),
        ]
        values = field.get("values") or []
        if values:
            rows.extend([*base, value["code"], value["label"]] for value in values)
        else:
            rows.append([*base, "", ""])
    return _to_csv([_DICTIONARY_HEADERS, *rows], prevent_formula_injection)


def translated_response_to_csv(
    response: TranslatedResponse, *, prevent_formula_injection: bool = True
) -> str:
    return translated_dataset_to_csv(
        {"responses": [response], "issues": response["issues"]},
        prevent_formula_injection=prevent_formula_injection,
    )


def translated_dataset_to_csv(
    dataset: TranslatedDataset, *, prevent_formula_injection: bool = True
) -> str:
    rows: list[list[Any]] = []
    for response in dataset["responses"]:
        index, identifier = response["responseIndex"], response.get("responseId", UNDEFINED)
        rows.extend(
            [
                index,
                identifier,
                True,
                field["responseKey"],
                field["questionCode"],
                field["questionLabel"],
                _serialize(field["sourceValue"]),
                _serialize(field["displayValue"]),
                field["missing"],
            ]
            for field in response["fields"]
        )
        rows.extend(
            [
                index,
                identifier,
                False,
                value["sourceKey"],
                "",
                "",
                _serialize(value["sourceValue"]),
                _serialize(value["sourceValue"]),
                value["sourceValue"] is None or value["sourceValue"] == "",
            ]
            for value in response["unmappedValues"]
        )
    return _to_csv([_TRANSLATION_HEADERS, *rows], prevent_formula_injection)


def _serialize(value: Any) -> Any:
    if isinstance(value, dict | list):
        return stringify(value)
    return value


def _to_csv(rows: list[list[Any]], prevent_formula_injection: bool) -> str:
    return (
        "\n".join(
            ",".join(_cell(value, prevent_formula_injection) for value in row) for row in rows
        )
        + "\n"
    )


def _cell(value: Any, prevent_formula_injection: bool) -> str:
    raw = "" if value is None or value is UNDEFINED else to_string(value)
    if prevent_formula_injection and isinstance(value, str) and _FORMULA.match(raw):
        raw = f"'{raw}"
    return '"' + raw.replace('"', '""') + '"'
