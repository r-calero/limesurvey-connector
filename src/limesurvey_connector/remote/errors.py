"""LimeSurvey access errors with stable codes (port of limesurvey-rc2-api ``error_mapper``)."""

from __future__ import annotations

import re

import requests
from citric.exceptions import (
    InvalidJSONResponseError,
    LimeSurveyApiError,
    LimeSurveyStatusError,
    RPCInterfaceNotEnabledError,
)


class LimeSurveyError(Exception):
    """Base error; ``code`` is stable and ``status_code`` suggests an HTTP status."""

    code = "LS_UNKNOWN"
    status_code = 500

    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class LimeSurveyUrlError(LimeSurveyError, ValueError):
    code = "LIMESURVEY_URL_NOT_ALLOWED"
    status_code = 400


class LimeSurveyLoginError(LimeSurveyError):
    code = "LS_LOGIN_FAILED"
    status_code = 401


class LimeSurveySessionExpiredError(LimeSurveyError):
    code = "LS_SESSION_EXPIRED"
    status_code = 401


class LimeSurveyUnreachableError(LimeSurveyError):
    code = "LS_UNREACHABLE"
    status_code = 503


class LimeSurveyRemoteControlUnavailableError(LimeSurveyError):
    code = "LS_REMOTE_CONTROL_UNAVAILABLE"
    status_code = 502


class LimeSurveyRequestRejectedError(LimeSurveyError):
    code = "LS_REMOTE_REJECTED_REQUEST"
    status_code = 502


class LimeSurveyTimeoutError(LimeSurveyError, TimeoutError):
    code = "LS_TIMEOUT"
    status_code = 504

    def __init__(self, message: str, code: str = "LS_TIMEOUT") -> None:
        super().__init__(message)
        self.code = code


class SurveyNotFoundError(LimeSurveyError, LookupError):
    code = "LS_SURVEY_NOT_FOUND"
    status_code = 404


class SurveyLanguageNotAvailableError(LimeSurveyError, ValueError):
    """The requested language, or a translation it needs, is not in the survey."""

    code = "LS_LANGUAGE_NOT_AVAILABLE"
    status_code = 400


class ResponseExportTooLargeError(LimeSurveyError):
    code = "LS_RESPONSE_EXPORT_TOO_LARGE"
    status_code = 413


class InvalidResponseExportError(LimeSurveyError):
    code = "INVALID_LS_RESPONSE_EXPORT"
    status_code = 502


_UNREACHABLE = (
    "connection refused",
    "failed to establish a new connection",
    "max retries exceeded",
    "all connection attempts failed",
    "network is unreachable",
    "connection aborted",
    "name or service not known",
    "failed to resolve",
    "temporary failure in name resolution",
    "nodename nor servname provided",
    "read timed out",
    "connect timeout",
    "timed out",
)
_SESSION_EXPIRED = (
    r"invalid\s+session\s+key",
    r"session\s+key[^.]*invalid",
    r"session[^.]*expired",
)


def is_unreachable(error: BaseException) -> bool:
    if isinstance(error, TimeoutError | requests.Timeout | requests.ConnectionError):
        return True
    text = str(error).lower()
    return any(pattern in text for pattern in _UNREACHABLE)


def classify(error: BaseException, context: str) -> LimeSurveyError:
    """Translate a Citric, network or LimeSurvey failure into a ``LimeSurveyError``."""
    if isinstance(error, LimeSurveyError):
        return error
    text = str(error)
    error_code = str(getattr(error, "error_code", "") or "").casefold()
    structured_session = isinstance(error, LimeSurveyStatusError) and any(
        token in error_code for token in ("invalid_session", "session_expired", "invalidsession")
    )
    if structured_session or any(
        re.search(pattern, text.casefold()) for pattern in _SESSION_EXPIRED
    ):
        return LimeSurveySessionExpiredError(
            "LimeSurvey session expired. Please login again.", text
        )
    if is_unreachable(error):
        return LimeSurveyUnreachableError("LimeSurvey remote is unreachable.", f"{context}: {text}")
    if isinstance(error, RPCInterfaceNotEnabledError | InvalidJSONResponseError):
        return LimeSurveyRemoteControlUnavailableError(
            "LimeSurvey RemoteControl 2 is disabled or did not return JSON.", text
        )
    if isinstance(error, LimeSurveyStatusError | LimeSurveyApiError):
        return LimeSurveyRequestRejectedError(
            "LimeSurvey rejected the RemoteControl 2 request.", text
        )
    return LimeSurveyError(f"Unexpected LimeSurvey error while {context}.", text)
