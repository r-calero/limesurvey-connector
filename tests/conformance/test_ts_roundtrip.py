import pytest

from tests.support.conformance import NODE, load_result_goldens, ts_validate, validation_cases

pytestmark = [
    pytest.mark.conformance,
    pytest.mark.ts_roundtrip,
    pytest.mark.skipif(NODE is None, reason="Node is not installed."),
]

CASES = validation_cases()
LOAD_RESULTS = [(name, golden) for name, golden in load_result_goldens() if golden["ok"]]


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_vendored_validator_agrees_with_goldens(case):
    result = ts_validate(case["contract"], case["value"])
    assert result["success"] is case["success"]
    if not case["success"]:
        assert [issue["path"] for issue in result["issues"]] == [
            issue["path"] for issue in case["issues"]
        ]


@pytest.mark.parametrize(
    "golden", [golden for _, golden in LOAD_RESULTS], ids=[name for name, _ in LOAD_RESULTS]
)
def test_reference_load_results_satisfy_the_typescript_contract(golden):
    assert ts_validate("SurveyLoadResult", golden["result"]) == {"success": True}


VALID_CASES = [case for case in CASES if case["success"]]


@pytest.mark.parametrize("case", VALID_CASES, ids=[case["name"] for case in VALID_CASES])
def test_python_parsed_documents_satisfy_the_typescript_contract(case):
    from survey_structure import (
        safe_parse_survey_load_result,
        safe_parse_survey_structure,
    )

    parse = (
        safe_parse_survey_structure
        if case["contract"] == "SurveyStructure"
        else safe_parse_survey_load_result
    )
    result = parse(case["value"])
    assert ts_validate(case["contract"], result.data) == {"success": True}
