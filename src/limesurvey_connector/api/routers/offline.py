"""Endpoints that do not contact LimeSurvey; they require an API key."""

from __future__ import annotations

import asyncio
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Body, File, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from limesurvey_connector.api.dependencies import ClientIdDep, SettingsDep
from limesurvey_connector.api.errors import (
    ApiError,
    format_validation_issues,
    invalid_request,
    request_locale,
)
from limesurvey_connector.api.output import dictionary_response, translation_response, wants_csv
from limesurvey_connector.api.settings import Settings
from limesurvey_connector.limesurvey.dictionary import build_limesurvey_dictionary
from limesurvey_connector.limesurvey.normalization import (
    SurveyStructureContractError,
    SurveyStructureSourceError,
    survey_structure_from_lss,
)
from limesurvey_connector.limesurvey.normalization.survey_languages import SurveyLanguageError
from limesurvey_connector.limesurvey.responses import (
    CsvParseError,
    translate_csv,
    translate_records,
)
from survey_data_dictionary import (
    SurveyDictionary,
    get_question_dictionary,
    safe_parse_survey_dictionary,
)
from survey_data_dictionary.schemas import survey_response_record_schema
from survey_structure import (
    SURVEY_STRUCTURE_VERSION,
    get_survey_execution_issues,
    safe_parse_survey_structure,
)
from survey_structure.engine import Array, Enum, Object, String, Unknown

router = APIRouter(prefix="/v1", tags=["dictionaries"])

Language = Annotated[
    str | None, Query(description="Language inside the source, for example es or es-MX.")
]


def invalid_structure(issues: list[dict[str, Any]], locale: str) -> ApiError:
    return ApiError(
        422,
        "INVALID_SURVEY_STRUCTURE",
        f"The submitted object does not satisfy the SurveyStructure {SURVEY_STRUCTURE_VERSION} contract. "
        "Check details.errors for the affected paths and rules.",
        f"El objeto enviado no cumple el contrato SurveyStructure {SURVEY_STRUCTURE_VERSION}. "
        "Consulta las rutas y reglas afectadas en details.errors.",
        details={
            "stage": "survey-structure-validation",
            "surveyStructureVersion": SURVEY_STRUCTURE_VERSION,
            "errors": format_validation_issues(issues, locale),
        },
    )


def invalid_connector_contract(errors: list[dict[str, Any]], locale: str) -> ApiError:
    roots = {error["path"][0] if error["path"] else None for error in errors}
    component = {
        "survey": "SurveyStructure",
        "issues": "SurveyImportIssues",
        "responseState": "SurveyResponseState",
    }.get(next(iter(roots)) if len(roots) == 1 else None, "SurveyLoadResult")  # type: ignore[arg-type]
    return ApiError(
        502,
        "INVALID_CONNECTOR_CONTRACT",
        "The LimeSurvey source was read, but normalization produced a result that does not satisfy the "
        f"{component} contract.",
        f"Se leyó el origen de LimeSurvey, pero la normalización produjo un resultado que no cumple el contrato {component}.",
        details={
            "stage": "survey-structure-normalization",
            "resultType": "SurveyLoadResult",
            "failedComponent": component,
            "surveyStructureVersion": SURVEY_STRUCTURE_VERSION,
            "errors": format_validation_issues(errors, locale),
        },
    )


def survey_aliases(settings: Settings, survey_id: str) -> dict[str, str] | None:
    config = settings.surveys.get(survey_id)
    return dict(config.aliases) if config else None


def ignored_headers(settings: Settings, survey_id: str) -> list[str]:
    config = settings.surveys.get(survey_id)
    return list(config.ignoredHeaders) if config else []


@router.post("/survey-structure/validate", summary="Validate a SurveyStructure")
def validate(request: Request, _: ClientIdDep, document: Annotated[Any, Body()]) -> dict[str, Any]:
    result = safe_parse_survey_structure(document)
    if not result.success:
        raise invalid_structure(result.issues, request_locale(request))
    return {"valid": True, "surveyStructureVersion": SURVEY_STRUCTURE_VERSION, "errors": []}


@router.post(
    "/survey-structure/readiness", summary="List what a valid survey still needs before publication"
)
def readiness(request: Request, _: ClientIdDep, document: Annotated[Any, Body()]) -> dict[str, Any]:
    result = safe_parse_survey_structure(document)
    if not result.success:
        raise invalid_structure(result.issues, request_locale(request))
    issues = get_survey_execution_issues(result.data)
    return {
        "ready": not issues,
        "surveyStructureVersion": SURVEY_STRUCTURE_VERSION,
        "issues": issues,
    }


@router.post("/dictionaries/generate", summary="Build a dictionary from a SurveyStructure")
def generate_dictionary(
    request: Request,
    settings: SettingsDep,
    _: ClientIdDep,
    document: Annotated[Any, Body()],
    output_format: Annotated[Literal["json", "csv"] | None, Query(alias="format")] = None,
    include_system_fields: Annotated[bool, Query(alias="includeSystemFields")] = False,
    include_timing_fields: Annotated[bool, Query(alias="includeTimingFields")] = False,
) -> Response:
    result = safe_parse_survey_structure(document)
    if not result.success:
        raise invalid_request(
            {"errors": format_validation_issues(result.issues, request_locale(request))}
        )
    dictionary = build_limesurvey_dictionary(
        result.data,
        aliases=survey_aliases(settings, result.data["id"]),
        include_system_fields=include_system_fields,
        include_timing_fields=include_timing_fields,
    )
    return dictionary_response(dictionary, wants_csv(request, output_format))


async def _read_lss(
    settings: Settings, file: UploadFile, language: str | None, locale: str
) -> dict[str, Any]:
    if not (file.filename or "").lower().endswith(".lss"):
        raise invalid_request({"file": "The uploaded file must have a .lss extension."})
    content = await file.read(settings.lss_max_bytes + 1)
    if len(content) > settings.lss_max_bytes:
        raise ApiError(
            413,
            "PAYLOAD_TOO_LARGE",
            "Request body exceeds the configured limit.",
            "El cuerpo de la solicitud supera el límite configurado.",
        )
    try:
        return await asyncio.to_thread(survey_structure_from_lss, content, language)
    except (SurveyStructureSourceError, SurveyLanguageError) as error:
        raise ApiError(400, "INVALID_LSS_SOURCE", str(error)) from error
    except SurveyStructureContractError as error:
        raise invalid_connector_contract(error.errors, locale) from error


@router.post("/survey-structures/from-lss", summary="Convert an .lss file to a SurveyLoadResult")
async def structure_from_lss(
    request: Request,
    settings: SettingsDep,
    _: ClientIdDep,
    file: Annotated[UploadFile, File()],
    language: Language = None,
) -> JSONResponse:
    return JSONResponse(await _read_lss(settings, file, language, request_locale(request)))


@router.post("/dictionaries/from-lss", summary="Build a dictionary from an .lss file")
async def dictionary_from_lss(
    request: Request,
    settings: SettingsDep,
    _: ClientIdDep,
    file: Annotated[UploadFile, File()],
    language: Language = None,
    question_code: Annotated[str | None, Query(alias="questionCode")] = None,
    output_format: Annotated[Literal["json", "csv"] | None, Query(alias="format")] = None,
    include_system_fields: Annotated[bool, Query(alias="includeSystemFields")] = False,
    include_timing_fields: Annotated[bool, Query(alias="includeTimingFields")] = False,
) -> Response:
    loaded = await _read_lss(settings, file, language, request_locale(request))
    dictionary = build_limesurvey_dictionary(
        loaded["survey"],
        aliases=survey_aliases(settings, loaded["survey"]["id"]),
        source_issues=loaded["issues"],
        include_system_fields=include_system_fields,
        include_timing_fields=include_timing_fields,
    )
    return dictionary_response(
        select_question(dictionary, question_code), wants_csv(request, output_format)
    )


def select_question(dictionary: SurveyDictionary, question_code: str | None) -> SurveyDictionary:
    if question_code is None:
        return dictionary
    fields = get_question_dictionary(dictionary, question_code)
    if not fields:
        raise ApiError(
            404,
            "QUESTION_NOT_FOUND",
            f'Question code "{question_code}" does not exist in this survey dictionary.',
            f'El código de pregunta "{question_code}" no existe en el diccionario de esta encuesta.',
        )
    return {**dictionary, "fields": fields}


_translation_request = Object(
    {
        "dictionary": Unknown(),
        "responses": Array(survey_response_record_schema).optional(),
        "csv": String().optional(),
        "csvOptions": Object(
            {
                "delimiter": String().min(1).max(1).optional(),
                "ignoredHeaders": Array(String()).optional(),
                "missingValues": Array(String()).optional(),
                "format": Enum("auto", "question-code", "full-heading", "sgqa", "vv").optional(),
                "responseIdHeader": String().min(1).optional(),
            }
        ).optional(),
        "responseIdKey": String().min(1).optional(),
    }
).refine(
    lambda value: ("responses" in value) + ("csv" in value) == 1,
    "Provide exactly one of responses or csv.",
)


@router.post(
    "/responses/translate", summary="Translate response records or a CSV export with a dictionary"
)
def translate(
    request: Request,
    settings: SettingsDep,
    _: ClientIdDep,
    payload: Annotated[Any, Body()],
    output_format: Annotated[Literal["json", "csv"] | None, Query(alias="format")] = None,
) -> Response:
    locale = request_locale(request)
    issues: list[dict[str, Any]] = []
    envelope = _translation_request.parse(payload, [], issues)
    if envelope.status != "valid":
        raise invalid_request({"errors": format_validation_issues(issues, locale)})
    parsed = safe_parse_survey_dictionary(envelope.value["dictionary"])
    if not parsed.success:
        prefixed = [{**issue, "path": ["dictionary", *issue["path"]]} for issue in parsed.issues]
        raise invalid_request({"errors": format_validation_issues(prefixed, locale)})
    dictionary: SurveyDictionary = parsed.data
    body = envelope.value
    if "csv" in body:
        options = body.get("csvOptions", {})
        try:
            translated = translate_csv(
                dictionary,
                body["csv"],
                delimiter=options.get("delimiter"),
                ignored_headers=[
                    *ignored_headers(settings, dictionary["surveyId"]),
                    *options.get("ignoredHeaders", []),
                ],
                missing_values=options.get("missingValues"),
                format=options.get("format", "auto"),
                response_id_header=options.get("responseIdHeader"),
            )["translated"]
        except CsvParseError as error:
            raise invalid_request({"csv": str(error)}) from error
    else:
        translated = translate_records(
            dictionary, body["responses"], response_id_key=body.get("responseIdKey")
        )
    return translation_response(
        translated, dictionary["surveyId"], wants_csv(request, output_format)
    )
