"""Construction and resumption of Citric clients (port of limesurvey-rc2-api ``citric_session_adapter``)."""

from __future__ import annotations

import json
from typing import Any

import requests
from citric import Client
from citric.session import Session


class TimeoutHttpSession(requests.Session):
    """Apply a default timeout and disable redirects for every RemoteControl request."""

    def __init__(self, timeout: tuple[float, float]) -> None:
        super().__init__()
        self._timeout = timeout

    def request(
        self, method: str | bytes, url: str | bytes, *args: Any, **kwargs: Any
    ) -> requests.Response:
        kwargs.setdefault("timeout", self._timeout)
        kwargs.setdefault("allow_redirects", False)
        verb = method.decode("ascii") if isinstance(method, bytes) else method
        return super().request(verb, url, *args, **kwargs)


def create_client(url: str, username: str, password: str, timeout: tuple[float, float]) -> Client:
    return Client(url, username, password, requests_session=TimeoutHttpSession(timeout))


def resume_client(url: str, session_key: str, timeout: tuple[float, float]) -> Client:
    """Attach Citric 2.3 to a previously issued session key.

    Citric has no public constructor for this; private attributes are touched only here,
    and the dependency is pinned to 2.3.x.
    """
    session = object.__new__(Session)
    session.url = url
    http = TimeoutHttpSession(timeout)
    http.headers["User-Agent"] = Session.USER_AGENT
    session._session = http
    session._encoder = json.JSONEncoder
    setattr(session, "_Session__key", session_key)  # noqa: B010
    setattr(session, "_Session__closed", False)  # noqa: B010
    client = object.__new__(Client)
    setattr(client, "_Client__session", session)  # noqa: B010
    setattr(client, "_Client__server_version", None)  # noqa: B010
    return client
