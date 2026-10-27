"""Language tag syntax check equivalent to the reference ``surveyLanguageSchema``.

The reference accepts private-use tags (``x-...``) and anything
``Intl.getCanonicalLocales`` accepts, which is a structurally valid Unicode
BCP 47 locale identifier (UTS #35) with ``-`` separators.
"""

from __future__ import annotations

import re

_PRIVATE_USE_ONLY = re.compile(r"^x(?:-[a-z0-9]{1,8})+\Z", re.IGNORECASE | re.ASCII)
_ALPHA = re.compile(r"^[a-z]+\Z", re.IGNORECASE | re.ASCII)
_DIGIT = re.compile(r"^[0-9]+\Z", re.ASCII)
_ALPHANUM = re.compile(r"^[a-z0-9]+\Z", re.IGNORECASE | re.ASCII)


def _alpha(value: str, *sizes: int) -> bool:
    return len(value) in sizes and bool(_ALPHA.match(value))


def _alphanum(value: str, low: int, high: int) -> bool:
    return low <= len(value) <= high and bool(_ALPHANUM.match(value))


def _is_language(value: str) -> bool:
    return _alpha(value, 2, 3, 5, 6, 7, 8)


def _is_script(value: str) -> bool:
    return _alpha(value, 4)


def _is_region(value: str) -> bool:
    return _alpha(value, 2) or (len(value) == 3 and bool(_DIGIT.match(value)))


def _is_variant(value: str) -> bool:
    if _alphanum(value, 5, 8):
        return True
    return len(value) == 4 and value[0].isdigit() and bool(_ALPHANUM.match(value))


def _language_id(parts: list[str], start: int) -> int | None:
    """Parse unicode_language_id; return the index after it, or ``None``."""
    if start >= len(parts) or not _is_language(parts[start]):
        return None
    index = start + 1
    if index < len(parts) and _is_script(parts[index]):
        index += 1
    if index < len(parts) and _is_region(parts[index]):
        index += 1
    variants: set[str] = set()
    while index < len(parts) and _is_variant(parts[index]):
        variant = parts[index].lower()
        if variant in variants:
            return None
        variants.add(variant)
        index += 1
    return index


def _is_singleton(value: str) -> bool:
    return len(value) == 1 and bool(_ALPHANUM.match(value))


def _unicode_extension(parts: list[str], index: int) -> int | None:
    start = index
    while index < len(parts) and _alphanum(parts[index], 3, 8):
        index += 1
    while (
        index < len(parts)
        and len(parts[index]) == 2
        and parts[index][1].isalpha()
        and bool(_ALPHANUM.match(parts[index]))
    ):
        index += 1
        while index < len(parts) and _alphanum(parts[index], 3, 8):
            index += 1
    return index if index > start else None


def _transformed_extension(parts: list[str], index: int) -> int | None:
    start = index
    if index < len(parts) and _is_language(parts[index]):
        end = _language_id(parts, index)
        if end is None:
            return None
        index = end
    while (
        index < len(parts)
        and len(parts[index]) == 2
        and parts[index][0].isalpha()
        and parts[index][1].isdigit()
    ):
        index += 1
        values = index
        while index < len(parts) and _alphanum(parts[index], 3, 8):
            index += 1
        if index == values:
            return None
    return index if index > start else None


def _other_extension(parts: list[str], index: int) -> int | None:
    start = index
    while index < len(parts) and _alphanum(parts[index], 2, 8):
        index += 1
    return index if index > start else None


def _private_use(parts: list[str], index: int) -> int | None:
    start = index
    while index < len(parts) and _alphanum(parts[index], 1, 8):
        index += 1
    return index if index > start else None


def is_structurally_valid_locale(tag: str) -> bool:
    parts = tag.split("-")
    if any(not part for part in parts):
        return False
    index = _language_id(parts, 0)
    if index is None:
        return False
    singletons: set[str] = set()
    while index < len(parts):
        singleton = parts[index].lower()
        if not _is_singleton(singleton) or singleton in singletons:
            return False
        singletons.add(singleton)
        index += 1
        if singleton == "x":
            end = _private_use(parts, index)
        elif singleton == "u":
            end = _unicode_extension(parts, index)
        elif singleton == "t":
            end = _transformed_extension(parts, index)
        else:
            end = _other_extension(parts, index)
        if end is None:
            return False
        index = end
        if singleton == "x" and index < len(parts):
            return False
    return True


def is_valid_language_tag(tag: str) -> bool:
    return bool(_PRIVATE_USE_ONLY.match(tag)) or is_structurally_valid_locale(tag)
