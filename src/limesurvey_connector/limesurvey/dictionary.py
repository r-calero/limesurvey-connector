"""Dictionaries as the connector serves them: LimeSurvey column names, optional system and timing columns."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from limesurvey_connector.limesurvey.naming import with_limesurvey_names
from limesurvey_connector.limesurvey.responses import timing_columns, with_system_fields
from survey_data_dictionary import SurveyDictionary, build_survey_dictionary


def build_limesurvey_dictionary(
    structure: Any,
    *,
    aliases: Mapping[str, str] | None = None,
    source_issues: Sequence[Mapping[str, Any]] | None = None,
    include_system_fields: bool = False,
    include_timing_fields: bool = False,
) -> SurveyDictionary:
    dictionary = with_limesurvey_names(
        build_survey_dictionary(structure, aliases=aliases, source_issues=source_issues)
    )
    if include_system_fields:
        return with_system_fields(dictionary, include_timing=include_timing_fields)
    if include_timing_fields:
        return with_system_fields(dictionary, timing_columns(dictionary))
    return dictionary
