"""Offline LimeSurvey sources: .lss import, normalization and response exports."""

from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import Any

from limesurvey_connector.limesurvey.normalization import (
    SurveyStructureContractError,
    SurveyStructureSourceError,
    build_survey_structure,
    survey_structure_from_lss,
)


def load_lss(source: bytes | str | PathLike[str], language: str | None = None) -> dict[str, Any]:
    """Read a LimeSurvey ``.lss`` export (bytes or a path) into a ``SurveyLoadResult``.

    Raises ``SurveyStructureSourceError`` for unreadable or unsupported files.
    """
    content = source if isinstance(source, bytes) else Path(source).read_bytes()
    return survey_structure_from_lss(content, language)


__all__ = [
    "SurveyStructureContractError",
    "SurveyStructureSourceError",
    "build_survey_structure",
    "load_lss",
    "survey_structure_from_lss",
]
