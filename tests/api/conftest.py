import pytest
from fastapi.testclient import TestClient

from limesurvey_connector.api.app import create_app
from limesurvey_connector.api.settings import Settings, SurveyConfiguration
from limesurvey_connector.api.store import MemoryStore
from tests.support.fake_limesurvey import SURVEY_ID, FakeGateway

API_KEY = "k" * 40
OTHER_API_KEY = "o" * 40
LIMESURVEY_URL = "https://surveys.example.org/index.php/admin/remotecontrol"


@pytest.fixture
def settings():
    return Settings(
        environment="test",
        app_locale="en",
        api_keys=(API_KEY, OTHER_API_KEY),
        jwt_keys=(("2026-09", "s" * 40), ("2026-01", "r" * 40)),
        allowed_limesurvey_hosts=("surveys.example.org",),
        rate_limit_per_minute=1000,
        surveys={str(SURVEY_ID): SurveyConfiguration(aliases={"external_consent": "CONSIENTE"})},
    )


@pytest.fixture
def gateway():
    return FakeGateway()


@pytest.fixture
def store():
    return MemoryStore()


@pytest.fixture
def client(settings, store, gateway):
    with TestClient(create_app(settings, store=store, gateway=gateway)) as test_client:
        yield test_client


@pytest.fixture
def api_headers():
    return {"X-Api-Key": API_KEY}


@pytest.fixture
def token(client, api_headers):
    response = client.post(
        "/v1/limesurvey/sessions",
        headers=api_headers,
        json={"url": LIMESURVEY_URL, "username": "ana", "password": "secret"},
    )
    assert response.status_code == 201, response.text
    return response.json()["accessToken"]


@pytest.fixture
def session_headers(token):
    return {"Authorization": f"Bearer {token}"}
