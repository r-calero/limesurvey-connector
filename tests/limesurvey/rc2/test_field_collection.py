"""Collection behavior across normalization boundaries, without a live LimeSurvey."""

from xml.sax.saxutils import escape

import pytest

from limesurvey_connector.limesurvey.normalization import (
    build_survey_structure,
    survey_structure_from_lss,
)
from limesurvey_connector.limesurvey.normalization.survey_settings import normalize_groups


def test_collection_keeps_order_diagnostics_and_source_counts_when_fields_are_skipped():
    result = build_survey_structure(
        {
            "survey": {"sid": "synthetic-survey"},
            "groups": [
                {"gid": "20", "group_order": "9"},
                {"gid": "10", "group_order": "3"},
            ],
            "questions": [
                {"qid": "200", "gid": "20", "title": "SAME", "type": "S"},
                {"qid": "300", "gid": "20", "title": "TAIL", "type": "S", "question_order": "1"},
                {"qid": "100", "gid": "10", "title": "SAME", "type": "M", "mandatory": "Y"},
                {"qid": "102", "parent_qid": "100", "title": "B", "question_order": "1"},
                {"qid": "101", "parent_qid": "100", "title": "A", "question_order": "0"},
                {"qid": "110", "gid": "10", "title": " ", "type": "S", "question_order": "1"},
                {"qid": "901", "parent_qid": "900", "title": "ORPHAN"},
                {
                    "qid": "120",
                    "gid": "10",
                    "title": "UNSUPPORTED",
                    "type": "*",
                    "question_order": "2",
                    "attributes": {"em_validation_q": "self.NAOK > 0"},
                },
            ],
        }
    )

    assert [
        (field["id"], field["code"], field["order"]) for field in result["survey"]["fields"]
    ] == [
        ("100", "SAME", 0),
        ("300", "TAIL", 1),
    ]
    assert [option["code"] for option in result["survey"]["fields"][0]["options"]] == ["A", "B"]
    assert [(group["id"], group["order"]) for group in result["survey"]["groups"]] == [
        ("10", 0),
        ("20", 1),
    ]
    assert [(issue["code"], issue["fieldId"]) for issue in result["issues"]] == [
        ("MISSING_PARENT", "901"),
        ("MISSING_QUESTION_CODE", "110"),
        ("UNSUPPORTED_TYPE", "120"),
        ("DUPLICATE_QUESTION_CODE", "200"),
    ]
    assert result["sourceMetrics"] == {
        "topLevelQuestions": 5,
        "childQuestions": 3,
        "integratedChildren": 2,
        "detectedTypes": ["*", "M", "S"],
        "conditionsDetected": 0,
        "validationQuestions": 2,
    }


def test_group_order_does_not_reorder_source_diagnostics():
    issues = []
    groups = normalize_groups(
        [
            {"gid": "20", "group_order": "9", "grelevance": "UNKNOWN_B == 1"},
            {"gid": "10", "group_order": "3", "grelevance": "UNKNOWN_A == 1"},
        ],
        {},
        issues,
    )

    assert [(group["id"], group["order"]) for group in groups] == [("10", 0), ("20", 1)]
    assert [issue["details"]["sourceExpression"] for issue in issues] == [
        "UNKNOWN_B == 1",
        "UNKNOWN_A == 1",
    ]


def child_relevance_result(source, expression):
    if source == "lss":
        return survey_structure_from_lss(
            f"""<document><LimeSurveyDocType>Survey</LimeSurveyDocType>
            <DBVersion>708</DBVersion><surveys><rows><row><sid>123</sid><language>es</language></row></rows></surveys>
            <questions><rows><row><qid>100</qid><parent_qid>0</parent_qid><title>Q1</title>
            <type>Q</type><question>Question</question></row></rows></questions>
            <subquestions><rows><row><qid>101</qid><parent_qid>100</parent_qid><title>SQ1</title>
            <question>Item</question><relevance>{escape(expression)}</relevance></row></rows></subquestions>
            </document>""".encode()
        )
    return build_survey_structure(
        {
            "survey": {"sid": "123", "language": "es"},
            "questions": [
                {
                    "qid": "100",
                    "parent_qid": "0",
                    "title": "Q1",
                    "type": "Q",
                    "question": "Question",
                },
                {
                    "qid": "101",
                    "parent_qid": "100",
                    "title": "SQ1",
                    "question": "Item",
                    "relevance": expression,
                },
            ],
        }
    )


@pytest.mark.parametrize("source", ["lss", "remotecontrol"])
@pytest.mark.parametrize("expression", ["  unsupported(Q1_SQ1) > 0  ", "0", "false"])
@pytest.mark.parametrize("locale", ["es-MX", "en-US"])
def test_child_relevance_is_preserved_in_a_warning_without_hiding_parent(
    source, expression, locale, monkeypatch
):
    monkeypatch.setenv("APP_LOCALE", locale)
    result = child_relevance_result(source, expression)
    assert len(result["issues"]) == 1
    issue = result["issues"][0]
    assert issue["code"] == "UNSUPPORTED_SOURCE_EXPRESSION"
    assert issue["level"] == "warning"
    assert (issue["fieldId"], issue["questionCode"]) == ("100", "Q1")
    assert issue["details"]["sourceExpression"] == expression
    assert "SQ1 (qid=101)" in issue["message"]
    assert ("no se ejecuta" if locale.startswith("es") else "is not executed") in issue["message"]
    assert "visibility" not in result["survey"]["fields"][0]
    assert result["survey"]["fields"][0]["subquestions"][0]["code"] == "SQ1"


@pytest.mark.parametrize("source", ["lss", "remotecontrol"])
@pytest.mark.parametrize("expression", ["", "  ", "1", "true", " TRUE "])
def test_unconditional_child_relevance_needs_no_warning(source, expression):
    assert child_relevance_result(source, expression)["issues"] == []
