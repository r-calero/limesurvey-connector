"""Schema combinators with the parsing semantics of Zod 3.

The reference contract is written with Zod. Reproducing its evaluation order,
union resolution and refinement rules is what keeps issue paths identical, so
this module mirrors Zod's behavior rather than using a general validation library.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from survey_structure import _js
from survey_structure._js import UNDEFINED
from survey_structure._url import can_parse_url

Issue = dict[str, Any]
Path = list[str | int]
Status = Literal["valid", "dirty", "aborted"]


@dataclass(frozen=True, slots=True)
class Outcome:
    status: Status
    value: Any = UNDEFINED


ABORTED = Outcome("aborted")


def parsed_type(data: object) -> str:
    if data is UNDEFINED:
        return "undefined"
    if isinstance(data, bool):
        return "boolean"
    if isinstance(data, str):
        return "string"
    if _js.is_number(data):
        return "nan" if isinstance(data, float) and math.isnan(data) else "number"
    if data is None:
        return "null"
    if isinstance(data, list):
        return "array"
    if isinstance(data, dict):
        return "object"
    return "unknown"


def _bound(issue: Issue, key: str) -> str:
    return _js.to_string(issue[key])


def default_message(issue: Issue) -> str:
    code = issue["code"]
    if code == "invalid_type":
        if issue["received"] == "undefined":
            return "Required"
        return f"Expected {issue['expected']}, received {issue['received']}"
    if code == "invalid_literal":
        return f"Invalid literal value, expected {_js.stringify(issue['expected'])}"
    if code == "unrecognized_keys":
        return f"Unrecognized key(s) in object: {_js.join_values(issue['keys'], ', ')}"
    if code == "invalid_union":
        return "Invalid input"
    if code == "invalid_union_discriminator":
        return f"Invalid discriminator value. Expected {_js.join_values(issue['options'])}"
    if code == "invalid_enum_value":
        return (
            f"Invalid enum value. Expected {_js.join_values(issue['options'])}, "
            f"received '{_js.to_string(issue['received'])}'"
        )
    if code == "invalid_string":
        return "Invalid" if issue["validation"] == "regex" else f"Invalid {issue['validation']}"
    if code in ("too_small", "too_big"):
        return _size_message(issue)
    if code == "not_finite":
        return "Number must be finite"
    return "Invalid input"


def _size_message(issue: Issue) -> str:
    small = issue["code"] == "too_small"
    kind, exact, inclusive = issue["type"], issue.get("exact"), issue.get("inclusive")
    bound = _bound(issue, "minimum" if small else "maximum")
    if kind in ("array", "string"):
        noun = "element(s)" if kind == "array" else "character(s)"
        if exact:
            qualifier = "exactly"
        elif small:
            qualifier = "at least" if inclusive else ("more than" if kind == "array" else "over")
        else:
            qualifier = "at most" if inclusive else ("less than" if kind == "array" else "under")
        subject = "Array" if kind == "array" else "String"
        return f"{subject} must contain {qualifier} {bound} {noun}"
    if kind == "number":
        if small:
            prefix = (
                "exactly equal to "
                if exact
                else "greater than or equal to "
                if inclusive
                else "greater than "
            )
            return f"Number must be {prefix}{bound}"
        suffix = "exactly" if exact else "less than or equal to" if inclusive else "less than"
        return f"Number must be {suffix} {bound}"
    return "Invalid input"


def add_issue(issues: list[Issue], path: Path, data: Issue) -> None:
    """Build an issue as Zod does; undefined properties are omitted like in JSON."""
    extra_path = data.pop("path", UNDEFINED) or []
    message = data.pop("message", None)
    issue = {key: value for key, value in data.items() if value is not UNDEFINED}
    issue["path"] = [*path, *extra_path]
    issue["message"] = default_message(issue) if message is None else message
    issues.append(issue)


class Schema:
    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        raise NotImplementedError

    def optional(self) -> Schema:
        return Optional(self)

    def refine(
        self, check: Callable[[Any], bool], message: str, path: Sequence[str | int] | None = None
    ) -> Schema:
        def refinement(value: Any, report: Callable[[Issue], None]) -> None:
            if not check(value):
                issue: Issue = {"code": "custom", "message": message}
                if path:
                    issue["path"] = list(path)
                report(issue)

        return Effects(self, refinement)

    def super_refine(self, refinement: Callable[[Any, Callable[[Issue], None]], None]) -> Schema:
        return Effects(self, refinement)


class Unknown(Schema):
    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        return Outcome("valid", data)


class Default(Schema):
    def __init__(self, inner: Schema, value: Callable[[], Any]) -> None:
        self.inner = inner
        self.value = value

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        return self.inner.parse(self.value() if data is UNDEFINED else data, path, issues)


class Optional(Schema):
    def __init__(self, inner: Schema) -> None:
        self.inner = inner

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        if data is UNDEFINED:
            return Outcome("valid", UNDEFINED)
        return self.inner.parse(data, path, issues)


class Nullable(Schema):
    def __init__(self, inner: Schema) -> None:
        self.inner = inner

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        if data is None:
            return Outcome("valid", None)
        return self.inner.parse(data, path, issues)


def _invalid_type(issues: list[Issue], path: Path, expected: str, data: Any) -> Outcome:
    add_issue(
        issues, path, {"code": "invalid_type", "expected": expected, "received": parsed_type(data)}
    )
    return ABORTED


class String(Schema):
    def __init__(self) -> None:
        self.checks: list[tuple[str, Any, str | None]] = []

    def _with(self, check: tuple[str, Any, str | None]) -> String:
        copy = String()
        copy.checks = [*self.checks, check]
        return copy

    def min(self, value: int) -> String:
        return self._with(("min", value, None))

    def max(self, value: int) -> String:
        return self._with(("max", value, None))

    def regex(self, pattern: re.Pattern[str], message: str | None = None) -> String:
        return self._with(("regex", pattern, message))

    def datetime_with_offset(self) -> String:
        return self._with(("datetime", DATETIME_WITH_OFFSET, None))

    def url(self) -> String:
        return self._with(("url", None, None))

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        if not isinstance(data, str):
            return _invalid_type(issues, path, "string", data)
        status: Status = "valid"
        for kind, value, message in self.checks:
            if kind == "min" and _js.length(data) < value:
                add_issue(
                    issues,
                    path,
                    {
                        "code": "too_small",
                        "minimum": value,
                        "type": "string",
                        "inclusive": True,
                        "exact": False,
                    },
                )
                status = "dirty"
            elif kind == "max" and _js.length(data) > value:
                add_issue(
                    issues,
                    path,
                    {
                        "code": "too_big",
                        "maximum": value,
                        "type": "string",
                        "inclusive": True,
                        "exact": False,
                    },
                )
                status = "dirty"
            elif kind == "url" and not can_parse_url(data):
                add_issue(
                    issues,
                    path,
                    {"code": "invalid_string", "validation": "url", "message": message},
                )
                status = "dirty"
            elif kind in ("regex", "datetime") and not value.search(data):
                add_issue(
                    issues,
                    path,
                    {
                        "code": "invalid_string",
                        "validation": kind,
                        "message": message,
                    },
                )
                status = "dirty"
        return Outcome(status, data)


class Number(Schema):
    def __init__(self) -> None:
        self.checks: list[tuple[str, Any]] = []

    def _with(self, check: tuple[str, Any]) -> Number:
        copy = Number()
        copy.checks = [*self.checks, check]
        return copy

    def int(self) -> Number:
        return self._with(("int", None))

    def nonnegative(self) -> Number:
        return self._with(("min", 0))

    def positive(self) -> Number:
        return self._with(("gt", 0))

    def finite(self) -> Number:
        return self._with(("finite", None))

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        if parsed_type(data) != "number":
            return _invalid_type(issues, path, "number", data)
        status: Status = "valid"
        for kind, value in self.checks:
            if kind == "int" and not _js.is_integer(data):
                add_issue(
                    issues,
                    path,
                    {"code": "invalid_type", "expected": "integer", "received": "float"},
                )
                status = "dirty"
            elif kind == "min" and data < value:
                add_issue(
                    issues,
                    path,
                    {
                        "code": "too_small",
                        "minimum": value,
                        "type": "number",
                        "inclusive": True,
                        "exact": False,
                    },
                )
                status = "dirty"
            elif kind == "gt" and data <= value:
                add_issue(
                    issues,
                    path,
                    {
                        "code": "too_small",
                        "minimum": value,
                        "type": "number",
                        "inclusive": False,
                        "exact": False,
                    },
                )
                status = "dirty"
            elif kind == "finite" and not math.isfinite(data):
                add_issue(issues, path, {"code": "not_finite"})
                status = "dirty"
        return Outcome(status, data)


class Boolean(Schema):
    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        if not isinstance(data, bool):
            return _invalid_type(issues, path, "boolean", data)
        return Outcome("valid", data)


class Null(Schema):
    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        if data is not None:
            return _invalid_type(issues, path, "null", data)
        return Outcome("valid", data)


class LiteralValue(Schema):
    def __init__(self, value: str | int | bool) -> None:
        self.value = value

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        if not _js.strict_equal(data, self.value):
            add_issue(
                issues, path, {"received": data, "code": "invalid_literal", "expected": self.value}
            )
            return ABORTED
        return Outcome("valid", data)


class Enum(Schema):
    def __init__(self, *values: str) -> None:
        self.values = list(values)

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        if not isinstance(data, str):
            return _invalid_type(issues, path, _js.join_values(self.values), data)
        if data not in self.values:
            add_issue(
                issues,
                path,
                {"received": data, "code": "invalid_enum_value", "options": self.values},
            )
            return ABORTED
        return Outcome("valid", data)


class Array(Schema):
    def __init__(self, item: Schema, *, min_length: int | None = None, length: int | None = None):
        self.item = item
        self.min_length = min_length
        self.exact_length = length

    def min(self, value: int) -> Array:
        return Array(self.item, min_length=value, length=self.exact_length)

    def length(self, value: int) -> Array:
        return Array(self.item, min_length=self.min_length, length=value)

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        if not isinstance(data, list):
            return _invalid_type(issues, path, "array", data)
        status: Status = "valid"
        if self.exact_length is not None and len(data) != self.exact_length:
            too_big = len(data) > self.exact_length
            add_issue(
                issues,
                path,
                {
                    "code": "too_big" if too_big else "too_small",
                    "minimum": UNDEFINED if too_big else self.exact_length,
                    "maximum": self.exact_length if too_big else UNDEFINED,
                    "type": "array",
                    "inclusive": True,
                    "exact": True,
                },
            )
            status = "dirty"
        if self.min_length is not None and len(data) < self.min_length:
            add_issue(
                issues,
                path,
                {
                    "code": "too_small",
                    "minimum": self.min_length,
                    "type": "array",
                    "inclusive": True,
                    "exact": False,
                },
            )
            status = "dirty"
        results = [
            self.item.parse(value, [*path, index], issues) for index, value in enumerate(data)
        ]
        values = []
        for result in results:
            if result.status == "aborted":
                return ABORTED
            if result.status == "dirty":
                status = "dirty"
            values.append(result.value)
        return Outcome(status, values)


def _merge_object(status: Status, pairs: list[tuple[str, Outcome, bool]]) -> Outcome:
    value: dict[str, Any] = {}
    for key, result, always_set in pairs:
        if result.status == "aborted":
            return ABORTED
        if result.status == "dirty":
            status = "dirty"
        if result.value is not UNDEFINED or always_set:
            value[key] = result.value
    return Outcome(status, value)


class Object(Schema):
    def __init__(self, shape: Mapping[str, Schema]) -> None:
        self.shape = dict(shape)

    def extend(self, shape: Mapping[str, Schema]) -> Object:
        merged = dict(self.shape)
        merged.update(shape)
        return Object(merged)

    def omit(self, *names: str) -> Object:
        return Object({key: schema for key, schema in self.shape.items() if key not in names})

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        if not isinstance(data, dict):
            return _invalid_type(issues, path, "object", data)
        extra = [key for key in _js.keys(data) if key not in self.shape]
        pairs = [
            (key, schema.parse(data.get(key, UNDEFINED), [*path, key], issues), key in data)
            for key, schema in self.shape.items()
        ]
        status: Status = "valid"
        if extra:
            add_issue(issues, path, {"code": "unrecognized_keys", "keys": extra})
            status = "dirty"
        return _merge_object(status, pairs)


class Record(Schema):
    def __init__(self, value: Schema) -> None:
        self.value = value

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        if not isinstance(data, dict):
            return _invalid_type(issues, path, "object", data)
        pairs = [
            (key, self.value.parse(data[key], [*path, key], issues), True) for key in _js.keys(data)
        ]
        return _merge_object("valid", pairs)


class Union(Schema):
    def __init__(self, *options: Schema) -> None:
        self.options = options

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        dirty: tuple[Outcome, list[Issue]] | None = None
        failures: list[list[Issue]] = []
        for option in self.options:
            option_issues: list[Issue] = []
            result = option.parse(data, path, option_issues)
            if result.status == "valid":
                return result
            if result.status == "dirty" and dirty is None:
                dirty = (result, option_issues)
            if option_issues:
                failures.append(option_issues)
        if dirty is not None:
            issues.extend(dirty[1])
            return dirty[0]
        add_issue(issues, path, {"code": "invalid_union", "unionErrors": failures})
        return ABORTED


class DiscriminatedUnion(Schema):
    def __init__(self, discriminator: str, options: Sequence[Object]) -> None:
        self.discriminator = discriminator
        self.options: list[tuple[Any, Object]] = []
        for option in options:
            key_schema = option.shape[discriminator]
            values = key_schema.values if isinstance(key_schema, Enum) else [key_schema.value]  # type: ignore[attr-defined]
            self.options.extend((value, option) for value in values)

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        if not isinstance(data, dict):
            return _invalid_type(issues, path, "object", data)
        value = data.get(self.discriminator, UNDEFINED)
        option = next(
            (schema for key, schema in self.options if _js.strict_equal(key, value)), None
        )
        if option is None:
            add_issue(
                issues,
                path,
                {
                    "code": "invalid_union_discriminator",
                    "options": [key for key, _ in self.options],
                    "path": [self.discriminator],
                },
            )
            return ABORTED
        return option.parse(data, path, issues)


class Lazy(Schema):
    def __init__(self, factory: Callable[[], Schema]) -> None:
        self.factory = factory
        self._schema: Schema | None = None

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        if self._schema is None:
            self._schema = self.factory()
        return self._schema.parse(data, path, issues)


class Effects(Schema):
    def __init__(self, inner: Schema, refinement: Callable[[Any, Callable[[Issue], None]], None]):
        self.inner = inner
        self.refinement = refinement

    def parse(self, data: Any, path: Path, issues: list[Issue]) -> Outcome:
        inner = self.inner.parse(data, path, issues)
        if inner.status == "aborted":
            return ABORTED
        status: list[Status] = [inner.status]

        def report(issue: Issue) -> None:
            add_issue(issues, path, dict(issue))
            status[0] = "dirty"

        self.refinement(inner.value, report)
        return Outcome(status[0], inner.value)


_DATE = (
    r"((\d\d[2468][048]|\d\d[13579][26]|\d\d0[48]|[02468][048]00|[13579][26]00)-02-29"
    r"|\d{4}-((0[13578]|1[02])-(0[1-9]|[12]\d|3[01])|(0[469]|11)-(0[1-9]|[12]\d|30)"
    r"|(02)-(0[1-9]|1\d|2[0-8])))"
)
_TIME = r"([01]\d|2[0-3]):[0-5]\d(:[0-5]\d(\.\d+)?)?"
DATETIME_WITH_OFFSET = re.compile(rf"^{_DATE}T{_TIME}(Z|([+-]\d{{2}}:?\d{{2}}))\Z", re.ASCII)
