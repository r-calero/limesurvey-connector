"""CSV reader with the behavior of papaparse 5.7 as used by limesurvey-dictionary-api.

Only the options that API uses are supported: an optional delimiter (guessed
otherwise), automatic line endings and ``skipEmptyLines: true``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from survey_structure._js import trim

_DELIMITERS = (",", "\t", "|", ";", "\x1e", "\x1f")
_BAD_DELIMITERS = ("\r", "\n", '"', chr(0xFEFF))
_QUOTE = '"'


@dataclass
class ParseError:
    type: str
    code: str
    message: str
    row: int | None = None
    index: int | None = None


@dataclass
class ParseResult:
    data: list[list[str]] = field(default_factory=list)
    errors: list[ParseError] = field(default_factory=list)
    delimiter: str = ","
    linebreak: str = "\n"


def parse(text: str, delimiter: str | None = None) -> ParseResult:
    text = text.removeprefix(chr(0xFEFF))
    newline = _guess_line_endings(text)
    delimiter_error = False
    if not delimiter:
        guessed = _guess_delimiter(text, newline)
        if guessed is None:
            delimiter_error = True
            delimiter = ","
        else:
            delimiter = guessed
    result = _Parser(delimiter, newline).parse(text)
    result.linebreak = newline
    if delimiter_error:
        result.errors.append(
            ParseError(
                "Delimiter",
                "UndetectableDelimiter",
                "Unable to auto-detect delimiting character; defaulted to ','",
            )
        )
    result.data = [row for row in result.data if not _is_empty_line(row)]
    return result


def _is_empty_line(row: list[str]) -> bool:
    return len(row) == 1 and len(row[0]) == 0


def _guess_line_endings(text: str) -> str:
    sample = text[: 1024 * 1024]
    # Remove quoted text, as papaparse does with /"([^]*?)"/gm.
    stripped: list[str] = []
    index = 0
    while True:
        start = sample.find(_QUOTE, index)
        if start < 0:
            stripped.append(sample[index:])
            break
        end = sample.find(_QUOTE, start + 1)
        if end < 0:
            stripped.append(sample[index:])
            break
        stripped.append(sample[index:start])
        index = end + 1
    sample = "".join(stripped)
    by_cr = sample.split("\r")
    by_lf = sample.split("\n")
    lf_first = len(by_lf) > 1 and len(by_lf[0]) < len(by_cr[0])
    if len(by_cr) == 1 or lf_first:
        return "\n"
    with_lf = sum(1 for part in by_cr if part[:1] == "\n")
    return "\r\n" if with_lf >= len(by_cr) / 2 else "\r"


def _guess_delimiter(text: str, newline: str) -> str | None:
    best: str | None = None
    best_delta: float | None = None
    max_field_count = 0.0
    for delimiter in _DELIMITERS:
        delta = 0
        average = 0.0
        empty_lines = 0
        previous: int | None = None
        rows = _Parser(delimiter, newline, preview=10).parse(text).data
        for row in rows:
            if _is_empty_line(row):
                empty_lines += 1
                continue
            count = len(row)
            average += count
            if previous is None:
                previous = count
                continue
            if count > 0:
                delta += abs(count - previous)
                previous = count
        if rows:
            counted = len(rows) - empty_lines
            average = average / counted if counted else float("nan")
        if average > 1.99 and (
            best_delta is None
            or delta < best_delta
            or (delta == best_delta and average > max_field_count)
        ):
            best_delta = delta
            best = delimiter
            max_field_count = average
    return best


class _Parser:
    def __init__(self, delimiter: str, newline: str, preview: int = 0) -> None:
        if not isinstance(delimiter, str) or delimiter in _BAD_DELIMITERS:
            delimiter = ","
        self.delimiter = delimiter
        self.newline = newline if newline in ("\n", "\r", "\r\n") else "\n"
        self.preview = preview

    def parse(self, text: str) -> ParseResult:
        delimiter, newline, preview = self.delimiter, self.newline, self.preview
        data: list[list[str]] = []
        errors: list[ParseError] = []
        result = ParseResult(data, errors, delimiter)
        if not text:
            return result
        if _QUOTE not in text:
            lines = text.split(newline)
            for index, line in enumerate(lines):
                data.append(line.split(delimiter))
                if preview and index >= preview:
                    del data[preview:]
                    return result
            return result

        length = len(text)
        cursor = 0
        row: list[str] = []
        next_delimiter = text.find(delimiter, cursor)
        next_newline = text.find(newline, cursor)
        quote_search = text.find(_QUOTE, cursor)

        def extra_spaces(index: int) -> int:
            if index != -1:
                between = text[quote_search + 1 : index]
                if between and trim(between) == "":
                    return len(between)
            return 0

        def finish(value: str | None = None) -> ParseResult:
            row.append(text[cursor:] if value is None else value)
            data.append(row)
            return result

        while True:
            if cursor < length and text[cursor] == _QUOTE:
                quote_search = cursor
                cursor += 1
                while True:
                    quote_search = text.find(_QUOTE, quote_search + 1)
                    if quote_search == -1:
                        errors.append(
                            ParseError(
                                "Quotes",
                                "MissingQuotes",
                                "Quoted field unterminated",
                                len(data),
                                cursor,
                            )
                        )
                        return finish()
                    if quote_search == length - 1:
                        return finish(text[cursor:quote_search].replace('""', '"'))
                    if text[quote_search + 1] == _QUOTE:
                        quote_search += 1
                        continue
                    if next_delimiter != -1 and next_delimiter < quote_search + 1:
                        next_delimiter = text.find(delimiter, quote_search + 1)
                    if next_newline != -1 and next_newline < quote_search + 1:
                        next_newline = text.find(newline, quote_search + 1)
                    check_up_to = (
                        next_delimiter if next_newline == -1 else min(next_delimiter, next_newline)
                    )
                    spaces = extra_spaces(check_up_to)
                    after = quote_search + 1 + spaces
                    if text[after : after + len(delimiter)] == delimiter:
                        row.append(text[cursor:quote_search].replace('""', '"'))
                        cursor = after + len(delimiter)
                        if text[cursor : cursor + 1] != _QUOTE:
                            quote_search = text.find(_QUOTE, cursor)
                        next_delimiter = text.find(delimiter, cursor)
                        next_newline = text.find(newline, cursor)
                        break
                    spaces = extra_spaces(next_newline)
                    after = quote_search + 1 + spaces
                    if text[after : after + len(newline)] == newline:
                        row.append(text[cursor:quote_search].replace('""', '"'))
                        cursor = after + len(newline)
                        data.append(row)
                        row = []
                        next_newline = text.find(newline, cursor)
                        next_delimiter = text.find(delimiter, cursor)
                        quote_search = text.find(_QUOTE, cursor)
                        if preview and len(data) >= preview:
                            return result
                        break
                    errors.append(
                        ParseError(
                            "Quotes",
                            "InvalidQuotes",
                            "Trailing quote on quoted field is malformed",
                            len(data),
                            cursor,
                        )
                    )
                    quote_search += 1
                continue

            if next_delimiter != -1 and (next_delimiter < next_newline or next_newline == -1):
                row.append(text[cursor:next_delimiter])
                cursor = next_delimiter + len(delimiter)
                next_delimiter = text.find(delimiter, cursor)
                continue
            if next_newline != -1:
                row.append(text[cursor:next_newline])
                cursor = next_newline + len(newline)
                data.append(row)
                row = []
                next_newline = text.find(newline, cursor)
                if preview and len(data) >= preview:
                    return result
                continue
            break
        return finish()
