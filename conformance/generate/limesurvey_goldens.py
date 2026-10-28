"""Record limesurvey-rc2-api normalization results. Runs inside that project's environment."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def outcome(action: Any) -> dict[str, Any]:
    try:
        return {"ok": True, "result": action()}
    except Exception as error:
        failure: dict[str, Any] = {"type": type(error).__name__, "message": str(error)}
        if getattr(error, "errors", None):
            failure["errors"] = error.errors
        return {"ok": False, "error": failure}


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class _FakeSurveyOperations:
    """RemoteControl 2 answers recorded in fixtures/remote-api, served like the rc2 facade."""

    def __init__(self, fixture: dict[str, Any]) -> None:
        self.fixture = fixture

    def get_survey_properties(self, survey_id: int, settings: Any = None) -> Any:
        return dict(self.fixture["surveyProperties"])

    def get_language_properties(
        self, survey_id: int, settings: Any = None, language: Any = None
    ) -> Any:
        return dict(self.fixture["languageProperties"])

    def list_groups(self, survey_id: int, language: Any = None) -> Any:
        return [dict(group) for group in self.fixture["groups"]]

    def list_questions(self, survey_id: int, group_id: Any = None, language: Any = None) -> Any:
        return [dict(row) for row in self.fixture["questionsByGroup"].get(str(group_id), [])]

    def export_responses(self, survey_id: int, **options: Any) -> bytes:
        return json.dumps({"responses": self.fixture["responses"]}).encode("utf-8")


class _FakeQuestionOperations:
    def __init__(self, fixture: dict[str, Any]) -> None:
        self.fixture = fixture

    def get_question_properties(
        self, question_id: int, settings: Any = None, language: Any = None
    ) -> Any:
        return json.loads(json.dumps(self.fixture["questionProperties"][str(question_id)]))


class _FakeApi:
    url = "https://surveys.example.org/index.php/admin/remotecontrol"
    username = "ana"

    def __init__(self, fixture: dict[str, Any]) -> None:
        self.survey = _FakeSurveyOperations(fixture)
        self.question = _FakeQuestionOperations(fixture)


def remote_api_goldens(fixtures: Path, out: Path) -> None:
    import asyncio

    from services.remote_response_loader import load_responses
    from services.remote_survey_structure_loader import load_remote_survey_structure

    for path in sorted((fixtures / "remote-api").glob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        api = _FakeApi(fixture)
        sid = fixture["surveyId"]
        golden = {
            "input": f"remote-api/{path.name}",
            **outcome(lambda api=api, sid=sid: asyncio.run(load_remote_survey_structure(api, sid))),
        }
        export = asyncio.run(
            load_responses(
                api=api,
                sid=sid,
                file_format="json",
                language="es",
                completion_status="all",
                heading_type="code",
                response_type="short",
                from_response_id=None,
                to_response_id=None,
                fields=None,
            )
        )
        golden["responseDataset"] = {
            "surveyId": str(sid),
            "language": "es",
            "responses": export.responses,
        }
        write(out / "remote-api" / path.name, golden)
        # dual-scale-question-level (intentional-changes.json): the patched option reads
        # answeroptions_multiscale where the remote loader leaves it.
        os.environ["CONFORMANCE_QUESTION_LEVEL_MULTISCALE"] = "1"
        try:
            changed = {
                "input": f"remote-api/{path.name}",
                "change": "dual-scale-question-level",
                **outcome(
                    lambda api=api, sid=sid: asyncio.run(load_remote_survey_structure(api, sid))
                ),
            }
        finally:
            del os.environ["CONFORMANCE_QUESTION_LEVEL_MULTISCALE"]
        write(out / "remote-api" / f"{path.stem}.dual-scale-question-level.json", changed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()

    os.environ.setdefault("ENV", "dev")
    os.environ.setdefault("ALLOW_IN_MEMORY_STATE", "true")
    # Only lets the adapter's configuration import; no token is signed or checked here.
    os.environ.setdefault("DICTIONARY_SERVICE_JWT_SECRET", "conformance-generator-" + "0" * 32)
    sys.path.insert(0, str(arguments.adapter))
    from services.survey_structure import build_survey_structure, survey_structure_from_lss

    for path in sorted((arguments.fixtures / "lss").glob("*.lss")):
        content = path.read_bytes()
        write(
            arguments.out / "lss" / f"{path.stem}.json",
            {
                "input": f"lss/{path.name}",
                **outcome(lambda content=content: survey_structure_from_lss(content)),
            },
        )

    for path in sorted((arguments.fixtures / "remote").glob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        payload, source_format = fixture["payload"], fixture.get("sourceFormat", "remotecontrol")
        write(
            arguments.out / "remote" / path.name,
            {
                "input": f"remote/{path.name}",
                **outcome(
                    lambda payload=payload, source_format=source_format: build_survey_structure(
                        payload, source_format
                    )
                ),
            },
        )

    remote_api_goldens(arguments.fixtures, arguments.out)


if __name__ == "__main__":
    main()
