"""Fixed K limits apply to each numeric box or the sum of its boxes."""

from limesurvey_connector.limesurvey.normalization import (
    build_survey_structure,
    survey_structure_from_lss,
)


def test_k_keeps_numeric_subquestions_and_converts_fixed_sum():
    result = build_survey_structure(
        {
            "survey": {"sid": "123", "language": "es"},
            "questions": [
                {
                    "qid": "100",
                    "sid": "123",
                    "parent_qid": "0",
                    "title": "PESOS",
                    "type": "K",
                    "question": "Peso de cada hijo",
                    "mandatory": "Y",
                    "attributes": {"maximum_chars": "4", "equals_num_value": "10"},
                },
                {
                    "qid": "101",
                    "sid": "123",
                    "parent_qid": "100",
                    "title": "SQ001",
                    "question": "Primero",
                    "question_order": "0",
                },
                {
                    "qid": "102",
                    "sid": "123",
                    "parent_qid": "100",
                    "title": "SQ002",
                    "question": "Segundo",
                    "question_order": "1",
                },
            ],
        }
    )
    field = result["survey"]["fields"][0]
    assert field["type"] == "multiple-input"
    assert field["source"]["nativeType"] == "K"
    assert field["responseValidation"] == {"maxLength": 4, "numericText": True, "sumEquals": 10.0}
    assert [(item["id"], item["code"]) for item in field["subquestions"]] == [
        ("101", "SQ001"),
        ("102", "SQ002"),
    ]
    assert [
        issue["details"]["rule"]
        for issue in result["issues"]
        if issue["code"] == "INVALID_VALIDATION"
    ] == []


def test_k_without_subquestions_is_omitted():
    result = build_survey_structure(
        {
            "survey": {"sid": "123"},
            "questions": [{"qid": "100", "parent_qid": "0", "title": "EMPTY", "type": "K"}],
        }
    )
    assert result["survey"]["fields"] == []
    assert any(
        issue["code"] == "EMPTY_OPTIONS" and issue["details"]["omitted"]
        for issue in result["issues"]
    )


def test_k_converts_fixed_item_limits_and_integer_rule_but_warns_about_slider():
    result = build_survey_structure(
        {
            "survey": {"sid": "123"},
            "questions": [
                {
                    "qid": "100",
                    "parent_qid": "0",
                    "title": "WEIGHTS",
                    "type": "K",
                    "attributes": {
                        "min_num_value_n": "1",
                        "max_num_value_n": "20",
                        "num_value_int_only": "1",
                        "slider_layout": "1",
                    },
                },
                {"qid": "101", "parent_qid": "100", "title": "SQ001", "question": "First"},
            ],
        }
    )
    field = result["survey"]["fields"][0]
    assert field["responseValidation"] == {
        "numericText": True,
        "itemMin": 1.0,
        "itemMax": 20.0,
        "integer": True,
    }
    assert {issue["details"]["rule"] for issue in result["issues"]} == {"slider_layout"}


def test_k_dynamic_and_conflicting_bounds_remain_visible_as_warnings():
    result = build_survey_structure(
        {
            "survey": {"sid": "123"},
            "questions": [
                {
                    "qid": "100",
                    "parent_qid": "0",
                    "title": "WEIGHTS",
                    "type": "K",
                    "attributes": {
                        "min_num_value_n": "10",
                        "max_num_value_n": "2",
                        "min_num_value": "Q1.NAOK",
                        "equals_num_value": "5",
                    },
                },
                {"qid": "101", "parent_qid": "100", "title": "SQ001", "question": "First"},
            ],
        }
    )
    assert result["survey"]["fields"][0]["responseValidation"] == {
        "numericText": True,
        "sumEquals": 5.0,
    }
    assert {
        issue["details"]["rule"]
        for issue in result["issues"]
        if issue["code"] == "INVALID_VALIDATION"
    } == {"min_num_value_n", "max_num_value_n", "min_num_value"}


def test_k_in_lss_uses_the_same_subquestion_codes():
    xml = b"""<document><LimeSurveyDocType>Survey</LimeSurveyDocType><DBVersion>348</DBVersion>
      <surveys><rows><row><sid>123</sid><language>es</language></row></rows></surveys>
      <questions><rows><row><qid>100</qid><sid>123</sid><parent_qid>0</parent_qid>
        <title>WEIGHTS</title><type>K</type><question>Weights</question></row></rows></questions>
      <subquestions><rows><row><qid>101</qid><sid>123</sid><parent_qid>100</parent_qid>
        <title>SQ001</title><question>First</question></row></rows></subquestions></document>"""
    result = survey_structure_from_lss(xml)
    field = result["survey"]["fields"][0]
    assert field["source"]["nativeType"] == "K"
    assert field["responseValidation"]["numericText"] is True
    assert field["subquestions"][0]["code"] == "SQ001"
