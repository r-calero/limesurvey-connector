"""Convert LimeSurvey rich text to the plain text stored by SurveyStructure."""

import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit


class _JavaScriptDetector(HTMLParser):
    """Recognize executable markup, never interpret code or unescape text as markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_script = False
        self.found = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "script":
            self.in_script = (attributes.get("type") or "").strip().lower() in {
                "",
                "module",
                "text/javascript",
                "application/javascript",
                "text/ecmascript",
                "application/ecmascript",
            }
            if self.in_script and (attributes.get("src") or "").strip():
                self.found = True
        if any(name.startswith("on") and value and value.strip() for name, value in attrs):
            self.found = True
        if any(
            name in {"href", "src", "action", "formaction", "xlink:href"}
            and value
            and value.strip().lower().startswith("javascript:")
            for name, value in attrs
        ):
            self.found = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self.in_script = False

    def handle_data(self, data: str) -> None:
        if self.in_script and data.strip():
            self.found = True


def contains_embedded_javascript(value: Any) -> bool:
    parser = _JavaScriptDetector()
    parser.feed("" if value is None else str(value))
    parser.close()
    return parser.found


class _PlainTextParser(HTMLParser):
    """Collect visible text without executing or preserving HTML markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.hidden_depth += 1
        elif tag in {"br", "p", "div", "li"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.hidden_depth:
            self.hidden_depth -= 1
        elif tag in {"p", "div", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)


def plain_text_from_html(value: Any) -> str:
    """Return readable text while dropping markup, scripts, and styles."""
    parser = _PlainTextParser()
    parser.feed("" if value is None else str(value))
    parser.close()
    lines = [
        re.sub(r"[ \t\r\f\v]+", " ", line).strip() for line in "".join(parser.parts).splitlines()
    ]
    return "\n".join(line for line in lines if line)


def question_images(value: Any, remote_url: str = "") -> list[dict[str, str]]:
    """Keep HTTP(S) images as question content; do not retain executable markup."""

    class ImageParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.images: list[dict[str, str]] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag != "img":
                return
            attributes = dict(attrs)
            src = (attributes.get("src") or "").strip()
            if not src:
                return
            url = urljoin(remote_url, src) if remote_url else src
            parsed = urlsplit(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                return
            self.images.append({"url": url, "alt": (attributes.get("alt") or "").strip()})

    parser = ImageParser()
    parser.feed("" if value is None else str(value))
    parser.close()
    return parser.images
