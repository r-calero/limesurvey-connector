from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, Protocol

from fastapi import Depends, Request
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from limesurvey_connector.api.errors import ApiError
from limesurvey_connector.api.security import InvalidTokenError, client_id_for_api_key, verify_token
from limesurvey_connector.api.settings import Settings
from limesurvey_connector.api.store import Store, StoredSession
from limesurvey_connector.remote import LimeSurveyClient, LimeSurveySessionExpiredError


class RemoteGateway(Protocol):
    """Creates LimeSurvey clients; tests replace it with a fake."""

    def open(self, url: str, username: str, password: str) -> LimeSurveyClient: ...
    def resume(self, session: StoredSession) -> LimeSurveyClient: ...


class CitricGateway:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def open(self, url: str, username: str, password: str) -> LimeSurveyClient:
        client = LimeSurveyClient(
            url, username, password, settings=self.settings.remote, validate_url=False
        )
        return client.open()

    def resume(self, session: StoredSession) -> LimeSurveyClient:
        return LimeSurveyClient.resume(
            session.lime_survey_url,
            session.username,
            session.remote_session_key,
            settings=self.settings.remote,
        )


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_store(request: Request) -> Store:
    store: Store = request.app.state.store
    return store


def get_gateway(request: Request) -> RemoteGateway:
    gateway: RemoteGateway = request.app.state.gateway
    return gateway


SettingsDep = Annotated[Settings, Depends(get_settings)]
StoreDep = Annotated[Store, Depends(get_store)]
GatewayDep = Annotated[RemoteGateway, Depends(get_gateway)]


_api_key_header = APIKeyHeader(
    name="X-Api-Key", auto_error=False, description="Key issued to the client application."
)
_bearer = HTTPBearer(
    auto_error=False, description="Token returned by POST /v1/limesurvey/sessions."
)


def require_api_key(
    settings: SettingsDep, x_api_key: Annotated[str | None, Depends(_api_key_header)] = None
) -> str:
    client_id = client_id_for_api_key(x_api_key, settings)
    if client_id is None:
        raise ApiError(
            401,
            "INVALID_CLIENT_CREDENTIAL",
            "A valid API credential is required.",
            "Se requiere una credencial de API válida.",
        )
    return client_id


ClientIdDep = Annotated[str, Depends(require_api_key)]


def _invalid_session() -> ApiError:
    return ApiError(
        401,
        "INVALID_SESSION",
        "Session is missing or expired.",
        "La sesión no existe o ha expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )


@dataclass
class SessionContext:
    session_id: str
    session: StoredSession
    client: LimeSurveyClient


async def current_session(
    settings: SettingsDep,
    store: StoreDep,
    gateway: GatewayDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> SessionContext:
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials.strip()
    ):
        raise _invalid_session()
    try:
        claims = verify_token(settings, credentials.credentials.strip())
    except InvalidTokenError as error:
        raise _invalid_session() from error
    session = await store.get_session(str(claims["jti"]))
    if session is None or session.client_id != claims["aud"]:
        raise _invalid_session()
    return SessionContext(str(claims["jti"]), session, gateway.resume(session))


SessionDep = Annotated[SessionContext, Depends(current_session)]


async def enforce_rate_limit(store: Store, key: str, limit: int, window_seconds: int = 60) -> None:
    count, retry_after = await store.increment(key, window_seconds)
    if count > max(1, limit):
        raise ApiError(
            429,
            "RATE_LIMIT_EXCEEDED",
            "Too many requests. Retry after the time indicated in the Retry-After header.",
            "Demasiadas solicitudes. Reintenta después del tiempo indicado en la cabecera Retry-After.",
            headers={"Retry-After": str(retry_after)},
        )


def hashed(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


async def run_remote[T](
    context: SessionContext | None,
    store: Store,
    timeout: float,
    timeout_error: tuple[str, str, str],
    operation: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    """Run a blocking LimeSurvey call in a worker thread with a total time limit.

    An expired remote session also removes the local one.
    """
    try:
        return await asyncio.wait_for(asyncio.to_thread(operation, *args, **kwargs), timeout)
    except TimeoutError as error:
        code, message, spanish = timeout_error
        raise ApiError(504, code, message, spanish) from error
    except LimeSurveySessionExpiredError:
        if context is not None:
            await store.delete_session(context.session_id)
        raise
