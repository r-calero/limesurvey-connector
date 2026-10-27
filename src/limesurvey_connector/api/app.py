from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from limesurvey_connector import __version__
from limesurvey_connector.api.dependencies import CitricGateway, ClientIdDep, RemoteGateway, hashed
from limesurvey_connector.api.errors import ApiError, install_error_handlers, request_locale
from limesurvey_connector.api.routers import limesurvey, offline
from limesurvey_connector.api.settings import Settings
from limesurvey_connector.api.store import MemoryStore, RedisStore, Store, StoredSession
from survey_structure import SURVEY_STRUCTURE_VERSION

logger = logging.getLogger(__name__)

_LSS_DATABASE_SCHEMA_VERSIONS = ["348", "623", "643", "708"]
_REAPER_INTERVAL_SECONDS = 30


def create_app(
    settings: Settings | None = None,
    *,
    store: Store | None = None,
    gateway: RemoteGateway | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    if store is None:
        if settings.redis_url:
            store = RedisStore(settings.redis_url)
        elif settings.allow_in_memory_state:
            store = MemoryStore()
        else:
            raise ValueError(
                "REDIS_URL is required unless ALLOW_IN_MEMORY_STATE is enabled outside production."
            )
    remote = gateway or CitricGateway(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await store.connect()
        stop = asyncio.Event()
        reaper = asyncio.create_task(_close_expired_sessions(store, remote, stop))
        try:
            yield
        finally:
            stop.set()
            await reaper
            await store.close()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "LimeSurvey dictionaries, survey structures and responses. Open a session with an API key "
            "(`X-Api-Key`) and use the returned bearer token for the LimeSurvey endpoints."
        ),
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.store = store
    app.state.gateway = remote
    install_error_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Api-Key", "Accept-Language"],
        expose_headers=[
            "X-Dictionary-Issue-Count",
            "X-Dictionary-Error-Count",
            "X-Dictionary-Warning-Count",
            "Retry-After",
        ],
    )

    @app.middleware("http")
    async def limits(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path == "/health":
            return await call_next(request)
        locale = request_locale(request)
        length = request.headers.get("content-length")
        limit = (
            max(settings.max_body_bytes, settings.lss_max_bytes)
            if "multipart" in request.headers.get("content-type", "")
            else settings.max_body_bytes
        )
        if length and length.isdigit() and int(length) > limit:
            error = ApiError(
                413,
                "PAYLOAD_TOO_LARGE",
                "Request body exceeds the configured limit.",
                "El cuerpo de la solicitud supera el límite configurado.",
            )
            return JSONResponse(error.body(locale), 413)
        client = request.client.host if request.client else "unknown"
        count, retry_after = await store.increment(f"ip:{hashed(client)}", 60)
        if count > settings.rate_limit_per_minute:
            error = ApiError(
                429,
                "RATE_LIMIT_EXCEEDED",
                "Too many requests. Retry after the time indicated in the Retry-After header.",
                "Demasiadas solicitudes. Reintenta después del tiempo indicado en la cabecera Retry-After.",
            )
            return JSONResponse(error.body(locale), 429, headers={"Retry-After": str(retry_after)})
        return await call_next(request)

    @app.get("/health", tags=["health"])
    async def health() -> Response:
        if await store.is_ready():
            return JSONResponse({"status": "ok"})
        error = ApiError(503, "DEPENDENCY_UNAVAILABLE", "Session storage is unavailable.")
        return JSONResponse(error.body("en"), 503)

    @app.get("/v1/contract", tags=["meta"])
    def contract(_: ClientIdDep) -> dict[str, Any]:
        return {
            "name": "SurveyStructure",
            "acceptedSurveyStructureVersions": [SURVEY_STRUCTURE_VERSION],
            "lssDatabaseSchemaVersions": _LSS_DATABASE_SCHEMA_VERSIONS,
        }

    @app.get("/v1/compatibility", tags=["meta"])
    def compatibility(_: ClientIdDep) -> dict[str, Any]:
        return {
            "expectedLimeSurveyVersion": settings.limesurvey_expected_version,
            "compatibilityProfile": settings.limesurvey_compatibility_profile,
            "acceptedDatabaseSchemaVersions": _LSS_DATABASE_SCHEMA_VERSIONS,
            "note": "The product version is configured explicitly; DBVersion in an LSS file is only its database schema version.",
        }

    app.include_router(limesurvey.router)
    app.include_router(offline.router)
    return app


def _logout(gateway: RemoteGateway, session: StoredSession) -> None:
    gateway.resume(session).close()


async def _close_expired_sessions(
    store: Store, gateway: RemoteGateway, stop: asyncio.Event
) -> None:
    """Log expired sessions out of LimeSurvey so they do not stay open on the server."""
    while not stop.is_set():
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), _REAPER_INTERVAL_SECONDS)
        try:
            for _, session in await store.take_expired_sessions():
                try:
                    await asyncio.to_thread(_logout, gateway, session)
                except Exception as error:
                    logger.warning(
                        "Could not close an expired LimeSurvey session (%s).", type(error).__name__
                    )
        except Exception as error:
            logger.warning("Expired session cleanup could not run (%s).", type(error).__name__)
