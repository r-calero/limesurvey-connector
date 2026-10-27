"""Shared JSON and CSV responses for dictionaries and translations."""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from limesurvey_connector.api.errors import ApiError
from limesurvey_connector.api.security import fingerprint
from survey_data_dictionary import (
    SurveyDictionary,
    TranslatedDataset,
    dictionary_to_csv,
    translated_dataset_to_csv,
)

type OutputFormat = Literal["json", "csv"]


def wants_csv(request: Request, output_format: str | None) -> bool:
    if output_format:
        return output_format == "csv"
    return "text/csv" in request.headers.get("accept", "")


def safe_filename(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value) or "unknown"


def _counts(issues: list[Any]) -> dict[str, str]:
    errors = sum(1 for issue in issues if issue["level"] == "error")
    warnings = sum(1 for issue in issues if issue["level"] == "warning")
    return {
        "X-Dictionary-Issue-Count": str(len(issues)),
        "X-Dictionary-Error-Count": str(errors),
        "X-Dictionary-Warning-Count": str(warnings),
    }


def dictionary_response(dictionary: SurveyDictionary, csv: bool) -> Response:
    issues = list(dictionary["issues"])
    headers = {
        "ETag": f'"{fingerprint(json.dumps(dictionary, ensure_ascii=False, sort_keys=True))}"'
    }
    if not csv:
        return JSONResponse(dictionary, headers=headers)
    if any(issue["level"] == "error" for issue in issues):
        raise ApiError(
            422,
            "DICTIONARY_HAS_ERRORS",
            "CSV download was stopped because the dictionary contains errors.",
            "Se detuvo la descarga CSV porque el diccionario contiene errores.",
            extra={"issues": issues},
        )
    headers.update(_counts(issues))
    headers["Content-Disposition"] = (
        f'attachment; filename="survey-{safe_filename(dictionary["surveyId"])}-dictionary.csv"'
    )
    return Response(
        dictionary_to_csv(dictionary), media_type="text/csv; charset=utf-8", headers=headers
    )


def translation_response(translated: TranslatedDataset, survey_id: str, csv: bool) -> Response:
    if not csv:
        return JSONResponse(_json_safe(translated), headers={"Cache-Control": "no-store"})
    issues = list(translated["issues"])
    if any(issue["level"] == "error" for issue in issues):
        raise ApiError(
            422,
            "TRANSLATION_HAS_ERRORS",
            "CSV download was stopped because response translation contains errors.",
            "Se detuvo la descarga CSV porque la traducción de respuestas contiene errores.",
            extra={"issues": issues},
        )
    headers = _counts(issues)
    headers["Cache-Control"] = "no-store"
    headers["Content-Disposition"] = (
        f'attachment; filename="survey-{safe_filename(survey_id)}-translated.csv"'
    )
    return Response(
        translated_dataset_to_csv(translated), media_type="text/csv; charset=utf-8", headers=headers
    )


def _json_safe(value: Any) -> Any:
    """Drop absent optional values the way JSON.stringify drops ``undefined``."""
    from survey_data_dictionary import ABSENT

    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items() if item is not ABSENT}
    if isinstance(value, list):
        return [None if item is ABSENT else _json_safe(item) for item in value]
    return value
