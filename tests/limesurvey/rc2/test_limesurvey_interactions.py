from copy import deepcopy
from xml.etree.ElementTree import SubElement, fromstring, tostring

import pytest

from limesurvey_connector.limesurvey.normalization import (
    build_survey_structure,
    survey_structure_from_lss,
)
from tests.limesurvey.rc2.test_fixed_question_types import as_lss as scalar_lss


def as_lss(native):
    native = deepcopy(native)
    attributes = [
        (question["qid"], key, value)
        for question in native["questions"]
        for key, value in question.pop("attributes", {}).items()
    ]
    root = fromstring(scalar_lss(native))
    rows = SubElement(SubElement(root, "question_attributes"), "rows")
    for qid, key, value in attributes:
        row = SubElement(rows, "row")
        for name, text in (("qid", qid), ("attribute", key), ("value", value), ("language", "es")):
            SubElement(row, name).text = text
    return tostring(root)


def payload():
    return {
        "survey": {"sid": "filters", "language": "es"},
        "groups": [{"gid": "10", "group_name": "Servicios"}],
        "questions": [
            {
                "qid": "1",
                "title": "SERVICES",
                "type": "M",
                "mandatory": "Y",
                "attributes": {"exclude_all_others": "NONE"},
            },
            {"qid": "2", "parent_qid": "1", "title": "LIB", "question": "Biblioteca", "type": "T"},
            {"qid": "3", "parent_qid": "1", "title": "LAB", "question": "Laboratorio", "type": "T"},
            {"qid": "4", "parent_qid": "1", "title": "NONE", "question": "Ninguna", "type": "T"},
            {
                "qid": "5",
                "title": "QUALITY",
                "question": "Calidad del servicio",
                "type": "A",
                "mandatory": "Y",
                "attributes": {"array_filter": "SERVICES"},
            },
            {
                "qid": "6",
                "parent_qid": "5",
                "title": "LIB",
                "question": "Biblioteca",
                "type": "T",
                "relevance": 'SERVICES_LAB.NAOK == "Y"',
            },
            {"qid": "7", "parent_qid": "5", "title": "LAB", "question": "Laboratorio", "type": "T"},
            {
                "qid": "8",
                "title": "NOT_USED",
                "type": "E",
                "attributes": {"array_filter_exclude": "SERVICES"},
            },
            {"qid": "9", "parent_qid": "8", "title": "LIB", "question": "Biblioteca", "type": "T"},
        ],
    }


@pytest.mark.parametrize("source", ["remotecontrol", "lss"])
def test_filters_combine_child_relevance_and_keep_exclusive_option(source):
    native = payload()
    for question in native["questions"]:
        question.update(gid="10", parent_qid=question.get("parent_qid", "0"), language="es")
    result = (
        build_survey_structure(native)
        if source == "remotecontrol"
        else survey_structure_from_lss(as_lss(native))
    )
    assert result["issues"] == []
    fields = result["survey"]["fields"]
    assert fields[0]["options"][2]["exclusive"] is True
    conditions = fields[1]["matrix"]["rows"][0]["visibility"]["condition"]["conditions"]
    assert [condition["responseReference"]["responseItemCode"] for condition in conditions] == [
        "LAB",
        "LIB",
    ]
    assert fields[2]["matrix"]["rows"][0]["visibility"]["condition"]["type"] == "not"


def test_unknown_filter_and_exclusive_codes_remain_explicit_diagnostics():
    native = payload()
    native["questions"][0]["attributes"]["exclusive_option"] = "UNKNOWN"
    native["questions"][4]["attributes"]["array_filter"] = "DOES_NOT_EXIST"
    result = build_survey_structure(native)
    assert {"array_filter", "exclusive_option"} <= {
        issue.get("details", {}).get("rule") for issue in result["issues"]
    }


def test_child_checkbox_relevance_and_cascaded_filters_are_combined():
    native = payload()
    native["questions"][1]["relevance"] = 'SERVICES_LAB.NAOK == "Y"'
    native["questions"] += [
        {"qid": "11", "title": "FOLLOW", "type": "M", "attributes": {"array_filter": "SERVICES"}},
        {"qid": "12", "parent_qid": "11", "title": "LIB", "question": "Biblioteca", "type": "T"},
        {"qid": "13", "title": "CASCADE", "type": "A", "attributes": {"array_filter": "FOLLOW"}},
        {"qid": "14", "parent_qid": "13", "title": "LIB", "question": "Biblioteca", "type": "T"},
    ]
    result = build_survey_structure(native)
    assert not any(issue["code"] == "INVALID_EXPRESSION" for issue in result["issues"])
    fields = {field["code"]: field for field in result["survey"]["fields"]}
    assert (
        fields["SERVICES"]["options"][0]["visibility"]["condition"]["responseReference"][
            "responseItemCode"
        ]
        == "LAB"
    )
    assert (
        fields["FOLLOW"]["options"][0]["visibility"]["condition"]["responseReference"]["fieldCode"]
        == "SERVICES"
    )
    assert [
        condition["responseReference"]["fieldCode"]
        for condition in fields["CASCADE"]["matrix"]["rows"][0]["visibility"]["condition"][
            "conditions"
        ]
    ] == ["FOLLOW", "SERVICES"]
