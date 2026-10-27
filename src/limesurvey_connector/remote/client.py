"""LimeSurvey RemoteControl 2 client built on Citric.

Ports the survey loading, response export and error handling of limesurvey-rc2-api
as a synchronous library. The REST service runs these calls in worker threads.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import FIRST_EXCEPTION, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Literal, Self, TypeVar

import requests
from citric import Client
from citric.exceptions import LimeSurveyStatusError

from limesurvey_connector.limesurvey.dictionary import build_limesurvey_dictionary
from limesurvey_connector.limesurvey.naming import underscore_record
from limesurvey_connector.limesurvey.normalization import (
    SurveyStructureSourceError,
    build_survey_structure,
)
from limesurvey_connector.limesurvey.normalization.survey_languages import (
    SurveyLanguageError,
    select_language_rows,
)
from limesurvey_connector.limesurvey.responses import translate_records
from limesurvey_connector.remote import _citric
from limesurvey_connector.remote.errors import (
    InvalidResponseExportError,
    LimeSurveyError,
    LimeSurveyLoginError,
    LimeSurveyTimeoutError,
    ResponseExportTooLargeError,
    SurveyLanguageNotAvailableError,
    SurveyNotFoundError,
    classify,
)
from limesurvey_connector.remote.url_policy import validate_limesurvey_url
from survey_data_dictionary import (
    SurveyDictionary,
    TranslatedDataset,
    get_question_dictionary,
    safe_parse_survey_response_dataset,
)

T = TypeVar("T")

SURVEY_SETTINGS = [
    "sid",
    "active",
    "format",
    "showwelcome",
    "showprogress",
    "allowprev",
    "questionindex",
    "navigationdelay",
    "showgroupinfo",
    "language",
    "additional_languages",
]
SURVEY_LANGUAGE_SETTINGS = [
    "surveyls_title",
    "surveyls_description",
    "surveyls_welcometext",
    "surveyls_endtext",
    "surveyls_policy_notice",
]

type CompletionStatus = Literal["all", "complete", "incomplete"]
type HeadingType = Literal["code", "full", "abbreviated"]
type ResponseType = Literal["short", "long"]


@dataclass(frozen=True)
class RemoteSettings:
    """Timeouts and limits; defaults match limesurvey-rc2-api."""

    connect_timeout: float = 5
    read_timeout: float = 30
    survey_load_timeout: float = 120
    max_concurrent_calls: int = 8
    max_attempts: int = 3
    backoff_base: float = 1
    backoff_max: float = 8
    backoff_jitter: float = 0.25
    responses_max_bytes: int = 20 * 1024 * 1024
    responses_max_fields: int = 500


_slots_lock = threading.Lock()
_account_slots: dict[str, threading.BoundedSemaphore] = {}


def account_id(url: str, username: str) -> str:
    """Hash of URL and username, used to scope caches and limits without exposing them."""
    identity = json.dumps(
        {"url": url.strip(), "username": username.strip()}, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _account_slot(identifier: str, limit: int) -> threading.BoundedSemaphore:
    with _slots_lock:
        slot = _account_slots.get(identifier)
        if slot is None:
            slot = _account_slots[identifier] = threading.BoundedSemaphore(max(1, limit))
        return slot


class LimeSurveyClient:
    """Session with one LimeSurvey account.

    Use as a context manager to log in and out::

        with LimeSurveyClient(url, username, password, allowed_hosts=["surveys.example.org"]) as ls:
            dictionary = ls.get_dictionary(783587, language="es")

    Without ``allowed_hosts`` the URL must resolve to a public address.
    """

    def __init__(
        self,
        url: str,
        username: str,
        password: str | None = None,
        *,
        allowed_hosts: Sequence[str] = (),
        allow_insecure_http: bool = False,
        settings: RemoteSettings | None = None,
        validate_url: bool = True,
    ) -> None:
        self.settings = settings or RemoteSettings()
        self.url = (
            validate_limesurvey_url(
                url, allowed_hosts=allowed_hosts, allow_insecure_http=allow_insecure_http
            )
            if validate_url
            else url
        )
        self.username = username
        self.account_id = account_id(self.url, username)
        self._password = password
        self._client: Client | None = None
        self._owns_session = False

    @classmethod
    def resume(
        cls, url: str, username: str, session_key: str, *, settings: RemoteSettings | None = None
    ) -> LimeSurveyClient:
        """Reattach to a session opened earlier; the URL was validated when it was opened."""
        instance = cls(url, username, settings=settings, validate_url=False)
        instance._client = _citric.resume_client(url, session_key, instance._timeout)
        return instance

    @property
    def _timeout(self) -> tuple[float, float]:
        return (self.settings.connect_timeout, self.settings.read_timeout)

    @property
    def is_open(self) -> bool:
        return self._client is not None

    @property
    def session_key(self) -> str:
        key = self._citric.session.key
        if not key:
            raise LimeSurveyError("LimeSurvey did not provide a session key.")
        return key

    @property
    def citric(self) -> Client:
        """The underlying Citric client, for RemoteControl calls this library does not wrap."""
        return self._citric

    @property
    def _citric(self) -> Client:
        if self._client is None:
            raise LimeSurveyError("LimeSurvey session is not open.")
        return self._client

    def open(self) -> Self:
        if self._client is not None:
            return self
        if self._password is None:
            raise LimeSurveyLoginError("A password is required to open a LimeSurvey session.")
        try:
            self._client = _citric.create_client(
                self.url, self.username, self._password, self._timeout
            )
        except Exception as error:
            classified = classify(error, "logging in")
            if type(classified) is LimeSurveyError:
                raise LimeSurveyLoginError(
                    f"LimeSurvey login failed: {error}", str(error)
                ) from error
            raise classified from error
        self._owns_session = True
        return self

    def close(self) -> None:
        """Release the session in LimeSurvey; local state is cleared even if that fails."""
        client, self._client = self._client, None
        if client is None:
            return
        try:
            client.close()
        except Exception as error:
            raise classify(error, "closing the session") from error

    def __enter__(self) -> Self:
        return self.open()

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        trace: TracebackType | None,
    ) -> None:
        if self._owns_session:
            try:
                self.close()
            except LimeSurveyError:
                if kind is None:
                    raise

    def _call(self, context: str, operation: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        with _account_slot(self.account_id, self.settings.max_concurrent_calls):
            try:
                return operation(*args, **kwargs)
            except Exception as error:
                raise classify(error, context) from error

    def _call_with_retry(
        self, context: str, operation: Callable[..., T], *args: Any, **kwargs: Any
    ) -> T:
        attempts = max(1, self.settings.max_attempts)
        for attempt in range(attempts):
            try:
                with _account_slot(self.account_id, self.settings.max_concurrent_calls):
                    return operation(*args, **kwargs)
            except (requests.Timeout, requests.ConnectionError) as error:
                if attempt == attempts - 1:
                    raise classify(error, context) from error
                delay = min(self.settings.backoff_max, self.settings.backoff_base * 2**attempt)
                time.sleep(delay + random.uniform(0, delay * self.settings.backoff_jitter))  # noqa: S311
            except Exception as error:
                raise classify(error, context) from error
        raise LimeSurveyError(f"Unexpected retry state while {context}.")

    def list_surveys(self) -> list[dict[str, Any]]:
        surveys: list[Any] = self._call("listing surveys", self._citric.list_surveys)
        return [dict(survey) for survey in surveys]

    def get_survey_load_result(self, survey_id: int, language: str | None = None) -> dict[str, Any]:
        """Load a survey and normalize it to a ``SurveyLoadResult``.

        Raises ``LimeSurveyTimeoutError`` (code ``LS_SURVEY_LOAD_TIMEOUT``) after
        ``settings.survey_load_timeout`` seconds.
        """
        deadline = time.monotonic() + self.settings.survey_load_timeout
        with ThreadPoolExecutor(max_workers=max(1, self.settings.max_concurrent_calls)) as pool:
            properties = self._call(
                "loading survey properties",
                self._citric.get_survey_properties,
                survey_id,
                SURVEY_SETTINGS,
            )
            selected = language or properties.get("language")
            available = _available_languages(properties)
            if language and language not in available:
                raise SurveyLanguageNotAvailableError(
                    f"Language {language} is not available ({', '.join(available)})."
                )
            language_future = pool.submit(
                self._call,
                "loading survey texts",
                self._citric.get_language_properties,
                survey_id,
                settings=SURVEY_LANGUAGE_SETTINGS,
                language=selected,
            )
            groups_future = pool.submit(
                self._call, "listing question groups", self._citric.list_groups, survey_id, selected
            )
            language_properties, groups = _gather([language_future, groups_future], deadline)
            if not groups:
                raise SurveyNotFoundError(f"No groups found for survey ID {survey_id}")
            questions = self._load_questions(pool, survey_id, groups, selected, deadline)
        payload = {
            "survey": properties,
            "language": language_properties,
            "groups": groups,
            "questions": questions,
            "source": {
                "selectedLanguage": selected,
                "availableLanguages": available,
            },
            "completion_context": _response_state(
                {**properties, "language": selected}, language_properties
            ),
        }
        try:
            return build_survey_structure(payload, source_format="remotecontrol")
        except SurveyLanguageError as error:
            raise SurveyLanguageNotAvailableError(str(error)) from error

    def _list_group_questions(
        self, survey_id: int, group_id: Any, language: str | None
    ) -> list[Any]:
        """Questions of one group; LimeSurvey reports an empty group as an error status."""
        try:
            rows = [
                dict(row) for row in self._citric.list_questions(survey_id, int(group_id), language)
            ]
        except LimeSurveyStatusError as error:
            if "no questions found" in str(error).casefold():
                return []
            raise
        return select_language_rows(rows, language, "qid")

    def _load_questions(
        self,
        pool: ThreadPoolExecutor,
        survey_id: int,
        groups: list[dict[str, Any]],
        language: str | None,
        deadline: float,
    ) -> list[dict[str, Any]]:
        group_futures = [
            pool.submit(
                self._call_with_retry,
                "listing questions",
                self._list_group_questions,
                survey_id,
                group["gid"],
                language,
            )
            for group in groups
        ]
        grouped = _gather(group_futures, deadline)
        property_futures = [
            [
                pool.submit(
                    self._call_with_retry,
                    "loading question properties",
                    self._citric.get_question_properties,
                    question["qid"],
                    language=language,
                )
                for question in questions or []
            ]
            for questions in grouped
        ]
        questions: list[dict[str, Any]] = []
        for group, group_questions, futures in zip(groups, grouped, property_futures, strict=True):
            relevance = str(group.get("grelevance") or "1").strip() or "1"
            for question, result in zip(
                group_questions or [], _gather(futures, deadline), strict=True
            ):
                questions.append(
                    {
                        **question,
                        **result,
                        "grelevance": relevance,
                        "full_condition": f"({relevance}) AND ({result.get('condition', '1')})",
                    }
                )
        return questions + self._load_missing_children(
            pool, survey_id, questions, language, deadline
        )

    def _load_missing_children(
        self,
        pool: ThreadPoolExecutor,
        survey_id: int,
        questions: list[dict[str, Any]],
        language: str | None,
        deadline: float,
    ) -> list[dict[str, Any]]:
        """Subquestions LimeSurvey lists under a stale or missing group.

        Their parent still names them, so their full properties are loaded: the summary
        embedded in the parent lacks order and relevance (as limesurvey-rc2-api does).
        """
        known = {str(question["qid"]) for question in questions}
        missing: dict[str, str] = {}
        for question in questions:
            children = question.get("subquestions")
            if isinstance(children, dict):
                for child_id in children:
                    if str(child_id) not in known:
                        missing[str(child_id)] = str(question["qid"])
        futures = [
            pool.submit(
                self._call_with_retry,
                "loading question properties",
                self._citric.get_question_properties,
                int(child_id),
                language=language,
            )
            for child_id in missing
        ]
        children_found: list[dict[str, Any]] = []
        for (child_id, parent_id), child in zip(
            missing.items(), _gather(futures, deadline), strict=True
        ):
            if (
                str(child.get("qid")) != child_id
                or str(child.get("parent_qid")) != parent_id
                or str(child.get("sid")) != str(survey_id)
            ):
                raise SurveyStructureSourceError(
                    f"Subquestion {child_id} does not belong to question {parent_id} in survey {survey_id}."
                )
            children_found.append(dict(child))
        return children_found

    def get_dictionary(
        self,
        survey_id: int,
        language: str | None = None,
        *,
        aliases: Mapping[str, str] | None = None,
        include_system_fields: bool = False,
        include_timing_fields: bool = False,
    ) -> SurveyDictionary:
        loaded = self.get_survey_load_result(survey_id, language)
        return build_limesurvey_dictionary(
            loaded["survey"],
            aliases=aliases,
            source_issues=loaded["issues"],
            include_system_fields=include_system_fields,
            include_timing_fields=include_timing_fields,
        )

    def get_field(
        self, survey_id: int, question_code: str, language: str | None = None
    ) -> dict[str, Any] | None:
        """One question's SurveyStructure field and dictionary entries, or ``None`` if absent."""
        loaded = self.get_survey_load_result(survey_id, language)
        return field_detail(loaded, question_code)

    def export_responses(
        self,
        survey_id: int,
        *,
        file_format: Literal["json", "csv"] = "json",
        language: str | None = None,
        completion_status: CompletionStatus = "all",
        heading_type: HeadingType = "code",
        response_type: ResponseType = "short",
        from_response_id: int | None = None,
        to_response_id: int | None = None,
        fields: Sequence[str] | None = None,
    ) -> dict[str, Any] | bytes:
        """Export responses: a ``SurveyResponseDataset`` for JSON, the raw file for CSV."""
        if fields is not None and len(fields) > self.settings.responses_max_fields:
            raise ValueError(
                f"At most {self.settings.responses_max_fields} response fields may be requested."
            )
        content = self._call(
            f"exporting responses for sid {survey_id}",
            self._citric.export_responses,
            survey_id,
            file_format=file_format,
            language=language,
            completion_status=completion_status,
            heading_type=heading_type,
            response_type=response_type,
            from_response_id=from_response_id,
            to_response_id=to_response_id,
            fields=list(fields) if fields else None,
        )
        return decode_response_export(
            content, survey_id, file_format, language, self.settings.responses_max_bytes
        )

    def translate_responses(
        self,
        survey_id: int,
        language: str | None = None,
        *,
        aliases: Mapping[str, str] | None = None,
        completion_status: CompletionStatus = "all",
        from_response_id: int | None = None,
        to_response_id: int | None = None,
    ) -> TranslatedDataset:
        """Export responses as JSON and translate them with the survey dictionary."""
        dictionary = self.get_dictionary(survey_id, language, aliases=aliases)
        dataset = self.export_responses(
            survey_id,
            language=language,
            completion_status=completion_status,
            from_response_id=from_response_id,
            to_response_id=to_response_id,
        )
        assert isinstance(dataset, dict)  # noqa: S101
        return translate_records(dictionary, dataset["responses"])


def decode_response_export(
    content: object, survey_id: int, file_format: str, language: str | None, max_bytes: int
) -> dict[str, Any] | bytes:
    """Check size and shape of an export (port of limesurvey-rc2-api ``remote_response_loader``)."""
    if not isinstance(content, bytes):
        raise InvalidResponseExportError("LimeSurvey response export did not return bytes.")
    if len(content) > max_bytes:
        raise ResponseExportTooLargeError(
            f"LimeSurvey response export exceeds the configured {max_bytes}-byte limit."
        )
    if file_format == "csv":
        return content
    try:
        decoded = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InvalidResponseExportError(
            "LimeSurvey returned an invalid JSON response export."
        ) from error
    responses = decoded.get("responses") if isinstance(decoded, dict) else None
    if not isinstance(responses, list) or not all(isinstance(item, dict) for item in responses):
        raise InvalidResponseExportError(
            'LimeSurvey JSON export must contain a "responses" array of objects.'
        )
    # LimeSurvey wraps each response in an object keyed by its id: {"responses": [{"12": {...}}]}.
    wrapped = bool(responses) and all(
        len(item) == 1 and isinstance(next(iter(item.values())), dict) for item in responses
    )
    records = [next(iter(item.values())) if wrapped else item for item in responses]
    dataset: dict[str, Any] = {"surveyId": str(survey_id)}
    if language is not None:
        dataset["language"] = language
    dataset["responses"] = [underscore_record(record) for record in records]
    if wrapped:
        dataset["responseIds"] = [str(next(iter(item))) for item in responses]
    if not safe_parse_survey_response_dataset(dataset).success:
        raise InvalidResponseExportError(
            "LimeSurvey returned values that are not valid JSON response data."
        )
    return dataset


def field_detail(load_result: Mapping[str, Any], question_code: str) -> dict[str, Any] | None:
    """Find a question (including children of custom fields) and its dictionary entries."""
    code = question_code.strip()

    def find(fields: list[dict[str, Any]]) -> dict[str, Any] | None:
        for field in fields:
            if field["code"] == code:
                return field
            if field["type"] == "custom":
                found = find(field["childrenFields"])
                if found is not None:
                    return found
        return None

    survey = load_result["survey"]
    field = find(survey["fields"])
    if field is None:
        return None
    dictionary = build_limesurvey_dictionary(survey, source_issues=load_result.get("issues", []))
    return {
        "surveyId": survey["id"],
        "field": field,
        "dictionary": get_question_dictionary(dictionary, code),
        "issues": [
            issue for issue in load_result.get("issues", []) if issue.get("questionCode") == code
        ],
    }


def _gather(futures: Sequence[Future[Any]], deadline: float) -> list[Any]:
    remaining = deadline - time.monotonic()
    done, pending = wait(futures, timeout=max(0.0, remaining), return_when=FIRST_EXCEPTION)
    for future in done:
        error = future.exception()
        if error is not None:
            for other in pending:
                other.cancel()
            raise error
    if pending:
        for future in pending:
            future.cancel()
        raise LimeSurveyTimeoutError(
            "LimeSurvey did not finish loading the survey within the configured timeout.",
            "LS_SURVEY_LOAD_TIMEOUT",
        )
    return [future.result() for future in futures]


def _response_state(
    properties: Mapping[str, Any], language_properties: Mapping[str, Any]
) -> dict[str, Any]:
    active = str(properties.get("active") or "").strip().upper() == "Y"
    return {
        "active": active,
        "canSaveResponses": active,
        "submitMode": "submit" if active else "submit_preview",
        "language": properties.get("language"),
        "endText": language_properties.get("surveyls_endtext", "") or "",
        "warningCodes": [] if active else ["SURVEY_NOT_ACTIVE_PREVIEW"],
        "didNotSaveCode": None if active else "SURVEY_NOT_ACTIVE_NOT_RECORDED",
    }


def _available_languages(properties: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    base = str(properties.get("language") or "").strip()
    if base:
        values.append(base)
    additional = properties.get("additional_languages")
    candidates = (
        additional
        if isinstance(additional, list)
        else re.split(r"[\s,;]+", str(additional or "").strip())
    )
    for candidate in candidates:
        normalized = str(candidate or "").strip()
        if normalized and normalized not in values:
            values.append(normalized)
    return values
