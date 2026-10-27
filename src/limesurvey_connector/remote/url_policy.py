"""Outbound policy for RemoteControl URLs (port of limesurvey-rc2-api ``limesurvey_url``)."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Iterable
from urllib.parse import urlsplit, urlunsplit

from limesurvey_connector.remote.errors import LimeSurveyUrlError

_LOCAL_ALIASES = {"localhost", "127.0.0.1", "host.docker.internal"}


def validate_limesurvey_url(
    value: str, *, allowed_hosts: Iterable[str] = (), allow_insecure_http: bool = False
) -> str:
    """Return a normalized RemoteControl URL or raise ``LimeSurveyUrlError`` before any request.

    Without ``allowed_hosts``, the host must resolve only to public addresses.
    """
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"}:
        raise LimeSurveyUrlError("LimeSurvey URL must use HTTP or HTTPS.")
    if parsed.scheme == "http" and not allow_insecure_http:
        raise LimeSurveyUrlError("LimeSurvey URL must use HTTPS.")
    if parsed.username or parsed.password:
        raise LimeSurveyUrlError("Credentials must not be embedded in the LimeSurvey URL.")
    if parsed.fragment:
        raise LimeSurveyUrlError("LimeSurvey URL must not contain a fragment.")
    if not parsed.hostname:
        raise LimeSurveyUrlError("LimeSurvey URL must contain a hostname.")
    path = parsed.path.rstrip("/")
    if not path.endswith("/admin/remotecontrol"):
        raise LimeSurveyUrlError(
            "LimeSurvey URL must point to the RemoteControl endpoint ending in /admin/remotecontrol."
        )
    hostname = parsed.hostname.lower().rstrip(".")
    trusted = {host.lower().rstrip(".") for host in allowed_hosts}
    allowed = hostname in trusted or (hostname in _LOCAL_ALIASES and bool(_LOCAL_ALIASES & trusted))
    if trusted and not allowed:
        raise LimeSurveyUrlError(f'LimeSurvey host "{hostname}" is not allowed.')
    if not trusted:
        _reject_non_public(hostname, parsed.port)
    netloc = f"{hostname}:{parsed.port}" if parsed.port else hostname
    return urlunsplit((parsed.scheme, netloc, path, parsed.query, ""))


def _reject_non_public(hostname: str, port: int | None) -> None:
    try:
        addresses = {
            str(entry[4][0])
            for entry in socket.getaddrinfo(hostname, port or 443, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as error:
        raise LimeSurveyUrlError("LimeSurvey hostname could not be resolved.") from error
    if not addresses:
        raise LimeSurveyUrlError("LimeSurvey hostname did not resolve to an address.")
    for address in addresses:
        if not ipaddress.ip_address(address).is_global:
            raise LimeSurveyUrlError(
                "LimeSurvey host resolves to a private or local address that is not explicitly allowed."
            )
