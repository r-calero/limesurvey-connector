import pytest
import requests
from citric.exceptions import LimeSurveyStatusError, RPCInterfaceNotEnabledError

from limesurvey_connector.remote.errors import classify, is_unreachable


def test_unreachable_by_type_and_text():
    assert is_unreachable(TimeoutError("timeout"))
    assert is_unreachable(requests.ConnectionError("x"))
    assert is_unreachable(Exception("HTTPConnectionPool: Max retries exceeded with url"))


@pytest.mark.parametrize(
    ("error", "code", "status"),
    [
        (Exception("connection refused while calling remote"), "LS_UNREACHABLE", 503),
        (Exception("boom"), "LS_UNKNOWN", 500),
        (Exception("Invalid session key"), "LS_SESSION_EXPIRED", 401),
        (Exception("INVALID SESSION KEY"), "LS_SESSION_EXPIRED", 401),
        (LimeSurveyStatusError("No permission"), "LS_REMOTE_REJECTED_REQUEST", 502),
        (RPCInterfaceNotEnabledError(), "LS_REMOTE_CONTROL_UNAVAILABLE", 502),
    ],
)
def test_classification(error, code, status):
    classified = classify(error, "listing surveys")
    assert classified.code == code
    assert classified.status_code == status


def test_unreachable_detail_names_the_operation():
    assert "listing surveys" in classify(Exception("connection refused"), "listing surveys").detail
