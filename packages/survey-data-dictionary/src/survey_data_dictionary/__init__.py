"""Data dictionaries and response translation, ported from the survey-data-dictionary npm package."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from survey_data_dictionary.contracts import (
    ABSENT,
    DictionaryField,
    DictionaryIssue,
    DictionaryValue,
    SurveyDictionary,
    SurveyDictionaryValidationError,
    TranslatedDataset,
    TranslatedResponse,
    TranslatedResponseField,
    UnmappedResponseValue,
)
from survey_data_dictionary.csv import (
    dictionary_to_csv,
    translated_dataset_to_csv,
    translated_response_to_csv,
)
from survey_data_dictionary.dataset import (
    TabularDatasetMapping,
    map_tabular_dataset,
    normalize_header,
)
from survey_data_dictionary.dictionary import build_survey_dictionary, get_question_dictionary
from survey_data_dictionary.schemas import (
    safe_parse_survey_dictionary,
    safe_parse_survey_response_dataset,
    safe_parse_survey_response_record,
)
from survey_data_dictionary.translation import translate_dataset, translate_response

try:
    __version__ = version("survey-data-dictionary")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

# The npm release and commit whose behavior this package reproduces.
UPSTREAM = {
    "package": "survey-data-dictionary",
    "version": "2.1.0",
    "commit": "99b1bd12fd1dee1562c3a5480289db13e45b2dd5",
    "repository": "https://github.com/JJKid/survey-data-dictionary",
}

__all__ = [
    "ABSENT",
    "UPSTREAM",
    "DictionaryField",
    "DictionaryIssue",
    "DictionaryValue",
    "SurveyDictionary",
    "SurveyDictionaryValidationError",
    "TabularDatasetMapping",
    "TranslatedDataset",
    "TranslatedResponse",
    "TranslatedResponseField",
    "UnmappedResponseValue",
    "build_survey_dictionary",
    "dictionary_to_csv",
    "get_question_dictionary",
    "map_tabular_dataset",
    "normalize_header",
    "safe_parse_survey_dictionary",
    "safe_parse_survey_response_dataset",
    "safe_parse_survey_response_record",
    "translate_dataset",
    "translate_response",
    "translated_dataset_to_csv",
    "translated_response_to_csv",
]
