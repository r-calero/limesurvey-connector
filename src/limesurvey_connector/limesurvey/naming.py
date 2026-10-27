"""LimeSurvey column names (intentional change ``limesurvey-column-names``).

The dictionary uses the underscore form of LimeSurvey's own names, as in ``vv``
exports and Expression Manager: ``Q1_SQ001``, ``Q2_SQ001_0``, ``Q11_SQ001comment``,
``Q12_other``, ``Q5_othercomment`` and ``Q1_comment``. The normalizer writes these
names as explicit response keys; ``with_limesurvey_names`` covers structures that
come from elsewhere.
Exports with code headings write the same columns with brackets (``Q1[SQ001]``,
``Q2[SQ001][1]``, ``Q11[SQ001comment]``); readers convert them before mapping.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, cast

from survey_data_dictionary import SurveyDictionary

_CODE = r"[A-Za-z][A-Za-z0-9_]*"
_ITEM = r"[A-Za-z0-9_#]+"
_DUAL = re.compile(rf"^(?P<code>{_CODE})\[(?P<item>{_ITEM})\]\[(?P<scale>[12])\]$")
_SINGLE = re.compile(rf"^(?P<code>{_CODE})\[(?P<item>{_ITEM})\]$")


def underscore_column(name: str) -> str:
    """``Q1[SQ001]`` -> ``Q1_SQ001``; dual scales ``Q2[SQ001][1]`` -> ``Q2_SQ001_0``; others unchanged."""
    dual = _DUAL.match(name)
    if dual:
        return f"{dual['code']}_{dual['item']}_{int(dual['scale']) - 1}"
    single = _SINGLE.match(name)
    if single:
        return f"{single['code']}_{single['item']}"
    return name


def underscore_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Rename bracketed keys; a key that would collide with an existing one is left as it is."""
    renamed: dict[str, Any] = {}
    for key, value in record.items():
        target = underscore_column(key)
        renamed[target if target == key or target not in record else key] = value
    return renamed


def _renamed_key(field: Mapping[str, Any]) -> str | None:
    key, code, parent = field["responseKey"], field["questionCode"], field.get("parentCode")
    if not parent:
        return None
    if key == f"{parent}_comment" and field["cardinality"] == "multiple":
        # Option comment without an explicit key: Q11_SQ001_comment -> Q11_SQ001comment.
        return f"{parent}comment"
    if key == f"{parent}comment" and field["cardinality"] == "single":
        # List-with-comment comment written as limesurvey-rc2-api does: Q1comment -> Q1_comment.
        return f"{parent}_comment"
    if key == f"{parent}other" and parent.endswith(code):
        # Other text written as limesurvey-rc2-api does: Q12other -> Q12_other.
        return f"{parent}_other"
    return None


def _sgqa(dictionary: SurveyDictionary, field: Mapping[str, Any], suffix: str) -> str | None:
    if not field.get("qid") or not field.get("groupId"):
        return None
    return f"{dictionary['surveyId']}X{field['groupId']}X{field['qid']}{suffix}"


def with_limesurvey_names(dictionary: SurveyDictionary) -> SurveyDictionary:
    """Use LimeSurvey's own names for comment and "other" columns, keeping the old keys as aliases."""
    renames = {
        field["responseKey"]: target
        for field in dictionary["fields"]
        if (target := _renamed_key(field)) is not None
    }
    fields = []
    for field in dictionary["fields"]:
        key = field["responseKey"]
        if key in renames:
            target = renames[key]
            aliases = [
                alias.removesuffix("_comment") + "comment" if alias.endswith("_comment") else alias
                for alias in field.get("aliases", [])
            ]
            # The reference dictionary cannot derive the SGQA address of Qother; Q_other gets it.
            sgqa = _sgqa(dictionary, field, "other") if target.endswith("_other") else None
            field = {
                **field,
                "responseKey": target,
                "aliases": list(dict.fromkeys([*aliases, *([sgqa] if sgqa else []), key])),
            }
        parent = field.get("parentCode")
        if parent in renames:
            field = {**field, "parentCode": renames[parent]}
        fields.append(field)
    return cast(SurveyDictionary, {**dictionary, "fields": fields})
