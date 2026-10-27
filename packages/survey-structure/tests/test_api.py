import pytest

from survey_structure import (
    SURVEY_STRUCTURE_VERSION,
    SurveyStructureValidationError,
    field_response_keys,
    parse_survey_load_result,
    parse_survey_response_record,
    parse_survey_structure,
    safe_parse_survey_structure,
    validation_pattern_source,
)

TEXT = {"id": "q1", "code": "Q01", "type": "short-text", "label": "Name"}


def survey(*fields, **extra):
    return {
        "surveyStructureVersion": SURVEY_STRUCTURE_VERSION,
        "id": "s1",
        "fields": list(fields),
        **extra,
    }


def test_parse_returns_data_in_contract_key_order():
    value = {"fields": [TEXT], "id": "s1", "surveyStructureVersion": "2.1.0"}
    assert list(parse_survey_structure(value)) == ["surveyStructureVersion", "id", "fields"]


def test_previous_contract_version_is_rejected():
    result = safe_parse_survey_structure({"contractVersion": "2.0.0", "id": "s1", "fields": []})
    assert not result.success
    assert {issue["code"] for issue in result.issues} == {"invalid_literal", "unrecognized_keys"}


def test_parse_raises_with_every_issue():
    with pytest.raises(SurveyStructureValidationError) as caught:
        parse_survey_structure(survey(TEXT, {**TEXT, "id": "q2"}))
    assert caught.value.issues[0]["params"]["reason"] == "duplicate-response-key"
    assert "fields.1" in str(caught.value)


def test_safe_parse_does_not_raise():
    result = safe_parse_survey_structure({"id": "s1"})
    assert result.success is False
    assert result.data is None
    assert {tuple(issue["path"]) for issue in result.issues} == {
        ("surveyStructureVersion",),
        ("fields",),
    }


def test_load_result_parser():
    result = parse_survey_load_result({"survey": survey(TEXT), "issues": []})
    assert result["survey"]["fields"][0]["code"] == "Q01"


def test_numbers_follow_json_semantics():
    assert safe_parse_survey_structure(survey({**TEXT, "order": 1.0})).success
    assert not safe_parse_survey_structure(survey({**TEXT, "order": True})).success


def test_response_keys_cover_children_and_other():
    custom = {
        "id": "c1",
        "code": "BLOCK",
        "type": "custom",
        "label": "Block",
        "childrenFields": [{**TEXT, "parentId": "c1"}],
    }
    choice = {
        "id": "q2",
        "code": "Q02",
        "type": "multiple-choice-with-comments",
        "label": "Pick",
        "options": [{"code": "A", "label": "A"}],
        "other": {
            "code": "OTH",
            "label": "Other",
            "textResponseKey": "Q02_other",
            "commentResponseKey": "Q02_oc",
        },
    }
    assert field_response_keys(custom) == ["BLOCK_Q01"]
    assert field_response_keys(choice) == ["Q02_A", "Q02_A_comment", "Q02_other", "Q02_oc"]


def test_explicit_comment_keys_replace_the_generated_ones():
    listed = {
        "id": "q3",
        "code": "Q03",
        "type": "list-with-comment",
        "label": "List",
        "options": [{"code": "A", "label": "A"}],
        "commentResponseKey": "Q03_comment",
    }
    checks = {
        "id": "q4",
        "code": "Q04",
        "type": "multiple-choice-with-comments",
        "label": "Pick",
        "options": [{"code": "A", "label": "A", "commentResponseKey": "Q04_Acomment"}],
    }
    assert field_response_keys(listed) == ["Q03", "Q03_comment"]
    assert field_response_keys(checks) == ["Q04_A", "Q04_Acomment"]


def test_response_records_accept_json_values_only():
    record = {"Q01": "a", "Q02": [1, None, {"x": True}]}
    assert parse_survey_response_record(record) == record
    with pytest.raises(SurveyStructureValidationError):
        parse_survey_response_record({"Q01": float("nan")})


def test_pattern_source_is_returned_as_written():
    assert validation_pattern_source({"responseFormatPattern": "\\d+"}) == "\\d+"
    assert validation_pattern_source({}) == ""
