"""Error bodies ``{code, message, details?}`` and diagnostics localized by Accept-Language."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from limesurvey_connector.remote import LimeSurveyError
from survey_structure import localize_survey_validation_issue, resolve_survey_diagnostic_locale

logger = logging.getLogger(__name__)
_IDENTIFIER = re.compile(r"^[A-Za-z_$][\w$]*$")


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        spanish: str | None = None,
        *,
        details: Any = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.spanish = spanish
        self.details = details
        self.headers = headers
        self.extra = extra or {}

    def body(self, locale: str) -> dict[str, Any]:
        body: dict[str, Any] = {
            "code": self.code,
            "message": self.spanish if locale == "es" and self.spanish else self.message,
        }
        if self.details is not None:
            body["details"] = self.details
        body.update(self.extra)
        return body


def request_locale(request: Request) -> str:
    """Accept-Language picks the diagnostics language; the ``language`` query selects survey content."""
    default = request.app.state.settings.app_locale
    best: tuple[float, str] | None = None
    for part in request.headers.get("accept-language", "").split(","):
        tag, *parameters = part.strip().split(";")
        quality = 1.0
        for parameter in parameters:
            name, _, value = parameter.strip().partition("=")
            if name == "q":
                try:
                    quality = float(value)
                except ValueError:
                    quality = 0
        if (
            0 < quality <= 1
            and re.match(r"^(en|es)(?:[-_]|$)", tag, re.IGNORECASE)
            and (best is None or quality > best[0])
        ):
            best = (quality, tag)
    return resolve_survey_diagnostic_locale(best[1] if best else default)


def format_validation_issues(issues: Sequence[dict[str, Any]], locale: str) -> list[dict[str, Any]]:
    """Paths, JSON pointers, rules and each failed union variant, as limesurvey-dictionary-api reports them."""
    formatted = []
    for issue in issues:
        params = dict(issue.get("params") or {})
        reason = params.pop("reason", None)
        if issue.get("keys") is not None:
            params["unknownProperties"] = issue["keys"]
        entry: dict[str, Any] = {
            "path": _format_path(issue["path"]),
            "pointer": "".join(
                "/" + str(segment).replace("~", "~0").replace("/", "~1")
                for segment in issue["path"]
            ),
            "rule": reason if isinstance(reason, str) else issue["code"],
            "message": localize_survey_validation_issue(issue, locale),
        }
        if params:
            entry["context"] = params
        if issue.get("unionErrors"):
            entry["alternatives"] = [
                format_validation_issues(branch, locale) for branch in issue["unionErrors"]
            ]
        formatted.append(entry)
    return formatted


def _format_path(path: Sequence[str | int]) -> str:
    result = ""
    for segment in path:
        if isinstance(segment, int):
            result += f"[{segment}]"
        elif _IDENTIFIER.match(segment):
            result = f"{result}.{segment}" if result else segment
        else:
            result += f"[{json.dumps(segment, ensure_ascii=False)}]"
    return result


def invalid_request(details: Any) -> ApiError:
    return ApiError(
        400,
        "INVALID_REQUEST",
        "Request contract is invalid.",
        "El contrato de la solicitud no es válido.",
        details=details,
    )


def limesurvey_error(error: LimeSurveyError) -> ApiError:
    spanish = {
        "LS_SESSION_EXPIRED": "LimeSurvey ya no acepta esta sesión. Abre una nueva con POST /v1/limesurvey/sessions.",
        "LS_UNREACHABLE": "No se puede contactar con el servidor LimeSurvey.",
        "LS_REMOTE_CONTROL_UNAVAILABLE": "RemoteControl 2 está desactivado en LimeSurvey o no respondió con JSON.",
        "LS_REMOTE_REJECTED_REQUEST": "LimeSurvey rechazó la solicitud de RemoteControl 2.",
        "LS_SURVEY_NOT_FOUND": "La encuesta no existe o no tiene grupos de preguntas.",
        "LS_LANGUAGE_NOT_AVAILABLE": "El idioma solicitado no está disponible en la encuesta.",
    }
    message = (
        "LimeSurvey no longer accepts this session. Open a new session with POST /v1/limesurvey/sessions."
        if error.code == "LS_SESSION_EXPIRED"
        else error.message
    )
    return ApiError(error.status_code, error.code, message, spanish.get(error.code))


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(request: Request, error: ApiError) -> JSONResponse:
        return JSONResponse(
            error.body(request_locale(request)), error.status_code, headers=error.headers
        )

    @app.exception_handler(LimeSurveyError)
    async def remote_error(request: Request, error: LimeSurveyError) -> JSONResponse:
        converted = limesurvey_error(error)
        return JSONResponse(converted.body(request_locale(request)), converted.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        details = {
            "errors": [
                {
                    "path": ".".join(str(part) for part in item["loc"]),
                    "rule": item["type"],
                    "message": item["msg"],
                }
                for item in error.errors()
            ]
        }
        return JSONResponse(invalid_request(details).body(request_locale(request)), 400)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
        locale = request_locale(request)
        if error.status_code == 404:
            body = ApiError(404, "NOT_FOUND", "Route not found.", "Ruta no encontrada.").body(
                locale
            )
        elif error.status_code == 405:
            body = ApiError(
                405, "METHOD_NOT_ALLOWED", "Method not allowed.", "Método no permitido."
            ).body(locale)
        else:
            body = ApiError(
                error.status_code,
                "INVALID_REQUEST",
                "The request could not be read. Check its syntax, content type and parameters.",
                "No se pudo leer la solicitud. Revisa su sintaxis, tipo de contenido y parámetros.",
            ).body(locale)
        return JSONResponse(body, error.status_code)

    @app.exception_handler(Exception)
    async def unexpected(request: Request, error: Exception) -> JSONResponse:
        logger.exception("Unhandled API error")
        body = ApiError(
            500,
            "INTERNAL_ERROR",
            "The request could not be completed.",
            "No se pudo completar la solicitud.",
        ).body(request_locale(request))
        return JSONResponse(body, 500)
