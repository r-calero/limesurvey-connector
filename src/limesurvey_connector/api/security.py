"""API keys for client applications and JWTs for LimeSurvey sessions (ADR 4)."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Any

import jwt

from limesurvey_connector.api.settings import Settings

_ALGORITHM = "HS256"


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def client_id_for_api_key(api_key: str | None, settings: Settings) -> str | None:
    """Client identifier for a valid key, compared in constant time; ``None`` otherwise."""
    if not api_key:
        return None
    candidate = hashlib.sha256(api_key.encode("utf-8")).digest()
    match = None
    for key in settings.api_keys:
        if hmac.compare_digest(candidate, hashlib.sha256(key.encode("utf-8")).digest()):
            match = key
    return f"client-{fingerprint(match)[:16]}" if match is not None else None


def subject_for(url: str, username: str) -> str:
    """Opaque subject for a LimeSurvey account; the username is not readable from the token."""
    return fingerprint(f"{username}@{url}")[:32]


def new_session_id() -> str:
    return secrets.token_urlsafe(24)


@dataclass(frozen=True)
class IssuedToken:
    token: str
    expires_at: int


def issue_token(
    settings: Settings, *, client_id: str, subject: str, session_id: str
) -> IssuedToken:
    key_id, secret = settings.jwt_keys[0]
    now = int(time.time())
    expires_at = now + settings.session_ttl_seconds
    claims = {
        "iss": settings.jwt_issuer,
        "aud": client_id,
        "sub": subject,
        "jti": session_id,
        "iat": now,
        "nbf": now,
        "exp": expires_at,
    }
    token = jwt.encode(claims, secret, algorithm=_ALGORITHM, headers={"kid": key_id})
    return IssuedToken(token, expires_at)


class InvalidTokenError(Exception):
    pass


def verify_token(settings: Settings, token: str) -> dict[str, Any]:
    """Check signature, algorithm, issuer and time claims; the session store checks the rest."""
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as error:
        raise InvalidTokenError(str(error)) from error
    if header.get("alg") != _ALGORITHM:
        raise InvalidTokenError("Unexpected token algorithm.")
    secret = dict(settings.jwt_keys).get(str(header.get("kid", "")))
    if secret is None:
        raise InvalidTokenError("Unknown signing key.")
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            secret,
            algorithms=[_ALGORITHM],
            issuer=settings.jwt_issuer,
            leeway=settings.jwt_leeway_seconds,
            options={
                "require": ["iss", "aud", "sub", "jti", "iat", "nbf", "exp"],
                "verify_aud": False,
            },
        )
    except jwt.PyJWTError as error:
        raise InvalidTokenError(str(error)) from error
    return claims
