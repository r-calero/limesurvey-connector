"""Record the connector's results for inputs the reference implementations cannot handle.

These cover intentional changes (conformance/intentional-changes.json) that no reference
option reproduces. Review the diff by hand before committing regenerated files.

    uv run python conformance/generate/connector_goldens.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from limesurvey_connector.limesurvey import load_lss
from limesurvey_connector.limesurvey.dictionary import build_limesurvey_dictionary
from limesurvey_connector.limesurvey.responses import translate_csv, translate_records
from limesurvey_connector.remote import decode_response_export
from survey_data_dictionary import dictionary_to_csv, translated_dataset_to_csv

CONFORMANCE = Path(__file__).resolve().parents[1]
FIXTURES = CONFORMANCE / "fixtures" / "connector"
OUT = CONFORMANCE / "goldens-connector"


def as_json(value: Any) -> Any:
    from survey_data_dictionary import ABSENT

    if value is ABSENT:
        return None
    if isinstance(value, dict):
        return {key: as_json(item) for key, item in value.items() if item is not ABSENT}
    if isinstance(value, list):
        return [as_json(item) for item in value]
    return value


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(
            json.dumps(as_json(value), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


def generate() -> dict[str, Any]:
    results: dict[str, Any] = {}
    name = "limesurvey3-dbversion-355"
    loaded = load_lss(FIXTURES / "lss" / f"{name}.lss")
    dictionary = build_limesurvey_dictionary(loaded["survey"], source_issues=loaded["issues"])
    extended = build_limesurvey_dictionary(
        loaded["survey"],
        source_issues=loaded["issues"],
        include_system_fields=True,
        include_timing_fields=True,
    )
    responses = FIXTURES / "responses"
    code_csv = (responses / "limesurvey3-code-headings.csv").read_text(encoding="utf-8-sig")
    vv = (responses / "limesurvey3-vv.txt").read_text(encoding="utf-8")
    exported = decode_response_export(
        (responses / "limesurvey3-export.json").read_bytes(), 900355, "json", "es-MX", 10_000_000
    )
    if not isinstance(exported, dict):
        raise TypeError("A JSON export must decode to a dataset.")
    code_result = translate_csv(dictionary, code_csv)
    vv_result = translate_csv(dictionary, vv, format="vv", delimiter="\t")
    json_result = translate_records(dictionary, exported["responses"], response_id_key="id")
    results[f"{name}/load-result.json"] = loaded
    results[f"{name}/dictionary.json"] = dictionary
    results[f"{name}/dictionary-system-timing.json"] = extended
    results[f"{name}/dictionary-system-timing.csv"] = dictionary_to_csv(extended)
    results[f"{name}/csv-code-headings.json"] = code_result
    results[f"{name}/csv-code-headings.csv"] = translated_dataset_to_csv(code_result["translated"])
    results[f"{name}/csv-vv.json"] = vv_result
    results[f"{name}/export-json.json"] = exported
    results[f"{name}/export-json-translated.json"] = json_result
    return results


def main() -> None:
    for relative, value in generate().items():
        write(OUT / relative, value)


if __name__ == "__main__":
    main()
