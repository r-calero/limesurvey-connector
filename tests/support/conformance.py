from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

CONFORMANCE = Path(__file__).resolve().parents[2] / "conformance"
GOLDENS = CONFORMANCE / "goldens"
FIXTURES = CONFORMANCE / "fixtures"
TS_VALIDATOR = CONFORMANCE / "tools" / "validate-survey.cjs"
NODE = shutil.which("node")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest() -> dict[str, Any]:
    return read_json(GOLDENS / "MANIFEST.json")


def validation_cases() -> list[dict[str, Any]]:
    return read_json(GOLDENS / "survey-structure" / "validation-cases.json")["cases"]


def load_result_goldens() -> Iterator[tuple[str, dict[str, Any]]]:
    for path in sorted((GOLDENS / "limesurvey").rglob("*.json")):
        yield path.relative_to(GOLDENS).as_posix(), read_json(path)


def ts_validate(contract: str, value: Any, locale: str = "en") -> dict[str, Any]:
    """Validate with the TypeScript reference contract; used only by tests."""
    if NODE is None:
        raise RuntimeError("Node is required to run the TypeScript contract validator.")
    payload = json.dumps({"contract": contract, "value": value, "locale": locale})
    completed = subprocess.run(
        [NODE, str(TS_VALIDATOR)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    result: dict[str, Any] = json.loads(completed.stdout)
    return result


def with_limesurvey_column_names(result):
    """limesurvey-column-names: Q_other and Q_comment, where limesurvey-rc2-api writes Qother and Qcomment."""
    expected = copy.deepcopy(result)
    for field in _all_fields(expected["survey"]["fields"]):
        code = field["code"]
        other = field.get("other")
        if other and other["textResponseKey"] == f"{code}other":
            other["textResponseKey"] = f"{code}_other"
        if field.get("commentResponseKey") == f"{code}comment":
            field["commentResponseKey"] = f"{code}_comment"
    return expected


def _all_fields(fields):
    for field in fields:
        yield field
        if field["type"] == "custom":
            yield from _all_fields(field["childrenFields"])
