"""LimeSurvey sessions and survey data. Opening a session needs an API key; the rest a session JWT."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit, urlunsplit

from fastapi import APIRouter, Path, Query, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from limesurvey_connector.api.dependencies import (
    ClientIdDep,
    GatewayDep,
    SessionContext,
    SessionDep,
    SettingsDep,
    StoreDep,
    enforce_rate_limit,
    hashed,
    run_remote,
)
from limesurvey_connector.api.errors import ApiError
from limesurvey_connector.api.output import (
    dictionary_response,
    safe_filename,
    translation_response,
    wants_csv,
)
from limesurvey_connector.api.routers.offline import select_question, survey_aliases
from limesurvey_connector.api.security import issue_token, new_session_id, subject_for
from limesurvey_connector.api.settings import Settings
from limesurvey_connector.api.store import Store, StoredSession
from limesurvey_connector.limesurvey.dictionary import build_limesurvey_dictionary
from limesurvey_connector.limesurvey.responses import translate_records
from limesurvey_connector.remote import LimeSurveyUrlError, field_detail, validate_limesurvey_url
from survey_structure import SURVEY_STRUCTURE_VERSION

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/limesurvey", tags=["limesurvey"])

SurveyId = Annotated[int, Path(ge=1, description="LimeSurvey survey id.")]
Language = Annotated[
    str | None, Query(description="Language of the survey content, for example es or es-MX.")
]
Refresh = Annotated[bool, Query(description="Bypass the cache and read LimeSurvey again.")]
OutputFormat = Annotated[
    Literal["json", "csv"] | None,
    Query(alias="format", description="Alternatively send Accept: text/csv."),
]

_LOAD_TIMEOUT = (
    "LS_SURVEY_LOAD_TIMEOUT",
    "LimeSurvey did not finish loading the survey within the configured timeout.",
    "LimeSurvey no terminó de cargar la encuesta dentro del tiempo configurado.",
)
_RESPONSES_TIMEOUT = (
    "LS_RESPONSE_EXPORT_TIMEOUT",
    "LimeSurvey did not finish exporting responses within the configured timeout.",
    "LimeSurvey no terminó de exportar las respuestas dentro del tiempo configurado.",
)


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(description="RemoteControl 2 URL ending in /admin/remotecontrol.")
    username: str = Field(min_length=1, max_length=256)
    password: str = Field(min_length=1, max_length=2048)


class SessionCreated(BaseModel):
    accessToken: str
    tokenType: Literal["Bearer"] = "Bearer"
    expiresIn: int
    expiresAt: str
    expectedLimeSurveyVersion: str | None
    compatibilityProfile: str


def _container_url(url: str, alias: str | None) -> str:
    """Route a host-local URL through a container alias such as host.docker.internal."""
    parts = urlsplit(url)
    if not alias or parts.hostname not in {"localhost", "127.0.0.1"}:
        return url
    netloc = f"{alias}:{parts.port}" if parts.port else alias
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


@router.post(
    "/sessions", status_code=201, response_model=SessionCreated, summary="Open a LimeSurvey session"
)
async def open_session(
    request: Request,
    body: SessionRequest,
    settings: SettingsDep,
    store: StoreDep,
    gateway: GatewayDep,
    client_id: ClientIdDep,
) -> SessionCreated:
    client_ip = request.client.host if request.client else "unknown"
    await enforce_rate_limit(
        store,
        f"login:{hashed(client_ip.lower(), body.username.strip().lower())}",
        settings.login_rate_limit_per_minute,
    )
    try:
        trusted = await asyncio.to_thread(
            validate_limesurvey_url,
            body.url,
            allowed_hosts=settings.allowed_limesurvey_hosts,
            allow_insecure_http=settings.allow_insecure_limesurvey_http,
        )
    except LimeSurveyUrlError as error:
        raise ApiError(400, error.code, error.message) from error
    url = _container_url(trusted, settings.limesurvey_localhost_alias)

    task = asyncio.ensure_future(asyncio.to_thread(gateway.open, url, body.username, body.password))
    try:
        client = await asyncio.wait_for(asyncio.shield(task), settings.login_timeout_seconds)
    except TimeoutError as error:
        # The login keeps running in its thread; close the session if it opens later.
        task.add_done_callback(_close_late_login)
        raise ApiError(
            504,
            "LS_LOGIN_TIMEOUT",
            f"LimeSurvey login did not finish within {int(settings.login_timeout_seconds)} seconds.",
            f"El inicio de sesión en LimeSurvey no terminó en {int(settings.login_timeout_seconds)} segundos.",
        ) from error

    session_id = new_session_id()
    expires_at = time.time() + settings.session_ttl_seconds
    try:
        await store.set_session(
            session_id,
            StoredSession(url, body.username, client.session_key, client_id, expires_at),
        )
    except BaseException:
        await asyncio.to_thread(_close_quietly, client)
        raise
    issued = issue_token(
        settings,
        client_id=client_id,
        subject=subject_for(url, body.username),
        session_id=session_id,
    )
    return SessionCreated(
        accessToken=issued.token,
        expiresIn=settings.session_ttl_seconds,
        expiresAt=datetime.fromtimestamp(issued.expires_at, UTC).isoformat().replace("+00:00", "Z"),
        expectedLimeSurveyVersion=settings.limesurvey_expected_version,
        compatibilityProfile=settings.limesurvey_compatibility_profile,
    )


def _close_quietly(client: Any) -> None:
    try:
        client.close()
    except Exception as error:
        logger.warning("Could not close a LimeSurvey session (%s).", type(error).__name__)


def _close_late_login(task: asyncio.Future[Any]) -> None:
    if not task.cancelled() and task.exception() is None:
        asyncio.get_running_loop().run_in_executor(None, _close_quietly, task.result())


@router.delete("/sessions/current", status_code=204, summary="Close the LimeSurvey session")
async def close_session(context: SessionDep, store: StoreDep) -> Response:
    try:
        await asyncio.to_thread(_close_quietly, context.client)
    finally:
        await store.delete_session(context.session_id)
    return Response(status_code=204)


@router.get("/surveys", summary="List the surveys visible to the LimeSurvey account")
async def list_surveys(
    context: SessionDep, settings: SettingsDep, store: StoreDep, refresh: Refresh = False
) -> Any:
    key = f"surveys:{context.client.account_id}"
    cached = None if refresh else await store.get_json(key)
    if cached is not None:
        return cached
    surveys = await run_remote(
        context,
        store,
        settings.surveys_timeout_seconds,
        (
            "LS_SURVEYS_TIMEOUT",
            "LimeSurvey did not list the surveys in time.",
            "LimeSurvey no listó las encuestas a tiempo.",
        ),
        context.client.list_surveys,
    )
    await store.set_json(key, surveys, settings.cache_ttl_seconds)
    return surveys


async def load_survey(
    context: SessionContext,
    settings: Settings,
    store: Store,
    survey_id: int,
    language: str | None,
    refresh: bool,
) -> dict[str, Any]:
    key = hashed(
        SURVEY_STRUCTURE_VERSION,
        "load-result",
        context.client.account_id,
        str(survey_id),
        language or "",
    )
    cached = None if refresh else await store.get_json(key)
    if isinstance(cached, dict):
        return cached
    loaded: dict[str, Any] = await run_remote(
        context,
        store,
        settings.remote.survey_load_timeout + 5,
        _LOAD_TIMEOUT,
        context.client.get_survey_load_result,
        survey_id,
        language,
    )
    await store.set_json(key, loaded, settings.cache_ttl_seconds)
    return loaded


@router.get("/surveys/{sid}/structure", summary="Survey as a SurveyLoadResult")
async def survey_structure(
    sid: SurveyId,
    context: SessionDep,
    settings: SettingsDep,
    store: StoreDep,
    language: Language = None,
    refresh: Refresh = False,
) -> JSONResponse:
    return JSONResponse(await load_survey(context, settings, store, sid, language, refresh))


@router.get(
    "/surveys/{sid}/fields/{question_code}",
    summary="One question: its structure and dictionary entries",
)
async def survey_field(
    sid: SurveyId,
    question_code: str,
    context: SessionDep,
    settings: SettingsDep,
    store: StoreDep,
    language: Language = None,
    refresh: Refresh = False,
) -> JSONResponse:
    detail = field_detail(
        await load_survey(context, settings, store, sid, language, refresh), question_code
    )
    if detail is None:
        raise ApiError(
            404,
            "QUESTION_NOT_FOUND",
            f'Question code "{question_code}" does not exist in this survey.',
            f'El código de pregunta "{question_code}" no existe en esta encuesta.',
        )
    return JSONResponse(detail)


@router.get("/surveys/{sid}/dictionary", summary="Survey data dictionary in JSON or CSV")
async def survey_dictionary(
    request: Request,
    sid: SurveyId,
    context: SessionDep,
    settings: SettingsDep,
    store: StoreDep,
    language: Language = None,
    question_code: Annotated[str | None, Query(alias="questionCode")] = None,
    include_system_fields: Annotated[bool, Query(alias="includeSystemFields")] = False,
    include_timing_fields: Annotated[bool, Query(alias="includeTimingFields")] = False,
    refresh: Refresh = False,
    output_format: OutputFormat = None,
) -> Response:
    loaded = await load_survey(context, settings, store, sid, language, refresh)
    dictionary = build_limesurvey_dictionary(
        loaded["survey"],
        aliases=survey_aliases(settings, str(sid)),
        source_issues=loaded["issues"],
        include_system_fields=include_system_fields,
        include_timing_fields=include_timing_fields,
    )
    return dictionary_response(
        select_question(dictionary, question_code), wants_csv(request, output_format)
    )


class ExportQuery(BaseModel):
    language: str | None
    completion_status: Literal["all", "complete", "incomplete"]
    heading_type: Literal["code", "full", "abbreviated"]
    response_type: Literal["short", "long"]
    from_response_id: int | None
    to_response_id: int | None
    fields: list[str] | None


def _export_query(
    settings: Settings,
    language: str | None,
    completion_status: Literal["all", "complete", "incomplete"],
    heading_type: Literal["code", "full", "abbreviated"],
    response_type: Literal["short", "long"],
    from_response_id: int | None,
    to_response_id: int | None,
    fields: list[str] | None,
) -> ExportQuery:
    if from_response_id and to_response_id and from_response_id > to_response_id:
        raise ApiError(
            400,
            "INVALID_RESPONSE_RANGE",
            "fromResponseId must be less than or equal to toResponseId.",
            "fromResponseId debe ser menor o igual que toResponseId.",
        )
    names = list(
        dict.fromkeys(
            part.strip() for item in fields or [] for part in item.split(",") if part.strip()
        )
    )
    if len(names) > settings.remote.responses_max_fields:
        raise ApiError(
            400,
            "TOO_MANY_RESPONSE_FIELDS",
            f"At most {settings.remote.responses_max_fields} response fields may be requested.",
            f"Se pueden pedir como máximo {settings.remote.responses_max_fields} campos de respuesta.",
        )
    return ExportQuery(
        language=language.strip() if language and language.strip() else None,
        completion_status=completion_status,
        heading_type=heading_type,
        response_type=response_type,
        from_response_id=from_response_id,
        to_response_id=to_response_id,
        fields=names or None,
    )


CompletionStatus = Annotated[
    Literal["all", "complete", "incomplete"], Query(alias="completionStatus")
]
HeadingType = Annotated[Literal["code", "full", "abbreviated"], Query(alias="headingType")]
ResponseType = Annotated[Literal["short", "long"], Query(alias="responseType")]
FromId = Annotated[int | None, Query(alias="fromResponseId", ge=1)]
ToId = Annotated[int | None, Query(alias="toResponseId", ge=1)]
Fields = Annotated[
    list[str] | None,
    Query(description="Response columns to export; repeat or separate with commas."),
]


async def _export(
    context: SessionContext,
    settings: Settings,
    store: Store,
    sid: int,
    query: ExportQuery,
    file_format: str,
) -> Any:
    await enforce_rate_limit(
        store,
        f"responses:{hashed(context.session_id, str(sid))}",
        settings.responses_rate_limit_per_minute,
    )
    return await run_remote(
        context,
        store,
        settings.responses_timeout_seconds,
        _RESPONSES_TIMEOUT,
        context.client.export_responses,
        sid,
        file_format=file_format,
        language=query.language,
        completion_status=query.completion_status,
        heading_type=query.heading_type,
        response_type=query.response_type,
        from_response_id=query.from_response_id,
        to_response_id=query.to_response_id,
        fields=query.fields,
    )


@router.get("/surveys/{sid}/responses", summary="Export responses as JSON or the original CSV")
async def survey_responses(
    request: Request,
    sid: SurveyId,
    context: SessionDep,
    settings: SettingsDep,
    store: StoreDep,
    language: Language = None,
    completion_status: CompletionStatus = "all",
    heading_type: HeadingType = "code",
    response_type: ResponseType = "short",
    from_response_id: FromId = None,
    to_response_id: ToId = None,
    fields: Fields = None,
    output_format: OutputFormat = None,
) -> Response:
    query = _export_query(
        settings,
        language,
        completion_status,
        heading_type,
        response_type,
        from_response_id,
        to_response_id,
        fields,
    )
    csv = wants_csv(request, output_format)
    exported = await _export(context, settings, store, sid, query, "csv" if csv else "json")
    if csv:
        return Response(
            exported,
            media_type="text/csv; charset=utf-8",
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": f'attachment; filename="survey-{safe_filename(str(sid))}-responses.csv"',
            },
        )
    return JSONResponse(exported, headers={"Cache-Control": "no-store"})


@router.get(
    "/surveys/{sid}/responses/translated",
    summary="Export responses and translate them with the dictionary",
)
async def survey_translated_responses(
    request: Request,
    sid: SurveyId,
    context: SessionDep,
    settings: SettingsDep,
    store: StoreDep,
    language: Language = None,
    completion_status: CompletionStatus = "all",
    from_response_id: FromId = None,
    to_response_id: ToId = None,
    refresh: Refresh = False,
    output_format: OutputFormat = None,
) -> Response:
    query = _export_query(
        settings,
        language,
        completion_status,
        "code",
        "short",
        from_response_id,
        to_response_id,
        None,
    )
    loaded = await load_survey(context, settings, store, sid, query.language, refresh)
    dictionary = build_limesurvey_dictionary(
        loaded["survey"], aliases=survey_aliases(settings, str(sid)), source_issues=loaded["issues"]
    )
    exported = await _export(context, settings, store, sid, query, "json")
    translated = translate_records(dictionary, exported["responses"], response_id_key="id")
    return translation_response(translated, str(sid), wants_csv(request, output_format))
