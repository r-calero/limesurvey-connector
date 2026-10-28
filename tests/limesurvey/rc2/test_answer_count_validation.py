"""Source count limits must not disappear behind a complete-conversion metric."""

import pytest

from limesurvey_connector.limesurvey.normalization import build_survey_structure


def payload(native, attributes, required=False, rows=3, row_relevance=None):
    questions = [
        {
            "qid": "1",
            "title": "Q",
            "type": native,
            "mandatory": "Y" if required else "N",
            "attributes": attributes,
            "answeroptions": {"A": {"answer": "A"}},
        }
    ]
    questions += [
        {
            "qid": str(index + 2),
            "title": f"R{index}",
            "parent_qid": "1",
            "type": "T",
            "scale_id": "0",
            **({"relevance": row_relevance} if row_relevance else {}),
        }
        for index in range(rows)
    ]
    if native == ";":
        questions += [
            {
                "qid": str(index + 100),
                "title": f"C{index}",
                "parent_qid": "1",
                "type": "T",
                "scale_id": "1",
            }
            for index in range(2)
        ]
    return {"survey": {"sid": "synthetic"}, "questions": questions}


@pytest.mark.parametrize(("native", "unit"), [("Q", "inputs")])
@pytest.mark.parametrize(("rule", "value"), [("min_answers", "1"), ("max_answers", "1")])
def test_unconverted_real_count_limits_remain_explicit(native, unit, rule, value):
    result = build_survey_structure(payload(native, {rule: value}))
    field = result["survey"]["fields"][0]
    assert not field["required"]
    assert "responseValidation" not in field
    assert result["sourceMetrics"]["validationQuestions"] == 1
    assert len(result["issues"]) == 1
    issue = result["issues"][0]
    assert (issue["code"], issue["fieldId"], issue["questionCode"]) == (
        "INVALID_VALIDATION",
        "1",
        "Q",
    )
    assert issue["details"] == {"rule": rule, "sourceValue": value}
    assert f"answered {unit}" in issue["message"]
    key = "minimumAnswersExpression" if rule == "min_answers" else "maximumAnswersExpression"
    assert field["source"]["originDetails"][0]["nativeValidation"][key] == value


@pytest.mark.parametrize(("native", "capacity"), [(";", 6), ("F", 3), ("Q", 3)])
def test_required_and_capacity_already_preserve_redundant_limits(native, capacity):
    result = build_survey_structure(
        payload(native, {"min_answers": str(capacity), "max_answers": str(capacity)}, required=True)
    )
    assert result["issues"] == []
    assert result["survey"]["fields"][0]["required"]
    assert result["sourceMetrics"]["validationQuestions"] == 1
    assert (
        build_survey_structure(payload(native, {"min_answers": "0", "max_answers": str(capacity)}))[
            "issues"
        ]
        == []
    )


def test_optional_rows_do_not_make_a_real_minimum_redundant():
    result = build_survey_structure(
        payload("F", {"min_answers": "1"}, required=True, row_relevance="0")
    )
    assert result["issues"] == []
    assert result["survey"]["fields"][0]["responseValidation"] == {"minAnswers": 1}


def test_dynamic_limits_are_diagnosed_once_and_zero_maximum_is_not_discarded():
    result = build_survey_structure(payload(";", {"min_answers": "LIMIT.NAOK", "max_answers": "0"}))
    assert [issue["details"]["rule"] for issue in result["issues"]] == ["min_answers"]
    assert result["survey"]["fields"][0]["responseValidation"] == {"maxAnswers": 0}


@pytest.mark.parametrize(
    ("native", "rule", "value", "portable"),
    [(";", "min_answers", "1", "minAnswers"), ("F", "max_answers", "3", "maxAnswers")],
)
def test_observed_matrix_limits_are_functional_without_changing_mandatory(
    native, rule, value, portable
):
    result = build_survey_structure(payload(native, {rule: value}, rows=7))
    field = result["survey"]["fields"][0]
    assert result["issues"] == []
    assert field["required"] is False
    assert field["responseValidation"] == {portable: int(value)}
    assert result["sourceMetrics"]["validationQuestions"] == 1
    source_key = "minimumAnswersExpression" if rule == "min_answers" else "maximumAnswersExpression"
    assert field["source"]["originDetails"][0]["nativeValidation"][source_key] == value


def test_fractional_bounds_preserve_integer_count_comparison_and_negative_max_is_diagnosed():
    result = build_survey_structure(payload(";", {"min_answers": "1.5", "max_answers": "2.5"}))
    assert result["survey"]["fields"][0]["responseValidation"] == {"minAnswers": 2, "maxAnswers": 2}
    result = build_survey_structure(payload("F", {"max_answers": "-1"}))
    assert result["issues"][0]["details"] == {"rule": "max_answers", "sourceValue": "-1"}


def test_single_choice_and_multi_choice_existing_validation_is_unchanged():
    single = build_survey_structure(
        payload("L", {"min_answers": "1", "max_answers": "1"}, required=True, rows=0)
    )
    assert single["issues"] == []
    multiple = build_survey_structure(payload("M", {"min_answers": "1", "max_answers": "2"}))
    assert multiple["issues"] == []
    assert multiple["survey"]["fields"][0]["responseValidation"] == {
        "minSelections": 1,
        "maxSelections": 2,
    }


def test_native_h_does_not_inherit_an_unverified_answer_count_diagnostic():
    result = build_survey_structure(payload("H", {"min_answers": "1", "max_answers": "1"}))
    assert result["issues"] == []
    assert result["sourceMetrics"]["validationQuestions"] == 1
    native = result["survey"]["fields"][0]["source"]["originDetails"][0]["nativeValidation"]
    assert native == {"minimumAnswersExpression": "1", "maximumAnswersExpression": "1"}
