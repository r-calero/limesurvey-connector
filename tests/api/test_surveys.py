from tests.support.fake_limesurvey import SURVEY_ID

BASE = f"/v1/limesurvey/surveys/{SURVEY_ID}"


def test_list_surveys_is_cached(client, session_headers, gateway):
    first = client.get("/v1/limesurvey/surveys", headers=session_headers)
    second = client.get("/v1/limesurvey/surveys", headers=session_headers)
    assert first.json() == second.json()
    assert gateway.backends["remote-key-1"].calls.count("list_surveys") == 1


def test_structure(client, session_headers, gateway):
    body = client.get(f"{BASE}/structure", headers=session_headers).json()
    assert body["survey"]["id"] == str(SURVEY_ID)
    assert body["responseState"]["active"] is True
    client.get(f"{BASE}/structure", headers=session_headers)
    assert gateway.backends["remote-key-1"].calls.count("get_survey_properties") == 1


def test_field_detail(client, session_headers):
    body = client.get(f"{BASE}/fields/SATISF", headers=session_headers).json()
    assert body["field"]["type"] == "matrix"
    assert [entry["responseKey"] for entry in body["dictionary"]] == ["SATISF_R1", "SATISF_R2"]
    missing = client.get(f"{BASE}/fields/NOPE", headers=session_headers)
    assert missing.status_code == 404
    assert missing.json()["code"] == "QUESTION_NOT_FOUND"


def test_dictionary_json_csv_and_system_fields(client, session_headers):
    dictionary = client.get(f"{BASE}/dictionary", headers=session_headers)
    consent = next(
        field for field in dictionary.json()["fields"] if field["responseKey"] == "CONSIENTE"
    )
    assert "external_consent" in consent["aliases"]
    assert dictionary.headers["etag"]
    with_system = client.get(
        f"{BASE}/dictionary?includeSystemFields=true", headers=session_headers
    ).json()
    assert with_system["fields"][0]["responseKey"] == "id"
    question = client.get(f"{BASE}/dictionary?questionCode=APOYOS", headers=session_headers).json()
    assert {field["questionCode"] for field in question["fields"]} == {"APOYOS"}
    csv = client.get(f"{BASE}/dictionary", headers={**session_headers, "Accept": "text/csv"})
    assert csv.headers["content-type"].startswith("text/csv")
    assert csv.headers["x-dictionary-warning-count"] == "2"
    assert csv.text.startswith('"survey_id","qid"')


def test_responses_json_and_csv(client, session_headers):
    dataset = client.get(f"{BASE}/responses", headers=session_headers).json()
    assert dataset["surveyId"] == str(SURVEY_ID)
    assert len(dataset["responses"]) == 2
    csv = client.get(f"{BASE}/responses?format=csv", headers=session_headers)
    assert csv.text.startswith("id,NOMBRE")
    assert csv.headers["cache-control"] == "no-store"


def test_translated_responses_keep_system_columns(client, session_headers):
    body = client.get(f"{BASE}/responses/translated?language=es", headers=session_headers).json()
    first = body["responses"][0]
    assert first["responseId"] == "1"
    fields = {field["responseKey"]: field for field in first["fields"]}
    assert fields["CONSIENTE"]["displayValue"] == "Sí"
    assert fields["submitdate"]["dataType"] == "date"
    assert not [issue for issue in body["issues"] if issue["code"] == "UNKNOWN_RESPONSE_KEY"]


def test_response_query_validation(client, session_headers, settings):
    bad_range = client.get(
        f"{BASE}/responses?fromResponseId=5&toResponseId=2", headers=session_headers
    )
    assert bad_range.json()["code"] == "INVALID_RESPONSE_RANGE"
    too_many = ",".join(f"F{index}" for index in range(settings.remote.responses_max_fields + 1))
    assert (
        client.get(f"{BASE}/responses?fields={too_many}", headers=session_headers).json()["code"]
        == "TOO_MANY_RESPONSE_FIELDS"
    )
    assert (
        client.get(
            f"{BASE}/responses?completionStatus=partial", headers=session_headers
        ).status_code
        == 400
    )


def test_response_export_rate_limit(client, session_headers, settings):
    statuses = [
        client.get(f"{BASE}/responses", headers=session_headers).status_code
        for _ in range(settings.responses_rate_limit_per_minute + 1)
    ]
    assert statuses[-1] == 429


def test_dictionary_timing_fields_and_limesurvey_names(client, session_headers):
    body = client.get(f"{BASE}/dictionary?includeTimingFields=true", headers=session_headers).json()
    keys = [field["responseKey"] for field in body["fields"]]
    assert keys[:3] == ["interviewtime", "groupTime10", "groupTime20"]
    assert "CUIDADOS_SQ001comment" in keys
    assert "CUIDADOS_SQ001_comment" not in keys
