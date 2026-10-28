"""Synthetic RC2/LSS fixtures: no remote access or persisted forms."""

import pytest

from limesurvey_connector.limesurvey.normalization import (
    build_survey_structure,
    survey_structure_from_lss,
)
from limesurvey_connector.limesurvey.normalization.condition_references import (
    build_condition_references,
)
from limesurvey_connector.limesurvey.normalization.field_normalizer import normalize_field
from tests.limesurvey.rc2.test_fixed_question_types import as_lss


@pytest.mark.parametrize("source", ["remotecontrol", "lss"])
@pytest.mark.parametrize(
    ("language", "labels"),
    [("es-MX", ["Aumenta", "Igual", "Disminuye"]), ("en", ["Increase", "Same", "Decrease"])],
)
def test_e_fixed_values_and_matrix_row_relevance(source, language, labels):
    questions = [
        {"qid": "1", "title": "GATE", "type": "S"},
        {"qid": "2", "title": "D1", "type": "E", "mandatory": "Y"},
        {
            "qid": "3",
            "title": "SQ001",
            "type": "T",
            "parent_qid": "2",
            "relevance": 'GATE.NAOK == "show"',
        },
        {"qid": "4", "title": "SQ002", "type": "T", "parent_qid": "2", "relevance": "0"},
        {"qid": "5", "title": "FOLLOW", "type": "S", "relevance": 'D1_SQ001.NAOK == "I"'},
        {"qid": "6", "title": "COUNT", "type": "S", "relevance": "count(that.D1.NAOK) >= 1"},
    ]
    payload = {
        "survey": {"sid": "123", "language": language},
        "groups": [{"gid": "10", "group_name": "Synthetic", "language": language}],
        "questions": [
            {"gid": "10", "language": language, "parent_qid": "0", "question": q["title"], **q}
            for q in questions
        ],
    }
    result = (
        build_survey_structure(payload)
        if source == "remotecontrol"
        else survey_structure_from_lss(as_lss(payload))
    )
    assert result["issues"] == []
    matrix = result["survey"]["fields"][1]["matrix"]
    assert matrix["mode"] == "single"
    assert [column["code"] for column in matrix["columns"]] == ["I", "S", "D"]
    assert [column["label"] for column in matrix["columns"]] == labels
    assert matrix["rows"][0]["visibility"]["condition"]["responseReference"] == {
        "fieldCode": "GATE"
    }
    assert matrix["rows"][1]["visibility"]["condition"] == {"type": "constant", "value": False}
    assert result["sourceMetrics"]["conditionsDetected"] == 4
    assert result["survey"]["fields"][2]["visibility"]["condition"]["value"] == "I"
    assert result["survey"]["fields"][3]["visibility"]["condition"]["type"] == "answered-count"


def test_nonfunctional_controls_are_omitted_but_other_only_is_preserved():
    payload = {
        "survey": {"sid": "123"},
        "questions": [
            {"qid": "1", "title": "NO_ROWS", "type": "E"},
            {"qid": "2", "title": "NO_OPTIONS", "type": "L"},
            {"qid": "3", "title": "OTHER_ONLY", "type": "M", "other": "Y"},
            {"qid": "4", "title": "NO_SUBQUESTIONS", "type": "Q"},
        ],
    }
    result = build_survey_structure(payload)
    assert [field["code"] for field in result["survey"]["fields"]] == ["OTHER_ONLY"]
    assert [issue["code"] for issue in result["issues"]] == ["EMPTY_OPTIONS"] * 4
    assert [issue["details"]["omitted"] for issue in result["issues"]] == [True, True, False, True]


def test_unsupported_row_expression_warns_on_owning_question():
    result = build_survey_structure(
        {
            "survey": {"sid": "123"},
            "questions": [
                {"qid": "1", "title": "MATRIX", "type": "E"},
                {
                    "qid": "2",
                    "title": "ROW",
                    "type": "T",
                    "parent_qid": "1",
                    "relevance": "unknown(42)",
                },
            ],
        }
    )
    issue = result["issues"][0]
    assert (issue["fieldId"], issue["questionCode"]) == ("1", "MATRIX")
    assert issue["details"] == {
        "sourceExpression": "unknown(42)",
        "rowCode": "ROW",
        "childQuestionId": "2",
    }
    assert "visibility" not in result["survey"]["fields"][0]["matrix"]["rows"][0]


@pytest.mark.parametrize(
    "expression",
    [
        'this.NAOK == "I" AND M_R.NAOK == "explicit"',
        'M_R.NAOK == "explicit" AND !is_empty(this.NAOK)',
        'count(self.NAOK) >= 1 AND M_R.NAOK == "explicit"',
    ],
)
def test_row_macros_never_resolve_to_a_colliding_real_question(expression):
    questions = [
        {"qid": "1", "title": "M", "type": "E"},
        {"qid": "2", "title": "R", "type": "T", "parent_qid": "1", "relevance": expression},
        {"qid": "3", "title": "M_R", "type": "S"},
    ]
    # Isolate conversion: this synthetic E/scalar pair also has a conflicting flat
    # response key M_R, independently rejected by the whole-survey contract.
    references = build_condition_references(questions, "123")
    issues = []
    field = normalize_field(questions[0], [questions[1]], "123", "es", issues, references)
    issue = issues[0]
    assert issue["code"] == "UNSUPPORTED_SOURCE_EXPRESSION"
    assert (issue["fieldId"], issue["questionCode"]) == ("1", "M")
    assert issue["details"] == {
        "sourceExpression": expression,
        "rowCode": "R",
        "childQuestionId": "2",
    }
    assert "visibility" not in field["matrix"]["rows"][0]
    # Explicit references retain their ordinary meaning; the index is not altered.
    questions[1]["relevance"] = 'M_R.NAOK == "explicit"'
    issues = []
    explicit = normalize_field(questions[0], [questions[1]], "123", "es", issues, references)
    assert issues == []
    assert explicit["matrix"]["rows"][0]["visibility"]["condition"]["responseReference"] == {
        "fieldCode": "M_R"
    }


def test_row_self_count_does_not_count_a_colliding_multi_input_question():
    result = build_survey_structure(
        {
            "survey": {"sid": "123"},
            "questions": [
                {"qid": "1", "title": "M", "type": "E"},
                {
                    "qid": "2",
                    "title": "R",
                    "type": "T",
                    "parent_qid": "1",
                    "relevance": "count(self.NAOK) >= 1 AND !is_empty(M_R_A.NAOK)",
                },
                {"qid": "3", "title": "M_R", "type": "Q"},
                {"qid": "4", "title": "A", "type": "T", "parent_qid": "3"},
            ],
        }
    )
    assert result["issues"][0]["code"] == "UNSUPPORTED_SOURCE_EXPRESSION"
    assert result["issues"][0]["details"]["rowCode"] == "R"
    assert "visibility" not in result["survey"]["fields"][0]["matrix"]["rows"][0]


@pytest.mark.parametrize("row_relevance", ["6", "true"])
def test_source_counts_do_not_report_true_relevance_or_zero_answer_minimum_as_lost(row_relevance):
    result = build_survey_structure(
        {
            "survey": {"sid": "123"},
            "groups": [{"gid": "10", "grelevance": "6"}],
            "questions": [
                {
                    "qid": "1",
                    "gid": "10",
                    "title": "MATRIX",
                    "type": "E",
                    "relevance": "6",
                    "attributes": {"min_answers": "0", "minimum_answer": "0"},
                },
                {
                    "qid": "2",
                    "gid": "10",
                    "title": "ROW",
                    "type": "T",
                    "parent_qid": "1",
                    "relevance": row_relevance,
                },
                {
                    "qid": "3",
                    "gid": "10",
                    "title": "NUMERIC",
                    "type": "N",
                    "attributes": {"min_num_value": "0"},
                },
                {
                    "qid": "4",
                    "gid": "10",
                    "title": "NUMERIC_ALIAS",
                    "type": "N",
                    "attributes": {"minimum_answer": "0"},
                },
            ],
        }
    )
    assert result["issues"] == []
    assert result["sourceMetrics"]["conditionsDetected"] == 3
    assert result["sourceMetrics"]["validationQuestions"] == 2
    field = result["survey"]["fields"][0]
    for owner in (result["survey"]["groups"][0], field, field["matrix"]["rows"][0]):
        assert owner["visibility"]["condition"] == {"type": "constant", "value": True}
    assert [f["responseValidation"]["min"] for f in result["survey"]["fields"][1:]] == [0, 0]
