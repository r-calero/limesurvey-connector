from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from limesurvey_connector.remote import RemoteSettings

_PLACEHOLDERS = ("replace_with", "change-me", "changeme", "placeholder")
_MIN_SECRET_LENGTH = 32


class SurveyConfiguration(BaseModel):
    """Per-survey options read from ``DICTIONARY_ALIASES_FILE``."""

    model_config = ConfigDict(frozen=True)

    aliases: dict[str, str] = Field(default_factory=dict)
    ignoredHeaders: list[str] = Field(default_factory=list)


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    app_name: str = "LimeSurvey Connector"
    environment: Literal["production", "development", "test"] = "development"
    app_locale: Literal["es", "en"] = "es"
    api_keys: tuple[str, ...] = ()
    # key id -> secret; the first entry signs new tokens.
    jwt_keys: tuple[tuple[str, str], ...] = ()
    jwt_issuer: str = "limesurvey-connector"
    jwt_leeway_seconds: int = 30
    session_ttl_seconds: int = 1800
    cache_ttl_seconds: int = 600
    rate_limit_per_minute: int = 60
    login_rate_limit_per_minute: int = 8
    responses_rate_limit_per_minute: int = 12
    max_body_bytes: int = 10 * 1024 * 1024
    lss_max_bytes: int = 20 * 1024 * 1024
    redis_url: str | None = None
    allow_in_memory_state: bool = True
    cors_origins: tuple[str, ...] = ()
    allowed_limesurvey_hosts: tuple[str, ...] = ()
    allow_insecure_limesurvey_http: bool = False
    limesurvey_localhost_alias: str | None = None
    limesurvey_expected_version: str | None = None
    limesurvey_compatibility_profile: str = "auto"
    login_timeout_seconds: float = 10
    surveys_timeout_seconds: float = 10
    responses_timeout_seconds: float = 60
    remote: RemoteSettings = RemoteSettings()
    surveys: dict[str, SurveyConfiguration] = Field(default_factory=dict)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if environ is None else environ
        environment = env.get("APP_ENV", "development").strip().lower()
        production = environment == "production"
        api_keys = _split(env.get("API_KEYS"))
        for key in api_keys:
            _require_secret("API_KEYS", key)
        if not api_keys and environment != "test":
            raise ValueError("API_KEYS is required.")
        jwt_keys = tuple(_parse_jwt_keys(env.get("JWT_KEYS", "")))
        if not jwt_keys and environment != "test":
            raise ValueError("JWT_KEYS is required, for example JWT_KEYS=2026-09:<secret>.")
        for _, secret in jwt_keys:
            _require_secret("JWT_KEYS", secret)
        redis_url = env.get("REDIS_URL") or None
        cors = _split(env.get("CORS_ORIGINS"))
        hosts = tuple(host.lower() for host in _split(env.get("ALLOWED_LIMESURVEY_HOSTS")))
        if production:
            if not redis_url:
                raise ValueError("REDIS_URL is required in production.")
            if not cors or "*" in cors:
                raise ValueError("CORS_ORIGINS must list explicit trusted origins in production.")
            if not hosts:
                raise ValueError("ALLOWED_LIMESURVEY_HOSTS is required in production.")
        locale = env.get("APP_LOCALE", "es").strip().lower()
        defaults = RemoteSettings()
        remote = RemoteSettings(
            connect_timeout=_number(
                env, "LS_REMOTE_CONNECT_TIMEOUT_SECONDS", defaults.connect_timeout
            ),
            read_timeout=_number(env, "LS_REMOTE_READ_TIMEOUT_SECONDS", defaults.read_timeout),
            survey_load_timeout=_number(
                env, "LS_SURVEY_LOAD_TIMEOUT_SECONDS", defaults.survey_load_timeout
            ),
            max_concurrent_calls=int(
                _number(env, "LS_ACCOUNT_MAX_CONCURRENT_CALLS", defaults.max_concurrent_calls)
            ),
            responses_max_bytes=int(
                _number(env, "LS_RESPONSES_MAX_BYTES", defaults.responses_max_bytes)
            ),
            responses_max_fields=int(
                _number(env, "LS_RESPONSES_MAX_FIELDS", defaults.responses_max_fields)
            ),
        )
        return cls(
            app_name=env.get("APP_NAME", "LimeSurvey Connector"),
            environment="production"
            if production
            else "test"
            if environment == "test"
            else "development",
            app_locale="es" if locale.startswith("es") else "en",
            api_keys=api_keys,
            jwt_keys=jwt_keys,
            jwt_issuer=env.get("JWT_ISSUER", "limesurvey-connector"),
            session_ttl_seconds=int(_number(env, "SESSION_TTL_SECONDS", 1800)),
            cache_ttl_seconds=int(_number(env, "CACHE_TTL_SECONDS", 600)),
            rate_limit_per_minute=int(_number(env, "RATE_LIMIT_PER_MINUTE", 60)),
            login_rate_limit_per_minute=int(_number(env, "LOGIN_RATE_LIMIT_PER_MINUTE", 8)),
            responses_rate_limit_per_minute=int(
                _number(env, "RESPONSES_RATE_LIMIT_PER_MINUTE", 12)
            ),
            max_body_bytes=int(_number(env, "MAX_BODY_BYTES", 10 * 1024 * 1024)),
            lss_max_bytes=int(_number(env, "LSS_MAX_BYTES", 20 * 1024 * 1024)),
            redis_url=redis_url,
            allow_in_memory_state=not production
            and env.get("ALLOW_IN_MEMORY_STATE", "true").lower() == "true",
            cors_origins=cors,
            allowed_limesurvey_hosts=hosts,
            allow_insecure_limesurvey_http=env.get(
                "ALLOW_INSECURE_LIMESURVEY_HTTP", "false"
            ).lower()
            == "true",
            limesurvey_localhost_alias=env.get("LIMESURVEY_LOCALHOST_ALIAS") or None,
            limesurvey_expected_version=env.get("LIMESURVEY_EXPECTED_VERSION") or None,
            limesurvey_compatibility_profile=env.get("LIMESURVEY_COMPATIBILITY_PROFILE", "auto"),
            login_timeout_seconds=_number(env, "LS_LOGIN_TIMEOUT_SECONDS", 10),
            surveys_timeout_seconds=_number(env, "LS_SURVEYS_TIMEOUT_SECONDS", 10),
            responses_timeout_seconds=_number(env, "LS_RESPONSES_TIMEOUT_SECONDS", 60),
            remote=remote,
            surveys=_load_survey_configuration(env.get("DICTIONARY_ALIASES_FILE")),
        )


def _split(value: str | None) -> tuple[str, ...]:
    return tuple(item.strip() for item in (value or "").split(",") if item.strip())


def _require_secret(name: str, value: str) -> None:
    lowered = value.lower()
    if len(value) < _MIN_SECRET_LENGTH or any(marker in lowered for marker in _PLACEHOLDERS):
        raise ValueError(
            f"Every {name} value must be a non-placeholder secret with at least {_MIN_SECRET_LENGTH} characters."
        )


def _parse_jwt_keys(value: str) -> list[tuple[str, str]]:
    keys = []
    for item in _split(value):
        key_id, separator, secret = item.partition(":")
        if not separator or not key_id.strip():
            raise ValueError("JWT_KEYS entries must have the form <key id>:<secret>.")
        keys.append((key_id.strip(), secret.strip()))
    return keys


def _number(env: Mapping[str, str], name: str, default: float) -> float:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    value = float(raw)
    if value <= 0:
        raise ValueError(f"{name} must be positive.")
    return value


def _load_survey_configuration(path: str | None) -> dict[str, SurveyConfiguration]:
    if not path:
        return {}
    data: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    return {survey_id: SurveyConfiguration(**config) for survey_id, config in data.items()}
