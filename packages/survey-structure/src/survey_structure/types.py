"""Static types for SurveyStructure documents. Validation lives in ``schemas``."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

type JsonScalar = str | int | float | bool
type JsonPrimitive = JsonScalar | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]

type FieldType = Literal[
    "short-text",
    "long-text",
    "number",
    "date",
    "yes-no",
    "gender",
    "single-choice",
    "list-with-comment",
    "multiple-choice",
    "multiple-choice-with-comments",
    "matrix",
    "multiple-input",
    "ranking",
    "display",
    "boolean",
    "range",
    "custom",
]
type DateValueType = Literal["date", "month-year", "month-day", "date-time", "time", "year"]
type Operator = Literal[
    "equals",
    "not-equals",
    "greater-than",
    "greater-than-or-equal",
    "less-than",
    "less-than-or-equal",
]


class SurveyGrading(TypedDict):
    points: float
    correctAnswers: list[JsonPrimitive]
    whenRight: NotRequired[str]
    whenWrong: NotRequired[str]
    generalFeedback: NotRequired[str]


class SurveyConditionReference(TypedDict):
    fieldCode: str
    responseItemCode: NotRequired[str]


class SurveyCondition(TypedDict, total=False):
    """Condition tree node; the keys present depend on ``type``."""

    type: Literal[
        "comparison",
        "answered",
        "not-answered",
        "pattern-match",
        "selection-count",
        "answered-count",
        "numeric-aggregate",
        "constant",
        "all",
        "any",
        "not",
    ]
    responseReference: SurveyConditionReference
    responseItemCodes: list[str]
    operator: Operator
    aggregation: Literal["sum", "min", "max"]
    value: JsonPrimitive
    pattern: str
    patternFlags: str
    conditions: list[SurveyCondition]
    condition: SurveyCondition


class SurveyStructureVisibility(TypedDict):
    condition: SurveyCondition


class SurveyStructureOption(TypedDict):
    code: str
    label: str
    commentResponseKey: NotRequired[str]
    exclusive: NotRequired[bool]
    visibility: NotRequired[SurveyStructureVisibility]
    order: NotRequired[int]


class SurveyStructureSubquestion(TypedDict):
    id: NotRequired[str]
    code: str
    label: str
    order: NotRequired[int]


class SurveyStructureMatrixItem(TypedDict):
    code: str
    label: str
    visibility: NotRequired[SurveyStructureVisibility]
    order: NotRequired[int]


class SurveyStructureMatrixRow(SurveyStructureMatrixItem):
    grading: NotRequired[SurveyGrading]
    required: NotRequired[bool]


class SurveyStructureScaleColumn(SurveyStructureMatrixItem):
    options: list[SurveyStructureMatrixItem]


class SurveyStructureMatrixCell(TypedDict):
    rowCode: str
    columnCode: str
    visibility: SurveyStructureVisibility


class SurveyStructureMatrix(TypedDict):
    mode: Literal["single", "multiple", "text", "number", "dual-single"]
    rows: list[SurveyStructureMatrixRow]
    columns: list[SurveyStructureMatrixItem] | list[SurveyStructureScaleColumn]
    cells: NotRequired[list[SurveyStructureMatrixCell]]


class SurveyStructureResponseValidation(TypedDict, total=False):
    min: float
    max: float
    dateMin: str
    dateMax: str
    rangeBehavior: Literal["warning", "error"]
    minLength: int
    maxLength: int
    minSelections: int
    maxSelections: int
    minAnswers: int
    maxAnswers: int
    integer: bool
    numericText: bool
    itemMin: float
    itemMax: float
    sumMin: float
    sumMax: float
    sumEquals: float
    itemMinReference: str
    itemMaxReference: str
    sumMinReference: str
    sumMaxReference: str
    sumEqualsReference: str
    sumAllowsMissing: bool
    responseFormatPattern: str
    patternFlags: str
    messages: dict[str, str]


class SurveyStructureRendering(TypedDict, total=False):
    widget: str
    placeholder: str
    showLabel: bool
    disabled: bool
    hidden: bool
    inputType: str
    inputMode: str
    dateOrder: Literal["date-time", "time-date"]
    dateFormat: Literal["dmy", "mdy", "ymd"]
    dateDropdowns: bool
    monthLabelStyle: Literal["short", "long", "numeric"]
    reverseYearOrder: bool
    yearMin: int
    yearMax: int
    randomizationGroup: str
    searchable: bool
    optionsLayout: Literal["horizontal", "vertical"]
    ratingIcon: Literal["star", "heart", "thumb-up"]
    scaleMinLabel: str
    scaleMaxLabel: str


class SurveyStructureResponseEncoding(TypedDict):
    selectedValue: JsonScalar
    unselectedValue: JsonScalar
    selectedLabel: NotRequired[str]
    unselectedLabel: NotRequired[str]


class SurveyStructureOtherResponse(TypedDict):
    code: str
    label: str
    textResponseKey: str
    commentResponseKey: NotRequired[str]
    textRequired: NotRequired[bool]
    commentRequired: NotRequired[bool]


class SurveyStructureOriginDetails(TypedDict, total=False):
    """Platform-specific traceability; the other keys depend on ``type``."""

    type: str
    version: str


class SurveyStructureFieldSource(TypedDict):
    platform: str
    surveyId: NotRequired[str]
    groupId: NotRequired[str]
    questionId: NotRequired[str]
    nativeType: NotRequired[str]
    responseAliases: NotRequired[list[dict[str, Any]]]
    originDetails: NotRequired[list[SurveyStructureOriginDetails]]


class SurveyStructureField(TypedDict):
    """Any field variant. Variant-specific keys are present only for their types."""

    id: str
    code: str
    type: FieldType
    label: str
    groupId: NotRequired[str]
    parentId: NotRequired[str]
    help: NotRequired[str]
    images: NotRequired[list[dict[str, str]]]
    required: NotRequired[bool]
    grading: NotRequired[SurveyGrading]
    order: NotRequired[int]
    responseValidation: NotRequired[SurveyStructureResponseValidation]
    visibility: NotRequired[SurveyStructureVisibility]
    rendering: NotRequired[SurveyStructureRendering]
    responseEncoding: NotRequired[SurveyStructureResponseEncoding]
    source: NotRequired[SurveyStructureFieldSource]
    options: NotRequired[list[SurveyStructureOption]]
    commentResponseKey: NotRequired[str]
    other: NotRequired[SurveyStructureOtherResponse]
    matrix: NotRequired[SurveyStructureMatrix]
    subquestions: NotRequired[list[SurveyStructureSubquestion]]
    dateValueType: NotRequired[DateValueType]
    responseValueType: NotRequired[Literal["number", "text"]]
    childrenFields: NotRequired[list[SurveyStructureField]]
    defaultValue: NotRequired[Any]


class SurveyStructureGroup(TypedDict):
    id: str
    title: NotRequired[str]
    description: NotRequired[str]
    order: int
    randomizationGroup: NotRequired[str]
    visibility: NotRequired[SurveyStructureVisibility]
    source: NotRequired[dict[str, Any]]
    navigation: NotRequired[list[dict[str, Any]]]


class SurveyStructure(TypedDict):
    surveyStructureVersion: Literal["2.1.0"]
    id: str
    title: NotRequired[str]
    description: NotRequired[str]
    language: NotRequired[str]
    availableLanguages: NotRequired[list[str]]
    groups: NotRequired[list[SurveyStructureGroup]]
    fields: list[SurveyStructureField]
    settings: NotRequired[dict[str, Any]]
    source: NotRequired[dict[str, Any]]


class SurveyStructureIssue(TypedDict):
    level: Literal["warning", "error"]
    code: str
    message: str
    fieldId: NotRequired[str]
    questionCode: NotRequired[str]
    details: NotRequired[dict[str, Any]]


class SurveyLoadResult(TypedDict):
    survey: SurveyStructure
    issues: list[SurveyStructureIssue]
    responseState: NotRequired[dict[str, Any]]
    sourceMetrics: NotRequired[dict[str, Any]]


type SurveyResponseScalar = str | int | float | bool | None
type SurveyResponseValue = JsonValue
type SurveyResponseRecord = dict[str, SurveyResponseValue]
