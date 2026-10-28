import json

import pytest
import requests

from limesurvey_connector.limesurvey.normalization import SurveyStructureSourceError
from limesurvey_connector.remote import (
    InvalidResponseExportError,
    LimeSurveyClient,
    LimeSurveySessionExpiredError,
    RemoteSettings,
    ResponseExportTooLargeError,
    SurveyLanguageNotAvailableError,
    decode_response_export,
)
from tests.support.conformance import GOLDENS, read_json, with_limesurvey_column_names
from tests.support.fake_limesurvey import FIXTURE, SURVEY_ID, FakeCitric


def make_client(backend=None, **settings):
    client = LimeSurveyClient(
        "https://surveys.example.org/index.php/admin/remotecontrol",
        "ana",
        validate_url=False,
        settings=RemoteSettings(**settings),
    )
    client._client = backend or FakeCitric()
    return client


GOLDEN = read_json(GOLDENS / "limesurvey" / "remote-api" / "all-types.json")
# The reference with its question-level multiscale option (intentional change dual-scale-question-level).
CHANGED = read_json(
    GOLDENS / "limesurvey" / "remote-api" / "all-types.dual-scale-question-level.json"
)


def test_survey_load_matches_the_reference_loader():
    expected = with_limesurvey_column_names(CHANGED["result"])
    assert make_client().get_survey_load_result(SURVEY_ID) == expected


def test_response_export_matches_the_reference_loader():
    assert make_client().export_responses(SURVEY_ID, language="es") == GOLDEN["responseDataset"]


def test_transient_errors_are_retried():
    backend = FakeCitric()
    failures = {"left": 2}
    original = backend.list_questions

    def flaky(*args, **kwargs):
        if failures["left"]:
            failures["left"] -= 1
            raise requests.ConnectionError("reset")
        return original(*args, **kwargs)

    backend.list_questions = flaky
    loaded = make_client(backend, backoff_base=0.001, backoff_max=0.001).get_survey_load_result(
        SURVEY_ID
    )
    assert loaded["survey"]["fields"]


def test_expired_session_is_classified():
    with pytest.raises(LimeSurveySessionExpiredError):
        make_client(FakeCitric(expired=True)).list_surveys()


def test_field_and_dictionary_helpers():
    client = make_client()
    assert client.get_field(SURVEY_ID, "NOPE") is None
    assert client.get_field(SURVEY_ID, "EDAD")["field"]["type"] == "number"
    dictionary = client.get_dictionary(SURVEY_ID, include_system_fields=True)
    assert dictionary["fields"][0]["responseKey"] == "id"


def test_translate_responses():
    translated = make_client().translate_responses(SURVEY_ID)
    assert len(translated["responses"]) == 2


def test_context_manager_closes_only_its_own_session(monkeypatch):
    backend = FakeCitric()
    monkeypatch.setattr("limesurvey_connector.remote._citric.create_client", lambda *args: backend)
    with LimeSurveyClient(
        "https://x.example/admin/remotecontrol", "ana", "pw", validate_url=False
    ) as client:
        assert client.session_key == "remote-key"
    assert backend.closed


def test_response_export_checks():
    assert decode_response_export(b"a,b\n", 1, "csv", None, 100) == b"a,b\n"
    with pytest.raises(ResponseExportTooLargeError):
        decode_response_export(b"x" * 10, 1, "csv", None, 5)
    with pytest.raises(InvalidResponseExportError):
        decode_response_export(b"{", 1, "json", None, 100)
    with pytest.raises(InvalidResponseExportError):
        decode_response_export(json.dumps({"responses": [1]}).encode(), 1, "json", None, 100)
    dataset = decode_response_export(
        json.dumps({"responses": [{"Q1": "A1"}]}).encode(), 7, "json", "es", 100
    )
    assert dataset == {"surveyId": "7", "language": "es", "responses": [{"Q1": "A1"}]}


def test_empty_question_groups_are_skipped():
    backend = FakeCitric()
    groups = backend.list_groups

    def with_empty_group(*args, **kwargs):
        return [
            *groups(*args, **kwargs),
            {"gid": "99", "group_name": "Solo texto", "group_order": "9"},
        ]

    backend.list_groups = with_empty_group
    loaded = make_client(backend).get_survey_load_result(SURVEY_ID)
    assert [field["code"] for field in loaded["survey"]["fields"]] == [
        field["code"] for field in CHANGED["result"]["survey"]["fields"]
    ]
    assert [group["id"] for group in loaded["survey"]["groups"]][-1] == "99"


class _OrphanChildCitric(FakeCitric):
    """LimeSurvey lists subquestion 1091 under a group that no longer exists."""

    def list_questions(self, survey_id, group_id=None, language=None):
        return [
            row
            for row in super().list_questions(survey_id, group_id, language)
            if row["qid"] != "1091"
        ]

    def get_question_properties(self, question_id, *, settings=None, language=None):
        result = super().get_question_properties(question_id, settings=settings, language=language)
        if str(question_id) == "109":
            result["subquestions"] = {"1091": {"title": "SQ001"}}
        if str(question_id) == "1091":
            # Real properties of a subquestion repeat its row, including its survey.
            row = next(row for row in FIXTURE["questionsByGroup"]["10"] if row["qid"] == "1091")
            result.update({**row, "sid": str(SURVEY_ID)})
        return result


def test_subquestions_under_a_missing_group_are_recovered():
    expected = make_client().get_survey_load_result(SURVEY_ID)["survey"]
    recovered = make_client(_OrphanChildCitric()).get_survey_load_result(SURVEY_ID)["survey"]
    field = next(item for item in recovered["fields"] if item["source"]["questionId"] == "109")
    assert field == next(
        item for item in expected["fields"] if item["source"]["questionId"] == "109"
    )


def test_a_recovered_subquestion_must_belong_to_its_parent():
    class Foreign(_OrphanChildCitric):
        def get_question_properties(self, question_id, *, settings=None, language=None):
            result = super().get_question_properties(
                question_id, settings=settings, language=language
            )
            if str(question_id) == "1091":
                result["parent_qid"] = "999"
            return result

    with pytest.raises(SurveyStructureSourceError, match="does not belong"):
        make_client(Foreign()).get_survey_load_result(SURVEY_ID)


def test_unavailable_language_is_rejected_before_loading_questions():
    backend = FakeCitric()
    with pytest.raises(SurveyLanguageNotAvailableError) as caught:
        make_client(backend).get_survey_load_result(SURVEY_ID, "fr")
    assert caught.value.code == "LS_LANGUAGE_NOT_AVAILABLE"
    assert "list_questions" not in backend.calls
