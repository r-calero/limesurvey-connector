import pytest

from survey_data_dictionary import (
    ABSENT,
    SurveyDictionaryValidationError,
    build_survey_dictionary,
    dictionary_to_csv,
    map_tabular_dataset,
    translate_dataset,
    translate_response,
)

SURVEY = {
    "surveyStructureVersion": "2.1.0",
    "id": "s1",
    "language": "es",
    "fields": [
        {
            "id": "q1",
            "code": "Q1",
            "type": "single-choice",
            "label": "Consentimiento",
            "options": [{"code": "A1", "label": "Sí"}, {"code": "A2", "label": "No"}],
        },
        {"id": "q2", "code": "Q2", "type": "short-text", "label": "Nombre"},
    ],
}


def test_build_and_translate():
    dictionary = build_survey_dictionary(SURVEY, aliases={"consent": "Q1"})
    assert [field["responseKey"] for field in dictionary["fields"]] == ["Q1", "Q2"]
    assert dictionary["fields"][0]["aliases"] == ["Consentimiento", "consent"]
    response = translate_response(dictionary, {"consent": "A1", "Q2": "Ana"})
    by_key = {field["responseKey"]: field for field in response["fields"]}
    assert by_key["Q1"]["displayValue"] == "Sí"
    assert "responseId" not in response


def test_response_id_absent_versus_null():
    dictionary = build_survey_dictionary(SURVEY)
    result = translate_dataset(dictionary, [{}, {}], response_ids=[None, ABSENT])
    assert result["responses"][0]["responseId"] is None
    assert "responseId" not in result["responses"][1]


def test_strict_mode_raises_on_errors():
    duplicate = {**SURVEY, "fields": [SURVEY["fields"][0]]}
    build_survey_dictionary(duplicate, strict=True)
    with pytest.raises(SurveyDictionaryValidationError):
        build_survey_dictionary(
            duplicate,
            aliases={"": "Q1"},
            strict=True,
            source_issues=[
                {"level": "error", "code": "INVALID_SOURCE", "message": "broken"},
            ],
        )


def test_csv_neutralizes_formulas():
    dictionary = build_survey_dictionary(
        {**SURVEY, "fields": [{**SURVEY["fields"][1], "label": "=cmd"}]}
    )
    assert '"\'=cmd"' in dictionary_to_csv(dictionary)


def test_tabular_rows_keep_position():
    dictionary = build_survey_dictionary(SURVEY)
    result = map_tabular_dataset(dictionary, ["Q2", "Q2"], [["a", "b"]])
    assert result["responses"] == [{}]
    assert [value["columnIndex"] for value in result["unmappedValues"][0]] == [0, 1]


def test_dictionary_carries_the_survey_structure_version():
    assert build_survey_dictionary(SURVEY)["surveyStructureVersion"] == "2.1.0"


def test_explicit_comment_keys_and_numeric_text():
    survey = {
        **SURVEY,
        "fields": [
            {
                "id": "1",
                "code": "Q001",
                "type": "list-with-comment",
                "label": "Choice",
                "options": [{"code": "A", "label": "A"}],
                "commentResponseKey": "Q001_comment",
            },
            {
                "id": "2",
                "code": "Q002",
                "type": "multiple-choice-with-comments",
                "label": "Choices",
                "options": [{"code": "A1", "label": "A", "commentResponseKey": "Q002_A1comment"}],
            },
            {
                "id": "3",
                "code": "N",
                "type": "number",
                "responseValueType": "text",
                "label": "Number",
            },
        ],
    }
    dictionary = build_survey_dictionary(survey)
    keys = {field["responseKey"]: field for field in dictionary["fields"]}
    assert {"Q001_comment", "Q002_A1comment"} <= set(keys)
    assert keys["N"]["dataType"] == "string"
    cells = translate_response(dictionary, {"N": "0012"})["fields"]
    assert next(cell for cell in cells if cell["responseKey"] == "N")["displayValue"] == "0012"


def test_sgqa_aliases_only_for_limesurvey_and_scalar_source_aliases():
    field = {
        "id": "age",
        "code": "AGE",
        "type": "number",
        "label": "Edad",
        "groupId": "g",
        "source": {
            "platform": "custom",
            "questionId": "7",
            "responseAliases": [{"aliases": ["age"]}],
        },
    }
    custom = {**SURVEY, "groups": [{"id": "g", "order": 0}], "fields": [field]}
    entry = build_survey_dictionary(custom)["fields"][0]
    assert entry["aliases"] == ["Edad", "age"]
    limesurvey = {**custom, "source": {"platform": "limesurvey"}}
    assert "s1XgX7" in build_survey_dictionary(limesurvey)["fields"][0]["aliases"]
