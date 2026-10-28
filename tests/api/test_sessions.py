import jwt

from tests.api.conftest import LIMESURVEY_URL, OTHER_API_KEY
from tests.support.fake_limesurvey import SURVEY_ID


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_api_key_required(client):
    response = client.get("/v1/contract")
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CLIENT_CREDENTIAL"


def test_contract_and_compatibility(client, api_headers):
    assert client.get("/v1/contract", headers=api_headers).json()[
        "acceptedSurveyStructureVersions"
    ] == ["2.1.0"]
    assert (
        "acceptedDatabaseSchemaVersions"
        in client.get("/v1/compatibility", headers=api_headers).json()
    )


def test_open_session_issues_a_token_without_secrets(client, api_headers, gateway):
    response = client.post(
        "/v1/limesurvey/sessions",
        headers=api_headers,
        json={"url": LIMESURVEY_URL, "username": "ana", "password": "secret"},
    )
    body = response.json()
    assert response.status_code == 201
    assert body["tokenType"] == "Bearer"
    assert body["expiresIn"] == 1800
    header = jwt.get_unverified_header(body["accessToken"])
    claims = jwt.decode(body["accessToken"], options={"verify_signature": False})
    assert header["kid"] == "2026-09"
    assert set(claims) == {"iss", "aud", "sub", "jti", "iat", "nbf", "exp"}
    assert "ana" not in body["accessToken"]
    assert "remote-key" not in str(claims)
    assert gateway.logins == [(LIMESURVEY_URL, "ana")]


def test_disallowed_url_is_rejected_before_login(client, api_headers, gateway):
    response = client.post(
        "/v1/limesurvey/sessions",
        headers=api_headers,
        json={
            "url": "https://evil.example.com/index.php/admin/remotecontrol",
            "username": "ana",
            "password": "secret",
        },
    )
    assert response.status_code == 400
    assert response.json()["code"] == "LIMESURVEY_URL_NOT_ALLOWED"
    assert gateway.logins == []


def test_failed_login(client, api_headers):
    response = client.post(
        "/v1/limesurvey/sessions",
        headers=api_headers,
        json={"url": LIMESURVEY_URL, "username": "ana", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "LS_LOGIN_FAILED"


def test_login_rate_limit(client, api_headers, settings):
    body = {"url": LIMESURVEY_URL, "username": "ana", "password": "wrong"}
    statuses = [
        client.post("/v1/limesurvey/sessions", headers=api_headers, json=body).status_code
        for _ in range(9)
    ]
    assert statuses[-1] == 429


def test_token_is_required_and_checked(client, token):
    assert client.get("/v1/limesurvey/surveys").json()["code"] == "INVALID_SESSION"
    tampered = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
    assert (
        client.get(
            "/v1/limesurvey/surveys", headers={"Authorization": f"Bearer {tampered}"}
        ).status_code
        == 401
    )
    unsigned = jwt.encode(
        jwt.decode(token, options={"verify_signature": False}),
        "x" * 40,
        algorithm="HS256",
        headers={"kid": "2026-09"},
    )
    assert (
        client.get(
            "/v1/limesurvey/surveys", headers={"Authorization": f"Bearer {unsigned}"}
        ).status_code
        == 401
    )


def test_token_belongs_to_the_client_that_opened_it(client, settings, token, store):
    from limesurvey_connector.api.security import issue_token

    claims = jwt.decode(token, options={"verify_signature": False})
    other = issue_token(
        settings, client_id="client-other", subject=claims["sub"], session_id=claims["jti"]
    )
    response = client.get(
        "/v1/limesurvey/surveys", headers={"Authorization": f"Bearer {other.token}"}
    )
    assert response.status_code == 401


def test_close_session_revokes_the_token(client, session_headers, gateway):
    assert (
        client.delete("/v1/limesurvey/sessions/current", headers=session_headers).status_code == 204
    )
    assert gateway.backends["remote-key-1"].closed
    assert client.get("/v1/limesurvey/surveys", headers=session_headers).status_code == 401


def test_expired_remote_session_removes_the_local_one(client, session_headers, gateway):
    gateway.backends["remote-key-1"].expired = True
    response = client.get(f"/v1/limesurvey/surveys/{SURVEY_ID}/structure", headers=session_headers)
    assert response.status_code == 401
    assert response.json()["code"] == "LS_SESSION_EXPIRED"
    gateway.backends["remote-key-1"].expired = False
    assert (
        client.get("/v1/limesurvey/surveys", headers=session_headers).json()["code"]
        == "INVALID_SESSION"
    )


def test_second_api_key_opens_its_own_session(client):
    response = client.post(
        "/v1/limesurvey/sessions",
        headers={"X-Api-Key": OTHER_API_KEY},
        json={"url": LIMESURVEY_URL, "username": "ana", "password": "secret"},
    )
    assert response.status_code == 201


def test_spanish_messages(client):
    response = client.get("/v1/contract", headers={"Accept-Language": "es-MX,en;q=0.5"})
    assert response.json()["message"] == "Se requiere una credencial de API válida."
