import pytest

from limesurvey_connector.limesurvey import _papaparse
from limesurvey_connector.limesurvey.responses import (
    CsvParseError,
    translate_csv,
    translate_records,
    with_system_fields,
)
from survey_data_dictionary import (
    build_survey_dictionary,
    dictionary_to_csv,
    get_question_dictionary,
    map_tabular_dataset,
    safe_parse_survey_dictionary,
    safe_parse_survey_response_dataset,
    safe_parse_survey_response_record,
    translated_dataset_to_csv,
)
from survey_structure import SurveyStructureValidationError
from tests.support.conformance import FIXTURES, GOLDENS, read_json
from tests.support.dictionary_cases import as_json, dictionary_cases

pytestmark = pytest.mark.conformance

CASES = list(dictionary_cases())
IDS = [case.name for case in CASES]


def _items(key):
    return [(case, item) for case in CASES for item in case.fixture.get(key, [])]


def _dictionary(case):
    survey, source_issues = case.survey()
    return build_survey_dictionary(survey, aliases=case.aliases, source_issues=source_issues)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_dictionary_matches_reference(case):
    expected = case.golden("dictionary.json")
    survey, source_issues = case.survey()
    if not expected["ok"]:
        with pytest.raises(SurveyStructureValidationError) as caught:
            build_survey_dictionary(survey, aliases=case.aliases, source_issues=source_issues)
        assert caught.value.issues == expected["error"]["issues"]
        return
    dictionary = build_survey_dictionary(survey, aliases=case.aliases, source_issues=source_issues)
    assert dictionary == expected["result"]
    assert dictionary_to_csv(dictionary) == case.golden_text("dictionary.csv")
    for code in case.fixture.get("questionCodes", []):
        assert get_question_dictionary(dictionary, code) == case.golden(f"question-{code}.json")


@pytest.mark.parametrize(
    "case",
    [case for case in CASES if case.fixture.get("includeSystemFields")],
    ids=lambda case: case.name,
)
def test_dictionary_with_system_fields(case):
    extended = with_system_fields(_dictionary(case))
    assert {"change": "system-columns", "ok": True, "result": extended} == case.golden(
        "dictionary-system.json"
    )
    assert dictionary_to_csv(extended) == case.golden_text("dictionary-system.csv")


@pytest.mark.parametrize(
    ("case", "request_"),
    _items("translations"),
    ids=lambda item: getattr(item, "name", None) or item.get("name"),
)
def test_record_translation_matches_reference(case, request_):
    result = translate_records(
        _dictionary(case),
        request_["responses"],
        response_id_key=request_.get("responseIdKey"),
        response_ids=request_.get("responseIds"),
        ignored_keys=request_.get("ignoredKeys", []),
        unmapped_values=request_.get("unmappedValues"),
    )
    expected = case.golden(f"translate-{request_['name']}.json")
    expected.pop("change", None)
    assert {"ok": True, "result": as_json(result)} == expected
    assert translated_dataset_to_csv(result) == case.golden_text(
        f"translate-{request_['name']}.csv"
    )


@pytest.mark.parametrize(
    ("case", "request_"),
    _items("csv"),
    ids=lambda item: getattr(item, "name", None) or item.get("name"),
)
def test_csv_translation_matches_reference(case, request_):
    options = request_.get("options", {})
    expected = case.golden(f"csv-{request_['name']}.json")
    assert expected.pop("change") == "system-columns"
    arguments = {
        "delimiter": options.get("delimiter"),
        "ignored_headers": [*case.ignored_headers, *options.get("ignoredHeaders", [])],
        "missing_values": options.get("missingValues"),
        "format": options.get("format", "auto"),
        "response_id_header": options.get("responseIdHeader"),
    }
    text = (FIXTURES / request_["file"]).read_text(encoding="utf-8")
    if not expected["ok"]:
        with pytest.raises(CsvParseError) as caught:
            translate_csv(_dictionary(case), text, **arguments)
        assert str(caught.value) == expected["error"]["message"]
        return
    result = translate_csv(_dictionary(case), text, **arguments)
    assert {"ok": True, "result": as_json(result)} == expected
    assert translated_dataset_to_csv(result["translated"]) == case.golden_text(
        f"csv-{request_['name']}.csv"
    )


@pytest.mark.parametrize(
    ("case", "request_"),
    _items("tabular"),
    ids=lambda item: getattr(item, "name", None) or item.get("name"),
)
def test_tabular_mapping_matches_reference(case, request_):
    result = map_tabular_dataset(
        _dictionary(case),
        request_["headers"],
        request_["rows"],
        request_.get("ignoredHeaders", []),
        request_.get("missingValues", []),
        request_.get("responseIdHeaders", []),
    )
    assert {"ok": True, "result": as_json(result)} == case.golden(
        f"tabular-{request_['name']}.json"
    )


CSV_PARSE = read_json(GOLDENS / "data-dictionary-cases" / "csv-parse.json")
CSV_INPUTS = {
    case["name"]: case for case in read_json(FIXTURES / "data-dictionary-cases.json")["csv"]
}


@pytest.mark.parametrize("expected", CSV_PARSE, ids=[case["name"] for case in CSV_PARSE])
def test_csv_reader_matches_papaparse(expected):
    source = CSV_INPUTS[expected["name"]]
    parsed = _papaparse.parse(source["text"], source.get("delimiter"))
    assert parsed.data == expected["data"]
    assert [
        {key: value for key, value in vars(error).items() if value is not None}
        for error in parsed.errors
    ] == expected["errors"]
    assert parsed.linebreak == expected["linebreak"]


SCHEMA_CASES = read_json(GOLDENS / "data-dictionary-cases" / "schema-cases.json")
SCHEMA_PARSERS = {
    "SurveyDictionary": safe_parse_survey_dictionary,
    "SurveyResponseDataset": safe_parse_survey_response_dataset,
    "SurveyResponseRecord": safe_parse_survey_response_record,
}


@pytest.mark.parametrize("case", SCHEMA_CASES, ids=[case["name"] for case in SCHEMA_CASES])
def test_dictionary_schemas_match_reference(case):
    result = SCHEMA_PARSERS[case["contract"]](case["value"])
    assert result.success is case["success"]
    if case["success"]:
        assert result.data == case["data"]
    else:
        assert result.issues == case["issues"]
