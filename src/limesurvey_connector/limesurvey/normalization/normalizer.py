"""Compose normalized LimeSurvey fields and groups into a validated SurveyLoadResult."""

from __future__ import annotations

import os
from typing import Any

from survey_structure import SURVEY_STRUCTURE_VERSION

from .condition_references import build_condition_references
from .contract import (
    SurveyStructureContractError,
    validate_survey_load_result,
)
from .field_collection import normalize_fields
from .source_values import _clean_html, _compact, _issue, _list, _record, _text
from .survey_languages import select_language_rows
from .survey_settings import normalize_groups, normalize_settings


class SurveyStructureSourceError(ValueError):
    """The source cannot produce a valid SurveyStructure."""


class UnsupportedQuestionDependencyError(SurveyStructureSourceError):
    """A rule depends on a source question whose native type is unsupported."""

    def __init__(
        self,
        message: str,
        errors: list[dict[str, Any]] | None = None,
        unsupported: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.errors = errors or []
        self.unsupported = unsupported or []


def build_survey_structure(
    payload: dict[str, Any], source_format: str = "remotecontrol"
) -> dict[str, Any]:
    """Normalize LimeSurvey data into a validated survey load result."""
    survey = _record(payload.get("survey"))
    language_data = _record(payload.get("language"))
    groups = [_record(item) for item in _list(payload.get("groups")) if _record(item)]
    questions = [
        _normalize_question(_record(item))
        for item in _list(payload.get("questions"))
        if _record(item)
    ]
    source = _record(payload.get("source"))
    issues: list[dict[str, Any]] = list(_list(payload.get("issues")))

    survey_id = _text(survey.get("sid") or source.get("surveyId") or payload.get("id")).strip()
    if not survey_id:
        raise SurveyStructureSourceError("LimeSurvey source does not contain a survey id.")

    selected_language = _text(
        source.get("selectedLanguage") or survey.get("language") or payload.get("selected_language")
    ).strip()
    groups = select_language_rows(groups, selected_language, "gid")
    questions = select_language_rows(questions, selected_language, "qid")
    condition_references = build_condition_references(questions, survey_id)
    populated_groups = {_text(question.get("gid")) for question in questions}
    spanish = os.environ.get("APP_LOCALE", "es").lower().startswith("es")
    for group in groups:
        if _text(group.get("gid")) not in populated_groups:
            name = _clean_html(group.get("group_name")) or _text(group.get("gid"))
            identity = f"{name} (gid={_text(group.get('gid'))})"
            issues.append(
                _issue(
                    "warning",
                    "INVALID_SOURCE",
                    (
                        f"El grupo {identity} no contiene preguntas; se conserva su contenido y se continúa con los demás grupos."
                        if spanish
                        else f"Group {identity} has no questions; its content is retained and the other groups are imported."
                    ),
                )
            )

    fields, source_metrics = normalize_fields(
        questions,
        groups,
        survey_id,
        selected_language,
        issues,
        condition_references,
        _text(_record(payload.get("source")).get("remoteUrl")),
    )

    available_languages = [
        str(item) for item in _list(source.get("availableLanguages")) if _text(item).strip()
    ]
    title = _clean_html(language_data.get("surveyls_title") or payload.get("title"))
    description = _clean_html(
        language_data.get("surveyls_description") or payload.get("description")
    )
    survey_structure: dict[str, Any] = {
        "surveyStructureVersion": SURVEY_STRUCTURE_VERSION,
        "id": survey_id,
        "fields": fields,
        "source": _compact(
            {
                "platform": "limesurvey",
                "format": source_format,
                # A LimeSurvey DBVersion is a database-schema revision, not the
                # product version. Keep it in the typed extension instead.
                "version": _text(source.get("version")).strip() or None,
                "originDetails": (
                    [
                        _compact(
                            {
                                "type": "limesurvey-survey",
                                "version": "1.0.0",
                                "databaseSchemaVersion": _text(
                                    source.get("databaseSchemaVersion")
                                ).strip()
                                or None,
                            }
                        )
                    ]
                    if source.get("databaseSchemaVersion")
                    else None
                ),
            }
        ),
    }
    if title:
        survey_structure["title"] = title
    if description:
        survey_structure["description"] = description
    if selected_language:
        survey_structure["language"] = selected_language
    if available_languages:
        survey_structure["availableLanguages"] = available_languages
    portable_groups = normalize_groups(groups, condition_references, issues)
    if portable_groups:
        survey_structure["groups"] = portable_groups
    settings = normalize_settings(survey, language_data)
    if settings:
        survey_structure["settings"] = settings
    load_result: dict[str, Any] = {
        "survey": survey_structure,
        "issues": issues,
        "sourceMetrics": source_metrics,
    }
    completion_context = _record(payload.get("completion_context"))
    if completion_context:
        load_result["responseState"] = {
            "active": bool(completion_context.get("active", False)),
            "canSaveResponses": bool(completion_context.get("canSaveResponses", False)),
            "submitMode": completion_context.get("submitMode", "submit_preview"),
            "warningCodes": _list(completion_context.get("warningCodes")),
            "didNotSaveCode": completion_context.get("didNotSaveCode"),
        }
        if completion_context.get("language"):
            load_result["responseState"]["language"] = completion_context["language"]
        if completion_context.get("endText"):
            load_result["responseState"]["endText"] = completion_context["endText"]
    try:
        return validate_survey_load_result(load_result)
    except SurveyStructureContractError as error:
        missing = {
            item.get("params", {}).get("fieldCode")
            for item in error.errors
            if item.get("params", {}).get("reason") == "condition-reference-missing-field"
        }
        unsupported = [
            item
            for item in issues
            if item.get("code") == "UNSUPPORTED_TYPE" and item.get("questionCode") in missing
        ]
        if unsupported:
            detail = ", ".join(
                f"{item['questionCode']} ({item.get('details', {}).get('sourceType')})"
                for item in unsupported
            )
            raise UnsupportedQuestionDependencyError(
                f"Las reglas dependen de preguntas que sí existen en LimeSurvey, pero su tipo todavía no está soportado: {detail}."
                if spanish
                else f"Rules depend on questions that exist in LimeSurvey but whose native types are not supported yet: {detail}.",
                errors=error.errors,
                unsupported=unsupported,
            ) from error
        raise


def _normalize_question(question: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(question)
    result = _record(normalized.get("result"))
    for key in (
        "answeroptions",
        "subquestions",
        "available_answers",
        "attributes",
        "attributes_lang",
    ):
        value = result.get(key, normalized.get(key))
        if isinstance(value, str) and value.strip().lower().startswith("no available "):
            value = None
        if key in result:
            result[key] = value
        if key in normalized:
            normalized[key] = value
    normalized["result"] = result
    return normalized
