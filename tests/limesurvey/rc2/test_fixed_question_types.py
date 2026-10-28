"""Synthetic definitions only: no remote instance or participant answers."""

from xml.etree.ElementTree import Element, SubElement, tostring

import pytest

from limesurvey_connector.limesurvey.normalization import (
    build_survey_structure,
    survey_structure_from_lss,
)


def fixed_payload(language="es-MX"):
    questions = [
        {"qid": "1", "title": "RATING", "type": "5", "mandatory": "Y"},
        {"qid": "2", "title": "SCALE", "type": "A"},
        {"qid": "3", "title": "CERTAINTY", "type": "C"},
        {"qid": "4", "title": "LONG", "type": "U"},
        {"qid": "5", "title": "FOLLOW", "type": "S", "relevance": 'RATING.NAOK > "3"'},
        {"qid": "6", "title": "FOLLOW_ROW", "type": "S", "relevance": '123X10X3SQ001.NAOK == "U"'},
        {"qid": "7", "title": "FOLLOW_SCALE", "type": "S", "relevance": "SCALE_SQ001.NAOK == 4"},
        {
            "qid": "8",
            "title": "FOLLOW_COUNT",
            "type": "S",
            "relevance": "count(that.CERTAINTY.NAOK) >= 1",
        },
    ]
    for parent in ("2", "3"):
        questions.append({"qid": f"{parent}1", "parent_qid": parent, "title": "SQ001", "type": "T"})
    questions = [
        {"gid": "10", "parent_qid": "0", "language": language, "question": q["title"], **q}
        for q in questions
    ]
    return {
        "survey": {"sid": "123", "language": language},
        "groups": [{"gid": "10", "group_name": "Synthetic", "language": language}],
        "questions": questions,
    }


def as_lss(payload):
    root = Element("document")
    SubElement(root, "LimeSurveyDocType").text = "Survey"
    SubElement(root, "DBVersion").text = "348"
    for name, rows in [
        ("surveys", [payload["survey"]]),
        ("groups", payload["groups"]),
        ("questions", payload["questions"]),
    ]:
        container = SubElement(SubElement(root, name), "rows")
        for source in rows:
            row = SubElement(container, "row")
            for key, value in source.items():
                SubElement(row, key).text = value
    return tostring(root)


@pytest.mark.parametrize("source", ["remotecontrol", "lss"])
@pytest.mark.parametrize(("language", "uncertain"), [("es-MX", "No sé"), ("en", "Uncertain")])
def test_fixed_types_keep_codes_rows_radio_and_conditions(source, language, uncertain):
    payload = fixed_payload(language)
    result = (
        build_survey_structure(payload)
        if source == "remotecontrol"
        else survey_structure_from_lss(as_lss(payload))
    )
    assert result["issues"] == []
    fields = {f["code"]: f for f in result["survey"]["fields"]}
    assert len(fields) == 8
    assert fields["RATING"]["rendering"]["widget"] == "radio-group"
    assert fields["RATING"]["required"] is True
    assert [o["code"] for o in fields["RATING"]["options"]] == ["1", "2", "3", "4", "5"]
    assert fields["SCALE"]["matrix"]["columns"] == fields["RATING"]["options"]
    assert fields["CERTAINTY"]["matrix"]["columns"] == [
        {"code": "Y", "label": "Sí" if language.startswith("es") else "Yes", "order": 0},
        {"code": "U", "label": uncertain, "order": 1},
        {"code": "N", "label": "No", "order": 2},
    ]
    assert fields["LONG"]["type"] == "long-text"
    assert fields["LONG"]["source"]["nativeType"] == "U"
    assert fields["FOLLOW"]["visibility"]["condition"] == {
        "type": "any",
        "conditions": [
            {
                "type": "comparison",
                "responseReference": {"fieldCode": "RATING"},
                "operator": "equals",
                "value": v,
            }
            for v in ["4", "5"]
        ],
    }
    assert fields["FOLLOW_ROW"]["visibility"]["condition"]["responseReference"] == {
        "fieldCode": "CERTAINTY",
        "responseItemCode": "SQ001",
    }
    assert fields["FOLLOW_ROW"]["visibility"]["condition"]["value"] == "U"
    assert fields["FOLLOW_SCALE"]["visibility"]["condition"]["value"] == "4"
    assert fields["FOLLOW_COUNT"]["visibility"]["condition"]["type"] == "answered-count"


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("RATING.NAOK >= 5", "comparison"),
        ("RATING.NAOK > 5", "constant"),
        ("SCALE_SQ001.NAOK >= 4", "any"),
    ],
)
def test_fixed_scale_ordered_thresholds(expression, expected):
    payload = fixed_payload()
    payload["questions"][4]["relevance"] = expression
    result = build_survey_structure(payload)
    assert result["issues"] == []
    assert result["survey"]["fields"][4]["visibility"]["condition"]["type"] == expected


def test_ambiguous_empty_scale_comparison_is_explicit_warning():
    payload = fixed_payload()
    payload["questions"][4]["relevance"] = "RATING.NAOK >= 0"
    result = build_survey_structure(payload)
    assert any(
        i["code"] == "UNSUPPORTED_SOURCE_EXPRESSION" and i["questionCode"] == "FOLLOW"
        for i in result["issues"]
    )
    assert "visibility" not in result["survey"]["fields"][4]


@pytest.mark.parametrize("source", ["remotecontrol", "lss"])
def test_encoded_relevance_preserves_rc2_lss_equivalence(source):
    payload = fixed_payload()
    expression = "!is_empty(RATING.NAOK) &amp;&amp; (RATING.NAOK &gt; &quot;3&quot;)"
    payload["questions"][4]["relevance"] = expression
    payload["questions"][3]["relevance"] = "6"
    payload["groups"][0]["grelevance"] = "LONG.NAOK == &quot;A&amp;amp;B &copy;&quot;"
    result = (
        build_survey_structure(payload)
        if source == "remotecontrol"
        else survey_structure_from_lss(as_lss(payload))
    )
    assert result["issues"] == []
    assert result["survey"]["fields"][3]["visibility"]["condition"] == {
        "type": "constant",
        "value": True,
    }
    condition = result["survey"]["fields"][4]["visibility"]["condition"]
    assert condition["type"] == "all"
    assert condition["conditions"][1]["type"] == "any"
    assert [item["value"] for item in condition["conditions"][1]["conditions"]] == ["4", "5"]
    assert result["survey"]["groups"][0]["visibility"]["condition"]["value"] == "A&amp;B &copy;"
    assert (
        result["survey"]["fields"][4]["source"]["originDetails"][0]["questionRelevanceExpression"]
        == expression
    )
