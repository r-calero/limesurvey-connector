"""Replays the dictionary fixtures the way conformance/generate/data_dictionary.mjs does."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from survey_data_dictionary import ABSENT
from tests.support.conformance import FIXTURES, GOLDENS, read_json

DICTIONARY_GOLDENS = GOLDENS / "data-dictionary"


@dataclass(frozen=True)
class DictionaryCase:
    name: str
    fixture: dict[str, Any]

    @property
    def directory(self):
        return DICTIONARY_GOLDENS / self.name

    def survey(self) -> tuple[Any, list[dict[str, Any]]]:
        if "structure" in self.fixture:
            return self.fixture["structure"], []
        if "structureFixture" in self.fixture:
            return read_json(FIXTURES / self.fixture["structureFixture"])["value"], []
        golden = read_json(GOLDENS / self.fixture["loadResultGolden"])
        return golden["result"]["survey"], golden["result"]["issues"]

    @property
    def aliases(self) -> dict[str, str] | None:
        return (self.fixture.get("aliasConfiguration") or {}).get("aliases")

    @property
    def ignored_headers(self) -> list[str]:
        return (self.fixture.get("aliasConfiguration") or {}).get("ignoredHeaders", [])

    def golden(self, filename: str) -> Any:
        return read_json(self.directory / filename)

    def golden_text(self, filename: str) -> str:
        return (self.directory / filename).read_text(encoding="utf-8")


def dictionary_cases() -> Iterator[DictionaryCase]:
    for path in sorted((FIXTURES / "dictionary").glob("*.json")):
        yield DictionaryCase(path.stem, read_json(path))
    for path in sorted((GOLDENS / "limesurvey" / "lss").glob("*.json")):
        if read_json(path)["ok"]:
            yield DictionaryCase(
                f"lss-{path.stem}", {"loadResultGolden": f"limesurvey/lss/{path.name}"}
            )


def as_json(value: Any) -> Any:
    """Drop ``ABSENT`` the way JSON.stringify drops ``undefined`` (``null`` inside arrays)."""
    if value is ABSENT:
        return None
    if isinstance(value, list):
        return [as_json(item) for item in value]
    if isinstance(value, dict):
        return {key: as_json(item) for key, item in value.items() if item is not ABSENT}
    return value
