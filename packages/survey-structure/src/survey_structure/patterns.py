"""ECMAScript response-format patterns on top of the standard ``re`` module.

The contract stores ``responseFormatPattern`` as ECMAScript source (the non-Unicode
grammar, including Annex B) and ``patternFlags`` as a subset of ``ims``; the pattern
is tested as written, without anchors. Patterns are translated to an equivalent
Python expression; the few constructs ``re`` cannot express with the same meaning
are rejected (ADR 3).
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from functools import lru_cache

from survey_structure._js import JS_WHITESPACE

_WHITESPACE = "".join(f"\\u{ord(char):04x}" for char in JS_WHITESPACE)
_LINE_TERMINATORS = "\\n\\r\\u2028\\u2029"
_ANY_BUT_LINE_TERMINATOR = f"[^{_LINE_TERMINATORS}]"
_ANY_UNIT = "[\\x00-\\uffff]"
_LINE_START = f"(?:^|(?<=[{_LINE_TERMINATORS}]))"
_LINE_END = f"(?=[{_LINE_TERMINATORS}]|\\Z)"
_JS_FLAGS = frozenset("dgimsuvy")
# Before Python 3.14, \B never matches an empty string; ECMAScript's does.
_NOT_WORD_BOUNDARY = "(?:(?<=\\w)(?=\\w)|(?<!\\w)(?!\\w))"
_CLASS_ESCAPES = {
    "d": "\\d",
    "D": "\\D",
    "w": "\\w",
    "W": "\\W",
    "s": f"[{_WHITESPACE}]",
    "S": f"[^{_WHITESPACE}]",
}
_CONTROL_ESCAPES = {"f": 0x0C, "n": 0x0A, "r": 0x0D, "t": 0x09, "v": 0x0B}
_QUANTIFIER = re.compile(r"\{(\d+)(?:,(\d*))?\}")
_GROUP_NAME = re.compile(r"<([A-Za-z_$][A-Za-z0-9_$]*)>")
_HEX2 = re.compile(r"[0-9A-Fa-f]{2}")
_HEX4 = re.compile(r"[0-9A-Fa-f]{4}")
_ASCII_LETTER = re.compile(r"[A-Za-z]")


class _Rejected(Exception):
    pass


@lru_cache(maxsize=1)
def _case_classes() -> tuple[list[int], dict[int, list[int]]]:
    """ECMAScript ``Canonicalize`` without the u flag, for every UTF-16 code unit."""
    canonical = list(range(0x10000))
    for code in range(0x10000):
        upper = chr(code).upper()
        if len(upper) != 1 or ord(upper) > 0xFFFF:
            continue
        if code >= 128 and ord(upper) < 128:
            continue
        canonical[code] = ord(upper)
    members: dict[int, list[int]] = {}
    for code, value in enumerate(canonical):
        members.setdefault(value, []).append(code)
    return canonical, members


def _fold(codes: set[int]) -> set[int]:
    canonical, members = _case_classes()
    folded: set[int] = set()
    for code in codes:
        folded.update(members[canonical[code]])
    return folded


def _ranges(codes: set[int]) -> str:
    ordered = sorted(codes)
    parts: list[str] = []
    start = previous = ordered[0]
    for code in [*ordered[1:], -1]:
        if code == previous + 1:
            previous = code
            continue
        parts.append(
            _literal(start) if start == previous else f"{_literal(start)}-{_literal(previous)}"
        )
        start = previous = code
    return "".join(parts)


def _literal(code: int) -> str:
    if code > 0xFFFF:
        # ECMAScript without the u flag sees a surrogate pair as two characters.
        code -= 0x10000
        return _literal(0xD800 + (code >> 10)) + _literal(0xDC00 + (code & 0x3FF))
    return f"\\x{code:02x}" if code < 0x100 else f"\\u{code:04x}"


def utf16_units(value: str) -> str:
    """Rewrite ``value`` as one Python character per UTF-16 code unit, as ECMAScript sees it."""
    return "".join(
        chr(unit) for unit in memoryview(value.encode("utf-16-le", "surrogatepass")).cast("H")
    )


@dataclass
class _Group:
    start: int
    capture: int | None = None
    name: str | None = None
    end: int | None = None
    quantified: bool = False
    parent: _Group | None = None


@dataclass
class _Reference:
    position: int
    target: int | str


@dataclass
class _Parsed:
    parts: list[str | _Reference] = field(default_factory=list)
    groups: list[_Group] = field(default_factory=list)


def _legacy_octal(source: str, index: int) -> tuple[int, int]:
    """Annex B LegacyOctalEscapeSequence starting at ``index``; returns (code, next index)."""
    limit = 3 if source[index] in "0123" else 2
    end = index
    while end < len(source) and end - index < limit and source[end] in "01234567":
        end += 1
    return int(source[index:end], 8), end


class _Parser:
    def __init__(self, source: str, flags: str = "") -> None:
        self.source = source
        self.ignore_case = "i" in flags
        self.multiline = "m" in flags
        self.dot_all = "s" in flags
        self.index = 0
        self.result = _Parsed()
        self.stack: list[_Group] = []
        self.captures = self._count_captures()
        self.named = bool(re.search(r"\(\?<(?![=!])", source))

    def _count_captures(self) -> int:
        count, index, in_class = 0, 0, False
        source = self.source
        while index < len(source):
            char = source[index]
            if char == "\\":
                index += 2
                continue
            if in_class:
                in_class = char != "]"
            elif char == "[":
                in_class = True
            elif char == "(" and (
                not source.startswith("(?", index) or _GROUP_NAME.match(source, index + 2)
            ):
                count += 1
            index += 1
        return count

    def emit(self, text: str) -> None:
        self.result.parts.append(text)

    def _emit_units(self, units: list[int], *, source: str | None = None) -> None:
        """Emit literal code units; ``source`` keeps a plain source character readable."""
        for unit in units:
            folded = _fold({unit}) if self.ignore_case else {unit}
            if len(folded) > 1:
                self.emit(f"[{_ranges(folded)}]")
            else:
                self.emit(re.escape(source) if source is not None else _literal(unit))

    def parse(self) -> _Parsed:
        source = self.source
        while self.index < len(source):
            char = source[self.index]
            if char == "\\":
                self._escape()
            elif char == "[":
                self._class()
            elif char == "(":
                self._open_group()
            elif char == ")":
                self._close_group()
            elif char in "*+?{":
                self._quantifier()
            else:
                special = {
                    ".": _ANY_UNIT if self.dot_all else _ANY_BUT_LINE_TERMINATOR,
                    "$": _LINE_END if self.multiline else "\\Z",
                    "^": _LINE_START if self.multiline else "^",
                    "|": "|",
                }
                if char in special:
                    self.emit(special[char])
                else:
                    self._emit_units(
                        _code_units(ord(char)), source=char if ord(char) <= 0xFFFF else None
                    )
                self.index += 1
        if self.stack:
            raise _Rejected
        return self.result

    def _open_group(self) -> None:
        source, start = self.source, self.index
        group = _Group(start=len(self.result.parts), parent=self.stack[-1] if self.stack else None)
        if source.startswith("(?", start):
            rest = source[start + 2 :]
            prefix = next(
                (item for item in (":", "=", "!", "<=", "<!") if rest.startswith(item)), None
            )
            if prefix is not None:
                self.emit("(?" + prefix)
                self.index = start + 2 + len(prefix)
            else:
                match = _GROUP_NAME.match(rest)
                if not match or "$" in match.group(1):
                    raise _Rejected
                group.name = match.group(1)
                group.capture = self._next_capture()
                self.emit(f"(?P<{group.name}>")
                self.index = start + 2 + match.end()
        else:
            group.capture = self._next_capture()
            self.emit("(")
            self.index += 1
        self.stack.append(group)
        self.result.groups.append(group)

    def _next_capture(self) -> int:
        return sum(1 for group in self.result.groups if group.capture is not None) + 1

    def _close_group(self) -> None:
        if not self.stack:
            raise _Rejected
        group = self.stack.pop()
        self.emit(")")
        group.end = len(self.result.parts)
        self.index += 1
        following = self.source[self.index : self.index + 1]
        group.quantified = following in ("*", "+", "?") or bool(
            _QUANTIFIER.match(self.source, self.index)
        )

    def _quantifier(self) -> None:
        source = self.source
        previous = self.result.parts[-1] if self.result.parts else None
        nothing_to_repeat = previous is None or (
            isinstance(previous, str)
            and (previous in ("|", "^") or (previous.startswith("(") and previous != "(?:)"))
        )
        if nothing_to_repeat and (
            source[self.index] != "{" or _QUANTIFIER.match(source, self.index)
        ):
            raise _Rejected
        if source[self.index] == "{":
            match = _QUANTIFIER.match(source, self.index)
            if not match:
                # ECMAScript reads a brace that does not form a quantifier as a literal.
                self.emit("\\{")
                self.index += 1
                return
            self.emit(match.group())
            self.index = match.end()
        else:
            self.emit(source[self.index])
            self.index += 1
        if source.startswith("?", self.index):
            self.emit("?")
            self.index += 1
        if source.startswith("+", self.index):
            raise _Rejected

    def _escape(self) -> None:
        source = self.source
        if self.index + 1 >= len(source):
            raise _Rejected
        char = source[self.index + 1]
        self.index += 2
        if char in _CLASS_ESCAPES:
            self.emit(_CLASS_ESCAPES[char])
        elif char == "b":
            self.emit("\\b")
        elif char == "B":
            self.emit(_NOT_WORD_BOUNDARY)
        elif char == "k" and self.named:
            match = _GROUP_NAME.match(source, self.index)
            if not match:
                raise _Rejected
            if self.ignore_case:
                # Python backreferences compare exactly; ECMAScript would compare canonical forms.
                raise _Rejected
            self.result.parts.append(_Reference(len(self.result.parts), match.group(1)))
            self.index = match.end()
        elif char in "123456789":
            end = self.index - 1
            while end < len(source) and source[end].isdigit():
                end += 1
            number = int(source[self.index - 1 : end])
            if number <= self.captures:
                if self.ignore_case:
                    raise _Rejected
                self.result.parts.append(_Reference(len(self.result.parts), number))
                self.index = end
            elif char in "89":
                self._emit_units([ord(char)])
            else:
                code, self.index = _legacy_octal(source, self.index - 1)
                self._emit_units([code])
        else:
            self._emit_units(_code_units(self._character_escape(char, in_class=False)))

    def _character_escape(self, char: str, *, in_class: bool) -> int:
        """Code of the character denoted by ``\\char``; ``self.index`` is past ``char``."""
        source = self.source
        if char in _CONTROL_ESCAPES:
            return _CONTROL_ESCAPES[char]
        if char == "0":
            if self.index < len(source) and source[self.index] in "01234567":
                code, self.index = _legacy_octal(source, self.index - 1)
                return code
            return 0
        if char == "c":
            following = source[self.index : self.index + 1]
            allowed = _ASCII_LETTER.match(following) or (
                in_class and following and following in "0123456789_"
            )
            if allowed:
                self.index += 1
                return ord(following) % 32
            # Annex B: "\\c" without a control letter is a literal backslash.
            self.index -= 1
            return ord("\\")
        if char == "x" and _HEX2.match(source, self.index):
            self.index += 2
            return int(source[self.index - 2 : self.index], 16)
        if char == "u" and _HEX4.match(source, self.index):
            self.index += 4
            return int(source[self.index - 4 : self.index], 16)
        # Annex B identity escape: any other character stands for itself.
        return ord(char)

    def _class(self) -> None:
        source = self.source
        self.index += 1
        negated = source.startswith("^", self.index)
        if negated:
            self.index += 1
        atoms: list[tuple[str, int | str]] = []
        while True:
            if self.index >= len(source):
                raise _Rejected
            char = source[self.index]
            if char == "]":
                self.index += 1
                break
            if char != "\\":
                self.index += 1
                if char == "-":
                    atoms.append(("dash", ord("-")))
                else:
                    atoms.extend(("char", unit) for unit in _code_units(ord(char)))
                continue
            if self.index + 1 >= len(source):
                raise _Rejected
            escaped = source[self.index + 1]
            self.index += 2
            if escaped in _CLASS_ESCAPES:
                atoms.append(("set", escaped))
            elif escaped == "b":
                atoms.append(("char", 0x08))
            elif escaped in "89":
                atoms.append(("char", ord(escaped)))
            elif escaped in "1234567":
                code, self.index = _legacy_octal(source, self.index - 1)
                atoms.append(("char", code))
            else:
                code = self._character_escape(escaped, in_class=True)
                atoms.extend(("char", unit) for unit in _code_units(code))
        self.emit(_render_class(atoms, negated=negated, ignore_case=self.ignore_case))


def _code_units(code: int) -> list[int]:
    if code <= 0xFFFF:
        return [code]
    code -= 0x10000
    return [0xD800 + (code >> 10), 0xDC00 + (code & 0x3FF)]


def _render_class(
    atoms: list[tuple[str, int | str]], *, negated: bool, ignore_case: bool = False
) -> str:
    """Follow ECMAScript ClassRanges: ``A-B`` is a range unless an endpoint is a class escape."""
    if not atoms:
        return "[\\s\\S]" if negated else "(?!)"
    if ignore_case:
        return _render_folded_class(atoms, negated=negated)
    members: list[str] = []
    negative_space = False

    def member(atom: tuple[str, int | str]) -> str:
        nonlocal negative_space
        kind, value = atom
        if kind == "set":
            if value == "S":
                negative_space = True
                return ""
            return _WHITESPACE if value == "s" else f"\\{value}"
        return "\\-" if kind == "dash" else _literal(int(value))

    index = 0
    while index < len(atoms):
        first = atoms[index]
        if index + 2 < len(atoms) and atoms[index + 1][0] == "dash":
            last = atoms[index + 2]
            if first[0] == "set" or last[0] == "set":
                members.extend((member(first), "\\-", member(last)))
            else:
                if int(first[1]) > int(last[1]):
                    raise _Rejected
                members.append(f"{member(first)}-{member(last)}")
            index += 3
            continue
        members.append(member(first))
        index += 1
    others = "".join(members)
    if not negative_space:
        return f"[{'^' if negated else ''}{others}]"
    # \\S cannot sit inside a Python class, so combine it with an alternation.
    if not negated:
        return f"(?:[^{_WHITESPACE}]|[{others}])" if others else f"[^{_WHITESPACE}]"
    return f"(?:(?![{others}])[{_WHITESPACE}])" if others else f"[{_WHITESPACE}]"


def _render_folded_class(atoms: list[tuple[str, int | str]], *, negated: bool) -> str:
    """With the i flag a unit matches when its canonical form equals that of a member.

    Class escapes (\\d, \\w, \\s and their complements) are closed under this
    relation already, so only literal units and ranges are expanded.
    """
    codes: set[int] = set()
    escapes: list[str] = []
    index = 0
    while index < len(atoms):
        first = atoms[index]
        if index + 2 < len(atoms) and atoms[index + 1][0] == "dash":
            last = atoms[index + 2]
            if first[0] != "set" and last[0] != "set":
                if int(first[1]) > int(last[1]):
                    raise _Rejected
                codes.update(range(int(first[1]), int(last[1]) + 1))
                index += 3
                continue
        if first[0] == "set":
            escapes.append(str(first[1]))
        else:
            codes.add(int(first[1]))
        index += 1
    folded = _fold(codes)
    negative_space = "S" in escapes
    others = "".join(
        _WHITESPACE if name == "s" else f"\\{name}" for name in escapes if name != "S"
    ) + (_ranges(folded) if folded else "")
    if not negative_space:
        if not others:
            return "[\\s\\S]" if negated else "(?!)"
        return f"[{'^' if negated else ''}{others}]"
    if not negated:
        return f"(?:[^{_WHITESPACE}]|[{others}])" if others else f"[^{_WHITESPACE}]"
    return f"(?:(?![{others}])[{_WHITESPACE}])" if others else f"[{_WHITESPACE}]"


def _render(parsed: _Parsed) -> str:
    output: list[str] = []
    captures = {group.capture: group for group in parsed.groups if group.capture is not None}
    names = {group.name: group for group in parsed.groups if group.name is not None}
    for part in parsed.parts:
        if isinstance(part, str):
            output.append(part)
            continue
        group = (
            names.get(part.target) if isinstance(part.target, str) else captures.get(part.target)
        )
        if group is None:
            raise _Rejected
        if group.end is None or group.end > part.position:
            # Referenced before its group closes: ECMAScript matches the empty string.
            output.append("(?:)")
            continue
        ancestor = group.parent
        while ancestor is not None:
            encloses_reference = ancestor.end is not None and ancestor.end > part.position
            if ancestor.quantified and encloses_reference:
                # Captures reset on every repetition in ECMAScript but persist in Python.
                raise _Rejected
            ancestor = ancestor.parent
        reference = group.name if group.name is not None else str(group.capture)
        backreference = f"(?P={group.name})" if group.name is not None else f"\\{group.capture}"
        output.append(f"(?({reference}){backreference})")
    return "".join(output)


def valid_flags(flags: str) -> bool:
    """Flags ``new RegExp`` accepts: known letters, each at most once, not u together with v."""
    return (
        all(flag in _JS_FLAGS for flag in flags)
        and len(set(flags)) == len(flags)
        and not ("u" in flags and "v" in flags)
    )


@lru_cache(maxsize=1024)
def compile_pattern(source: str, flags: str = "") -> re.Pattern[str] | None:
    """Compile an ECMAScript pattern, or return ``None`` if it cannot be matched identically.

    ``d`` and ``g`` do not change a single ``test``; ``y`` anchors it at the start. The
    Unicode grammar of ``u`` and ``v`` is not supported.
    """
    if not valid_flags(flags) or "u" in flags or "v" in flags:
        return None
    try:
        translated = _render(_Parser(source, flags).parse())
        if "y" in flags:
            translated = f"\\A(?:{translated})"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            return re.compile(translated, re.ASCII)
    except (_Rejected, re.error, RecursionError):
        return None


def to_python_pattern(source: str, flags: str = "") -> re.Pattern[str]:
    """Python equivalent of an ECMAScript ``responseFormatPattern`` with its ``patternFlags``.

    The expression works on UTF-16 code units, as ECMAScript does: search it in
    ``utf16_units(value)``, or use ``test_pattern``. Raises ``ValueError`` when the
    pattern is not accepted by the contract validator.
    """
    pattern = compile_pattern(source, flags)
    if pattern is None:
        raise ValueError(f"Pattern cannot be matched identically with Python's re: {source!r}")
    return pattern


def is_valid_pattern(source: str, flags: str = "") -> bool:
    return compile_pattern(source, flags) is not None


def test_pattern(source: str, value: str, flags: str = "") -> bool:
    """``new RegExp(source, flags).test(value)``. Raises ``ValueError`` for a pattern that is not accepted."""
    return to_python_pattern(source, flags).search(utf16_units(value)) is not None
