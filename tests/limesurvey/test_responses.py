from limesurvey_connector.limesurvey.responses import (
    csv_to_canonical_responses,
    default_response_id_headers,
    system_columns,
    system_columns_in,
    with_system_fields,
)
from survey_data_dictionary import build_survey_dictionary

SURVEY = {
    "surveyStructureVersion": "2.1.0",
    "id": "s1",
    "fields": [{"id": "q1", "code": "Q1", "type": "short-text", "label": "Name"}],
}


def test_csv_reader_defaults_keep_every_column():
    dictionary = build_survey_dictionary(SURVEY)
    result = csv_to_canonical_responses("id,submitdate,Q1\n7,2026-09-01,Ana\n", dictionary)
    assert result["responseIds"] == ["7"]
    assert result["responses"] == [{"Q1": "Ana"}]
    assert [value["sourceKey"] for value in result["unmappedValues"][0]] == ["submitdate"]


def test_system_fields_yield_to_survey_codes():
    dictionary = build_survey_dictionary(
        {**SURVEY, "fields": [{**SURVEY["fields"][0], "code": "seed"}]}
    )
    codes = [field["responseKey"] for field in with_system_fields(dictionary)["fields"]]
    assert codes.count("seed") == 1
    assert "id" in default_response_id_headers(dictionary)


def test_system_columns_catalog():
    assert {column["code"] for column in system_columns()} >= {
        "id",
        "submitdate",
        "lastpage",
        "token",
    }
    assert [column["code"] for column in system_columns_in(["Fecha en que se envió", "Q1"])] == [
        "submitdate"
    ]


def test_load_lss_accepts_paths_and_bytes(tmp_path):
    from limesurvey_connector.limesurvey import load_lss
    from tests.support.conformance import FIXTURES

    source = FIXTURES / "lss" / "display-message-question.lss"
    assert load_lss(source) == load_lss(source.read_bytes())
    assert load_lss(str(source), language="es")["survey"]["language"] == "es"
