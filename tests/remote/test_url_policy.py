import pytest

from limesurvey_connector.remote import LimeSurveyUrlError, validate_limesurvey_url


def test_accepts_an_explicitly_allowed_remotecontrol_host():
    value = validate_limesurvey_url(
        "https://surveys.example.org/index.php/admin/remotecontrol/",
        allowed_hosts=("surveys.example.org",),
    )
    assert value == "https://surveys.example.org/index.php/admin/remotecontrol"


def test_accepts_localhost_only_when_local_development_is_explicitly_allowed():
    value = validate_limesurvey_url(
        "http://localhost/limesurvey/index.php/admin/remotecontrol",
        allowed_hosts=("host.docker.internal",),
        allow_insecure_http=True,
    )
    assert value == "http://localhost/limesurvey/index.php/admin/remotecontrol"


@pytest.mark.parametrize(
    "value",
    [
        "file:///etc/passwd",
        "https://user:secret@surveys.example.org/admin/remotecontrol",
        "https://surveys.example.org/admin/remotecontrol#fragment",
        "https://surveys.example.org/internal/metadata",
        "https://untrusted.example.org/admin/remotecontrol",
        "http://surveys.example.org/admin/remotecontrol",
    ],
)
def test_rejects_urls_outside_the_outbound_policy(value):
    with pytest.raises(LimeSurveyUrlError):
        validate_limesurvey_url(value, allowed_hosts=("surveys.example.org",))


def test_without_allowed_hosts_private_addresses_are_rejected():
    with pytest.raises(LimeSurveyUrlError, match="private or local"):
        validate_limesurvey_url("https://127.0.0.1/admin/remotecontrol")
