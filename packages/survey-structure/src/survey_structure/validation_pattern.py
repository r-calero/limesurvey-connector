"""``validationPatternSource``: the response-format pattern exactly as written."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def validation_pattern_source(rules: Mapping[str, Any]) -> str:
    """Return the supplied response-format pattern without adding or changing anchors."""
    pattern = rules.get("responseFormatPattern")
    return pattern if isinstance(pattern, str) else ""
