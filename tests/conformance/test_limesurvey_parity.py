import pytest

from limesurvey_connector.limesurvey.normalization import (
    SurveyStructureSourceError,
    build_survey_structure,
    survey_structure_from_lss,
)
from tests.support.conformance import (
    CONFORMANCE,
    FIXTURES,
    NODE,
    load_result_goldens,
    read_json,
    ts_validate,
    with_limesurvey_column_names,
)

pytestmark = pytest.mark.conformance

INTENTIONAL = read_json(CONFORMANCE / "intentional-changes.json")["changes"]


def _effective(cases):
    """Prefer a golden produced with an intentional change's option over the plain one for the same input."""
    changed = {golden["input"] for _, golden in cases if golden.get("change")}
    return [
        (name, golden)
        for name, golden in cases
        if golden.get("change") or golden["input"] not in changed
    ]


def _expected_error_message(golden):
    """lss-dbversion-355 adds 355 to the accepted versions listed in this error."""
    return golden["error"]["message"].replace("348, 623,", "348, 355, 623,")


GOLDEN_CASES = _effective(list(load_result_goldens()))


def _normalize(golden):
    if golden["input"].startswith("remote-api/"):
        from limesurvey_connector.remote import LimeSurveyClient
        from tests.support.fake_limesurvey import FakeCitric

        client = LimeSurveyClient(
            "https://surveys.example.org/index.php/admin/remotecontrol", "ana", validate_url=False
        )
        client._client = FakeCitric()
        return client.get_survey_load_result(read_json(FIXTURES / golden["input"])["surveyId"])
    source = FIXTURES / golden["input"]
    if source.suffix == ".lss":
        return survey_structure_from_lss(source.read_bytes())
    fixture = read_json(source)
    return build_survey_structure(fixture["payload"], fixture.get("sourceFormat", "remotecontrol"))


@pytest.mark.parametrize(("name", "golden"), GOLDEN_CASES, ids=[name for name, _ in GOLDEN_CASES])
def test_normalization_matches_reference(name, golden):
    if golden["ok"]:
        assert _normalize(golden) == with_limesurvey_column_names(golden["result"])
        return
    with pytest.raises(SurveyStructureSourceError) as caught:
        _normalize(golden)
    assert type(caught.value).__name__ == golden["error"]["type"]
    assert str(caught.value) == _expected_error_message(golden)


@pytest.mark.ts_roundtrip
@pytest.mark.skipif(NODE is None, reason="Node is not installed.")
@pytest.mark.parametrize(
    ("name", "golden"),
    [item for item in GOLDEN_CASES if item[1]["ok"]],
    ids=[n for n, g in GOLDEN_CASES if g["ok"]],
)
def test_python_normalization_satisfies_the_typescript_contract(name, golden):
    assert ts_validate("SurveyLoadResult", _normalize(golden)) == {"success": True}
