import pytest

from limesurvey_connector.limesurvey.normalization import (
    SurveyStructureContractError,
    validate_survey_load_result,
    validate_survey_structure,
)
from tests.support.conformance import validation_cases

CASES = validation_cases()


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_contract_check_matches_reference_cases(case):
    validate = (
        validate_survey_structure
        if case["contract"] == "SurveyStructure"
        else validate_survey_load_result
    )
    if case["success"]:
        assert validate(case["value"]) is case["value"]
    else:
        with pytest.raises(SurveyStructureContractError) as caught:
            validate(case["value"])
        assert [error["path"] for error in caught.value.errors] == [
            issue["path"] for issue in case["issues"]
        ]


def test_misspelled_property_is_named_in_the_error():
    invalid = {
        "surveyStructureVersion": "2.1.0",
        "id": "123",
        "fields": [
            {
                "id": "1",
                "code": "Q1",
                "type": "short-text",
                "label": "Name",
                "renderign": {"widget": "text-input"},
            }
        ],
    }
    with pytest.raises(SurveyStructureContractError, match="renderign"):
        validate_survey_structure(invalid)
