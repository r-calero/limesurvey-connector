"""Diagnose verified native restrictions without claiming they are executed."""

import pytest

from limesurvey_connector.limesurvey.normalization import build_survey_structure


@pytest.mark.parametrize(
    ("native_type", "rule", "value", "original_key"),
    [
        ("D", "date_min", "2021-01-01", "minimumDateExpression"),
        ("D", "date_max", "2026-12-31", "maximumDateExpression"),
    ],
)
def test_fixed_date_bounds_are_preserved_and_converted(native_type, rule, value, original_key):
    result = build_survey_structure(
        {
            "survey": {"sid": "synthetic-survey", "language": "es"},
            "questions": [
                {
                    "qid": "question-1",
                    "title": "ANSWER",
                    "type": native_type,
                    "question": "Answer",
                    "attributes": {rule: value},
                }
            ],
        }
    )
    field = result["survey"]["fields"][0]
    assert field["source"]["originDetails"][0]["nativeValidation"][original_key] == value
    assert result["sourceMetrics"]["validationQuestions"] == 1
    assert result["issues"] == []
    assert field["responseValidation"]["dateMin" if rule == "date_min" else "dateMax"] == value


@pytest.mark.parametrize(
    "attributes",
    [
        {},
        {"maximum_chars": "0"},
        {"date_min": "", "date_max": ""},
        {"hide_tip": "1", "time_limit_action": "3", "time_limit_disable_next": "1"},
    ],
)
def test_inactive_or_presentation_settings_do_not_claim_a_lost_validation(attributes):
    result = build_survey_structure(
        {
            "survey": {"sid": "synthetic-survey", "language": "es"},
            "questions": [
                {
                    "qid": "question-1",
                    "title": "ANSWER",
                    "type": "S",
                    "question": "Answer",
                    "attributes": attributes,
                }
            ],
        }
    )
    assert all(issue["code"] == "UNCONVERTED_SOURCE_PROPERTY" for issue in result["issues"])
    assert result["sourceMetrics"]["validationQuestions"] == 0


@pytest.mark.parametrize(
    ("native_type", "attribute", "value", "code"),
    [
        ("S", "time_limit", "5", "UNSUPPORTED_TIMER"),
        ("S", "preg", "/[/", "INVALID_VALIDATION"),
        ("N", "preg", r"/\A[0-9].*\z/", "INVALID_VALIDATION"),
    ],
)
def test_unsupported_behavior_retains_originals_and_counts_the_affected_question(
    native_type, attribute, value, code
):
    question = {
        "qid": "question-1",
        "title": "ANSWER",
        "type": native_type,
        "question": "Answer",
        "attributes": {attribute: value},
    }
    if attribute == "preg":
        question["preg"] = question["attributes"].pop("preg")
    if attribute == "time_limit":
        question["attributes"].update(time_limit_action="3", time_limit_disable_prev="1")
    result = build_survey_structure({"survey": {"sid": "test"}, "questions": [question]})
    issue = result["issues"][0]
    assert len(result["issues"]) == 1
    assert issue["code"] == code
    assert issue["questionCode"] == "ANSWER"
    assert issue["details"]["rule"] == attribute
    assert issue["details"].get("sourceValue", issue["details"].get("sourceExpression")) == value
    originals = result["survey"]["fields"][0]["source"]["originDetails"][0]["unconvertedAttributes"]
    assert originals[attribute] == value
    if attribute == "time_limit":
        assert originals == {
            "time_limit": "5",
            "time_limit_action": "3",
            "time_limit_disable_prev": "1",
        }
    assert result["sourceMetrics"]["conditionsDetected"] == (1 if attribute == "hidden" else 0)
    assert result["sourceMetrics"]["validationQuestions"] == (0 if attribute == "hidden" else 1)


@pytest.mark.parametrize(("value", "expected_count"), [("1", 1), ("0", 0)])
def test_numbers_only_counts_a_source_validation_without_other_rules(value, expected_count):
    result = build_survey_structure(
        {
            "survey": {"sid": "test"},
            "questions": [
                {
                    "qid": "1",
                    "title": "ANSWER",
                    "type": "S",
                    "mandatory": "N",
                    "attributes": {"numbers_only": value},
                }
            ],
        }
    )
    assert result["sourceMetrics"]["validationQuestions"] == expected_count
    assert bool(
        result["survey"]["fields"][0].get("responseValidation", {}).get("numericText")
    ) == bool(expected_count)
    assert result["issues"] == []


def test_numbers_only_and_question_image_survive_without_a_lost_rule_warning():
    result = build_survey_structure(
        {
            "survey": {"sid": "test", "language": "es"},
            "source": {"remoteUrl": "https://example.org/admin/remotecontrol"},
            "questions": [
                {
                    "qid": "question-1",
                    "title": "ANSWER",
                    "type": "S",
                    "question": 'Escribe un número <img src="/upload/photo.jpg" alt="Ejemplo">',
                    "attributes": {"numbers_only": "1", "time_limit": "6"},
                }
            ],
        }
    )
    field = result["survey"]["fields"][0]
    assert field["responseValidation"]["numericText"] is True
    assert field["images"] == [{"url": "https://example.org/upload/photo.jpg", "alt": "Ejemplo"}]
    assert result["sourceMetrics"]["validationQuestions"] == 1
    assert [issue["details"]["rule"] for issue in result["issues"]] == ["time_limit"]


def test_question_images_do_not_preserve_executable_urls():
    from limesurvey_connector.limesurvey.normalization.text_sanitizer import question_images

    html = '<img src="javascript:alert(1)"><img src="data:image/png;base64,AAAA"><img src="https://example.org/photo.jpg" alt="Foto">'
    assert question_images(html) == [{"url": "https://example.org/photo.jpg", "alt": "Foto"}]


def test_unconverted_filters_randomization_and_exclusive_option_are_reported():
    result = build_survey_structure(
        {
            "survey": {"sid": "test"},
            "groups": [{"gid": "10", "group_name": "General", "randomization_group": "mix"}],
            "questions": [
                {
                    "qid": "1",
                    "gid": "10",
                    "title": "SERVICES",
                    "type": "M",
                    "question": "Services",
                    "attributes": {
                        "array_filter": "CHOICE",
                        "array_filter_exclude": "HIDDEN",
                        "random_group": "mix",
                        "random_order": "1",
                        "exclusive_option": "B",
                        "exclude_all_others": "B",
                        "assessment_value": "1",
                        "other_numbers_only": "1",
                        "answer_order": "random",
                        "subquestion_order": "alphabetical",
                    },
                },
                {
                    "qid": "2",
                    "gid": "10",
                    "parent_qid": "1",
                    "title": "A",
                    "type": "M",
                    "question": "A",
                },
                {
                    "qid": "3",
                    "gid": "10",
                    "parent_qid": "1",
                    "title": "B",
                    "type": "M",
                    "question": "B",
                },
            ],
        }
    )
    rules = {
        issue["details"]["rule"]
        for issue in result["issues"]
        if issue["code"] == "INVALID_VALIDATION"
    }
    assert rules == {
        "array_filter",
        "array_filter_exclude",
        "random_order",
        "assessment_value",
        "other_numbers_only",
        "answer_order",
        "subquestion_order",
    }
    originals = result["survey"]["fields"][0]["source"]["originDetails"][0]["unconvertedAttributes"]
    assert (
        next(
            option for option in result["survey"]["fields"][0]["options"] if option["code"] == "B"
        )["exclusive"]
        is True
    )
    assert "exclusive_option" not in originals


@pytest.mark.parametrize("capacity", ["1", "2", "3", "0"])
def test_ranking_capacity_is_converted_without_removing_options(capacity):
    result = build_survey_structure(
        {
            "survey": {"sid": "test"},
            "questions": [
                {
                    "qid": "question-1",
                    "title": "RANK",
                    "type": "R",
                    "question": "Rank",
                    "answeroptions": {"A": {"answer": "A"}, "B": {"answer": "B"}},
                    "attributes": {"max_subquestions": capacity},
                }
            ],
        }
    )
    assert not result["issues"]
    field = result["survey"]["fields"][0]
    assert len(field["options"]) == 2
    assert field.get("responseValidation", {}).get("maxSelections") == (int(capacity) or None)


@pytest.mark.parametrize("other", ["Y", "N"])
@pytest.mark.parametrize("mandatory", ["Y", "N"])
def test_other_comment_rule_requires_an_actual_other_option(other, mandatory):
    result = build_survey_structure(
        {
            "survey": {"sid": "test"},
            "questions": [
                {
                    "qid": "question-1",
                    "title": "CHOICE",
                    "type": "L",
                    "question": "Choice",
                    "other": other,
                    "mandatory": mandatory,
                    "answeroptions": {"A": {"answer": "A"}},
                    "attributes": {"other_comment_mandatory": "1"},
                }
            ],
        }
    )
    assert not result["issues"]
    field = result["survey"]["fields"][0]
    assert field.get("other", {}).get("textRequired", False) == (other == "Y" and mandatory == "Y")


def test_permanent_hiding_is_converted_without_a_lost_condition_warning():
    result = build_survey_structure(
        {
            "survey": {"sid": "test"},
            "questions": [
                {
                    "qid": "1",
                    "title": "HIDDEN",
                    "type": "S",
                    "question": "Hidden",
                    "attributes": {"hidden": "1"},
                }
            ],
        }
    )
    assert result["survey"]["fields"][0]["rendering"]["hidden"] is True
    assert result["issues"] == []


def test_unknown_attribute_is_reported_and_preserved():
    result = build_survey_structure(
        {
            "survey": {"sid": "test"},
            "questions": [
                {
                    "qid": "1",
                    "title": "ANSWER",
                    "type": "S",
                    "question": "Answer",
                    "attributes": {"future_rule": "active"},
                }
            ],
        }
    )
    assert result["issues"][0]["code"] == "UNCONVERTED_SOURCE_PROPERTY"
    assert result["issues"][0]["details"] == {
        "propertyName": "future_rule",
        "sourceValue": "active",
    }
    assert (
        result["survey"]["fields"][0]["source"]["originDetails"][0]["unconvertedAttributes"][
            "future_rule"
        ]
        == "active"
    )
