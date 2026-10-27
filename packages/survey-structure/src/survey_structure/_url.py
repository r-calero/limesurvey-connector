"""Whether ``new URL(value)`` succeeds, following the WHATWG URL Standard (no base URL).

Zod's ``url()`` check only asks the parser to accept the string, so this module
answers that question without building the URL record. Non-ASCII domains go
through the standard library's IDNA codec, which follows IDNA 2003 rather than
UTS #46; see conformance/known-divergences.json.
"""

from __future__ import annotations

import re
import unicodedata

_SPECIAL_PORTS = {"ftp": 21, "file": None, "http": 80, "https": 443, "ws": 80, "wss": 443}
_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+\-.]*")
_FORBIDDEN_HOST = set("\x00\t\n\r #/:<>?@[\\]^|")
_FORBIDDEN_DOMAIN = _FORBIDDEN_HOST | {chr(code) for code in range(0x20)} | {"%", "\x7f"}
_PERCENT = re.compile(rb"%([0-9A-Fa-f]{2})")
_HEX_NUMBER = re.compile(r"0[xX][0-9A-Fa-f]*")


def can_parse_url(value: str) -> bool:
    text = value.strip("".join(chr(code) for code in range(0x21)))
    text = text.replace("\t", "").replace("\n", "").replace("\r", "")
    scheme_match = _SCHEME.match(text)
    if not scheme_match or text[scheme_match.end() : scheme_match.end() + 1] != ":":
        return False
    scheme = scheme_match.group().lower()
    rest = text[scheme_match.end() + 1 :]
    if scheme == "file":
        return _file(rest)
    if scheme in _SPECIAL_PORTS:
        return _authority(rest.lstrip("/\\"), special=True)
    if rest.startswith("//"):
        return _authority(rest[2:], special=False)
    return True


def _split_authority(rest: str, special: bool) -> str:
    ends = "/?#\\" if special else "/?#"
    end = next((index for index, char in enumerate(rest) if char in ends), len(rest))
    return rest[:end]


def _authority(rest: str, special: bool) -> bool:
    authority = _split_authority(rest, special)
    at = authority.rfind("@")
    credentials = at >= 0
    host_port = authority[at + 1 :] if credentials else authority
    host, port = _split_host_port(host_port)
    if host is None:
        return False
    if port is not None and not _valid_port(port):
        return False
    if special:
        if host == "":
            return False
        return _special_host(host)
    if host == "":
        return not credentials and port is None
    return _opaque_host(host)


def _split_host_port(value: str) -> tuple[str | None, str | None]:
    inside_brackets = False
    for index, char in enumerate(value):
        if char == "[":
            inside_brackets = True
        elif char == "]":
            inside_brackets = False
        elif char == ":" and not inside_brackets:
            return value[:index], value[index + 1 :]
    return value, None


def _valid_port(port: str) -> bool:
    if port == "":
        return True
    return port.isascii() and port.isdigit() and int(port) <= 65535


def _file(rest: str) -> bool:
    if len(rest) >= 2 and rest[0] in "/\\" and rest[1] in "/\\":
        host = _split_authority(rest[2:], special=True)
        if host == "" or _is_drive_letter(host):
            return True
        return _special_host(host)
    return True


def _is_drive_letter(value: str) -> bool:
    return len(value) == 2 and value[0].isascii() and value[0].isalpha() and value[1] in ":|"


def _opaque_host(host: str) -> bool:
    if host.startswith("["):
        return host.endswith("]") and _ipv6(host[1:-1])
    return not any(char in _FORBIDDEN_HOST for char in host)


def _special_host(host: str) -> bool:
    if host.startswith("["):
        return host.endswith("]") and _ipv6(host[1:-1])
    decoded = _percent_decode(host)
    if decoded is None:
        return False
    ascii_domain = _domain_to_ascii(decoded)
    if ascii_domain is None or not ascii_domain:
        return False
    if any(char in _FORBIDDEN_DOMAIN for char in ascii_domain):
        return False
    if _ends_in_number(ascii_domain):
        return _ipv4(ascii_domain)
    return True


def _percent_decode(host: str) -> str | None:
    data = host.encode("utf-8")
    decoded = _PERCENT.sub(lambda match: bytes([int(match.group(1), 16)]), data)
    return decoded.decode("utf-8", errors="replace")


def _domain_to_ascii(domain: str) -> str | None:
    if domain.isascii():
        lowered = domain.lower()
        labels = lowered.split(".")
        for label in labels:
            if label.startswith("xn--") and not _valid_punycode(label):
                return None
        return lowered
    try:
        mapped = unicodedata.normalize("NFKC", domain).casefold()
        labels = [
            label.encode("idna").decode("ascii") if label and not label.isascii() else label
            for label in mapped.split(".")
        ]
    except UnicodeError:
        return None
    return ".".join(labels)


def _valid_punycode(label: str) -> bool:
    try:
        decoded = label[4:].encode("ascii").decode("punycode")
        # The decoded label must itself be a valid internationalized label.
        return not decoded.isascii() and decoded.encode("idna").decode("ascii") == label
    except UnicodeError:
        return False


def _ends_in_number(domain: str) -> bool:
    parts = domain.split(".")
    if parts[-1] == "":
        if len(parts) == 1:
            return False
        parts.pop()
    last = parts[-1]
    if last and last.isascii() and last.isdigit():
        return True
    return bool(_HEX_NUMBER.fullmatch(last))


def _ipv4_number(part: str) -> int | None:
    if part == "":
        return None
    radix = 10
    if len(part) >= 2 and part[:2] in ("0x", "0X"):
        part, radix = part[2:], 16
    elif len(part) >= 2 and part[0] == "0":
        part, radix = part[1:], 8
    if part == "":
        return 0
    digits = {10: "0123456789", 16: "0123456789abcdefABCDEF", 8: "01234567"}[radix]
    if any(char not in digits for char in part):
        return None
    return int(part, radix)


def _ipv4(domain: str) -> bool:
    parts = domain.split(".")
    if parts[-1] == "" and len(parts) > 1:
        parts.pop()
    if len(parts) > 4:
        return False
    numbers = [_ipv4_number(part) for part in parts]
    if any(number is None for number in numbers):
        return False
    values = [number for number in numbers if number is not None]
    if any(number > 255 for number in values[:-1]):
        return False
    return bool(values[-1] < 256 ** (5 - len(values)))


def _ipv6(text: str) -> bool:
    """IPv6 address parser of the URL Standard, reduced to its success or failure."""
    pieces = 0
    compress: int | None = None
    index = 0
    if text.startswith(":"):
        if not text.startswith("::"):
            return False
        index = 2
        pieces = 1
        compress = 1
    while index < len(text):
        if pieces == 8:
            return False
        if text[index] == ":":
            if compress is not None:
                return False
            index += 1
            pieces += 1
            compress = pieces
            continue
        length = 0
        while length < 4 and index < len(text) and text[index] in "0123456789abcdefABCDEF":
            index += 1
            length += 1
        if index < len(text) and text[index] == ".":
            if length == 0:
                return False
            index -= length
            if pieces > 6:
                return False
            numbers_seen = 0
            while index < len(text):
                value: int | None = None
                if numbers_seen > 0:
                    if text[index] == "." and numbers_seen < 4:
                        index += 1
                    else:
                        return False
                if index >= len(text) or not text[index].isascii() or not text[index].isdigit():
                    return False
                while index < len(text) and text[index].isascii() and text[index].isdigit():
                    number = int(text[index])
                    if value is None:
                        value = number
                    elif value == 0:
                        return False
                    else:
                        value = value * 10 + number
                    if value > 255:
                        return False
                    index += 1
                numbers_seen += 1
                if numbers_seen in (2, 4):
                    pieces += 1
            if numbers_seen != 4:
                return False
            break
        if index < len(text) and text[index] == ":":
            index += 1
            if index >= len(text):
                return False
        elif index < len(text):
            return False
        pieces += 1
    if compress is not None:
        return pieces <= 8
    return pieces == 8
