from tests.support.conformance import FIXTURES, read_json

STRUCTURE = read_json(FIXTURES / "structures" / "extended-types.json")["value"]


def test_validate(client, api_headers):
    assert (
        client.post("/v1/survey-structure/validate", headers=api_headers, json=STRUCTURE).json()[
            "valid"
        ]
        is True
    )
    invalid = {**STRUCTURE, "fields": [STRUCTURE["fields"][0], STRUCTURE["fields"][0]]}
    response = client.post(
        "/v1/survey-structure/validate",
        headers={**api_headers, "Accept-Language": "es"},
        json=invalid,
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "INVALID_SURVEY_STRUCTURE"
    error = body["details"]["errors"][0]
    assert error["pointer"] == "/fields/1"
    assert error["rule"] == "duplicate-response-key"
    assert error["message"].startswith("La clave de respuesta")


def test_readiness(client, api_headers):
    draft = {"surveyStructureVersion": "2.1.0", "id": "d", "fields": []}
    assert (
        client.post("/v1/survey-structure/readiness", headers=api_headers, json=draft).json()[
            "ready"
        ]
        is False
    )


def test_generate_dictionary(client, api_headers):
    response = client.post(
        "/v1/dictionaries/generate?includeSystemFields=true", headers=api_headers, json=STRUCTURE
    )
    assert response.status_code == 200
    assert response.json()["fields"][0]["responseKey"] == "id"
    invalid = client.post("/v1/dictionaries/generate", headers=api_headers, json={"id": "x"})
    assert invalid.status_code == 400
    assert invalid.json()["code"] == "INVALID_REQUEST"


def test_lss_upload(client, api_headers):
    content = (FIXTURES / "lss" / "visibility-at-least-two-selections.lss").read_bytes()
    loaded = client.post(
        "/v1/survey-structures/from-lss",
        headers=api_headers,
        files={"file": ("survey.lss", content)},
    )
    assert loaded.status_code == 200
    assert loaded.json()["survey"]["surveyStructureVersion"] == "2.1.0"
    dictionary = client.post(
        "/v1/dictionaries/from-lss?format=csv",
        headers=api_headers,
        files={"file": ("survey.lss", content)},
    )
    assert dictionary.headers["content-type"].startswith("text/csv")


def test_lss_errors(client, api_headers):
    wrong_extension = client.post(
        "/v1/dictionaries/from-lss", headers=api_headers, files={"file": ("a.xml", b"<x/>")}
    )
    assert wrong_extension.status_code == 400
    broken = (FIXTURES / "lss" / "invalid-malformed-xml.lss").read_bytes()
    invalid = client.post(
        "/v1/dictionaries/from-lss", headers=api_headers, files={"file": ("a.lss", broken)}
    )
    assert invalid.status_code == 400
    assert invalid.json()["code"] == "INVALID_LSS_SOURCE"


def test_translate_records_and_csv(client, api_headers):
    dictionary = client.post(
        "/v1/dictionaries/generate", headers=api_headers, json=STRUCTURE
    ).json()
    records = client.post(
        "/v1/responses/translate",
        headers=api_headers,
        json={"dictionary": dictionary, "responses": [{"AGREE": True, "submitdate": "2026-09-01"}]},
    ).json()
    fields = {field["responseKey"]: field for field in records["responses"][0]["fields"]}
    assert fields["AGREE"]["displayValue"] == "Agreed"
    assert fields["submitdate"]["dataType"] == "date"
    csv = client.post(
        "/v1/responses/translate?format=csv",
        headers=api_headers,
        json={"dictionary": dictionary, "csv": "id,SCORE\n1,7\n", "csvOptions": {"delimiter": ","}},
    )
    assert csv.status_code == 200
    assert '"1","1","true","SCORE"' in csv.text


def test_translate_request_contract(client, api_headers):
    dictionary = client.post(
        "/v1/dictionaries/generate", headers=api_headers, json=STRUCTURE
    ).json()
    both = client.post(
        "/v1/responses/translate",
        headers=api_headers,
        json={"dictionary": dictionary, "responses": [], "csv": ""},
    )
    assert both.status_code == 400
    bad_dictionary = client.post(
        "/v1/responses/translate",
        headers=api_headers,
        json={"dictionary": {"surveyId": 1}, "responses": []},
    )
    assert bad_dictionary.json()["details"]["errors"][0]["path"].startswith("dictionary")
    malformed = client.post(
        "/v1/responses/translate",
        headers=api_headers,
        json={"dictionary": dictionary, "csv": 'a,b\n"x,1\n'},
    )
    assert malformed.status_code == 400


def test_body_limit(client, api_headers, settings):
    response = client.post(
        "/v1/survey-structure/validate",
        headers={**api_headers, "Content-Type": "application/json"},
        content=b" " * (settings.max_body_bytes + 1),
    )
    assert response.status_code == 413
    assert response.json()["code"] == "PAYLOAD_TOO_LARGE"
