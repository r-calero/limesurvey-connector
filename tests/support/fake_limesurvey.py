"""In-memory stand-in for Citric's client, answering with conformance/fixtures/remote-api/all-types.json."""

from __future__ import annotations

import copy
import json
from typing import Any

from citric.exceptions import LimeSurveyStatusError

from limesurvey_connector.remote import LimeSurveyClient
from tests.support.conformance import FIXTURES, read_json

FIXTURE = read_json(FIXTURES / "remote-api" / "all-types.json")
SURVEY_ID = FIXTURE["surveyId"]


class FakeSession:
    def __init__(self, key: str) -> None:
        self.key = key


class FakeCitric:
    """Implements the Citric methods used by ``LimeSurveyClient``."""

    def __init__(self, key: str = "remote-key", *, expired: bool = False) -> None:
        self.session = FakeSession(key)
        self.expired = expired
        self.closed = False
        self.calls: list[str] = []

    def _check(self, name: str) -> None:
        self.calls.append(name)
        if self.expired:
            raise LimeSurveyStatusError("Invalid session key")

    def list_surveys(self) -> list[dict[str, Any]]:
        self._check("list_surveys")
        return [{"sid": str(SURVEY_ID), "surveyls_title": "Encuesta sintética", "active": "Y"}]

    def get_survey_properties(self, survey_id: int, properties: Any = None) -> dict[str, Any]:
        self._check("get_survey_properties")
        return dict(FIXTURE["surveyProperties"])

    def get_language_properties(
        self, survey_id: int, *, settings: Any = None, language: Any = None
    ) -> dict[str, Any]:
        self._check("get_language_properties")
        return dict(FIXTURE["languageProperties"])

    def list_groups(self, survey_id: int, language: Any = None) -> list[dict[str, Any]]:
        self._check("list_groups")
        return copy.deepcopy(FIXTURE["groups"])

    def list_questions(
        self, survey_id: int, group_id: Any = None, language: Any = None
    ) -> list[dict[str, Any]]:
        self._check("list_questions")
        rows = copy.deepcopy(FIXTURE["questionsByGroup"].get(str(group_id), []))
        if not rows:
            # LimeSurvey reports an empty group as an error status, not an empty list.
            raise LimeSurveyStatusError("No questions found")
        return rows

    def get_question_properties(
        self, question_id: int, *, settings: Any = None, language: Any = None
    ) -> dict[str, Any]:
        self._check("get_question_properties")
        return copy.deepcopy(FIXTURE["questionProperties"][str(question_id)])

    def export_responses(
        self, survey_id: int, *, file_format: str = "json", **options: Any
    ) -> bytes:
        self._check("export_responses")
        if file_format == "csv":
            return b"id,NOMBRE\n1,Ana\n2,Luis\n"
        return json.dumps({"responses": FIXTURE["responses"]}).encode("utf-8")

    def close(self) -> None:
        self._check("close")
        self.closed = True


class FakeGateway:
    """Gateway whose clients are real ``LimeSurveyClient`` objects around ``FakeCitric``."""

    def __init__(self) -> None:
        self.backends: dict[str, FakeCitric] = {}
        self.logins: list[tuple[str, str]] = []
        self.fail_login = False

    def _client(self, url: str, username: str, key: str) -> LimeSurveyClient:
        client = LimeSurveyClient(url, username, validate_url=False)
        client._client = self.backends.setdefault(key, FakeCitric(key))  # type: ignore[assignment]
        return client

    def open(self, url: str, username: str, password: str) -> LimeSurveyClient:
        if self.fail_login or password != "secret":
            from limesurvey_connector.remote import LimeSurveyLoginError

            raise LimeSurveyLoginError("LimeSurvey login failed: Invalid user name or password")
        self.logins.append((url, username))
        return self._client(url, username, f"remote-key-{len(self.logins)}")

    def resume(self, session: Any) -> LimeSurveyClient:
        return self._client(session.lime_survey_url, session.username, session.remote_session_key)
