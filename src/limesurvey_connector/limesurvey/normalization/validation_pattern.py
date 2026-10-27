"""Read the common PCRE/ECMAScript subset without repairing the source expression."""

from __future__ import annotations

import re
from typing import Any


def portable_text_pattern(value: str) -> dict[str, Any] | None:
    # These unpaired delimiters and flags need no rewrite of the regex body.
    # Other PCRE features remain a diagnosed source rule, not a guessed equivalent.
    if not value or value[0] not in "/#~%!@":
        return None
    end = value.rfind(value[0])
    if end <= 0:
        return None
    source, flags = value[1:end], value[end + 1 :]
    if re.search(r"(?<!\\)(?:\\\\)*" + re.escape(value[0]), source):
        return None
    if len(set(flags)) != len(flags) or any(flag not in "ims" for flag in flags):
        return None
    if re.search(r"\[\[:|\(\*(?:.)|\(\?(?![:=!])|(?:[+*?]|\})\+", source):
        return None
    # Keep escapes explicit: Python accepting an escape does not make it PCRE/JS
    # compatible (for example \a, \u, or Unicode whitespace via \s).
    position, in_class = 0, False
    while position < len(source):
        char = source[position]
        if char == "\\":
            position += 1
            if (
                position == len(source)
                or source[position] not in r"\.^$|?*+()[]{}-/ #~%!@bBfnrtdDwW"
            ):
                return None
        elif char == "[":
            in_class = True
        elif char == "]":
            in_class = False
        elif char == "{" and not in_class:
            quantifier = re.match(r"\{([0-9]+)(?:,([0-9]*))?\}", source[position:])
            if not quantifier:
                return None
            for bound in quantifier.groups():
                digits = (bound or "").lstrip("0") or "0"
                if len(digits) > 5 or int(digits) > 65535:
                    return None
        position += 1
    try:
        re.compile(source, sum({"i": re.I, "m": re.M, "s": re.S}[flag] for flag in flags))
    except (re.error, OverflowError):
        return None
    return {"responseFormatPattern": source, **({"patternFlags": flags} if flags else {})}
