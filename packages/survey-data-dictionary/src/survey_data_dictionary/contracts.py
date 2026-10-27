"""Dictionary and translation contracts (port of survey-data-dictionary ``contracts.ts``)."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

from survey_structure.engine import UNDEFINED

# Response types moved to survey-structure 2.1.0; they stay importable from here, as in the npm package.
from survey_structure.types import SurveyResponseRecord as SurveyResponseRecord
from survey_structure.types import SurveyResponseScalar as SurveyResponseScalar
from survey_structure.types import SurveyResponseValue as SurveyResponseValue

# Marks an absent optional value (JavaScript ``undefined``); ``None`` is JSON ``null``.
ABSENT: Any = UNDEFINED

type DictionaryDataType = Literal["string", "number", "date", "boolean", "code"]
type DictionaryCardinality = Literal["single", "multiple"]


class DictionaryValue(TypedDict):
    code: str
    label: str


class DictionaryField(TypedDict):
    questionCode: str
    questionLabel: str
    responseKey: str
    dataType: DictionaryDataType
    cardinality: DictionaryCardinality
    values: NotRequired[list[DictionaryValue]]
    aliases: NotRequired[list[str]]
    parentCode: NotRequired[str]
    qid: NotRequired[str]
    groupId: NotRequired[str]


class DictionaryIssue(TypedDict):
    level: Literal["warning", "error"]
    code: str
    message: str
    questionCode: NotRequired[str]
    responseKey: NotRequired[str]
    responseIndex: NotRequired[int]
    details: NotRequired[dict[str, Any]]


class SurveyDictionary(TypedDict):
    surveyStructureVersion: Literal["2.1.0"]
    surveyId: str
    surveyTitle: NotRequired[str]
    language: NotRequired[str]
    fields: list[DictionaryField]
    issues: list[DictionaryIssue]


class TranslatedResponseField(TypedDict):
    responseKey: str
    questionCode: str
    questionLabel: str
    dataType: DictionaryDataType
    sourceValue: Any
    displayValue: Any
    missing: bool


class UnmappedResponseValue(TypedDict):
    sourceKey: str
    sourceValue: SurveyResponseValue
    columnIndex: NotRequired[int]


class TranslatedResponse(TypedDict):
    responseIndex: int
    responseId: NotRequired[SurveyResponseScalar]
    fields: list[TranslatedResponseField]
    unmappedValues: list[UnmappedResponseValue]
    issues: list[DictionaryIssue]


class TranslatedDataset(TypedDict):
    responses: list[TranslatedResponse]
    issues: list[DictionaryIssue]


class SurveyDictionaryValidationError(ValueError):
    """Raised by ``build_survey_dictionary(strict=True)`` when the dictionary has errors."""

    def __init__(self, issues: list[DictionaryIssue]) -> None:
        self.issues = issues
        super().__init__("Survey definition contains dictionary validation errors.")
