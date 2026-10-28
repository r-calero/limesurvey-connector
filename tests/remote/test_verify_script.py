import importlib.util
import json
from pathlib import Path

import pytest

from tests.support.fake_limesurvey import SURVEY_ID, FakeCitric

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "verify_limesurvey.py"

# The script is kept out of the repository; the test runs only where it exists.
pytestmark = pytest.mark.skipif(
    not SCRIPT.exists(), reason="scripts/verify_limesurvey.py is not present."
)


def load_script():
    spec = importlib.util.spec_from_file_location("verify_limesurvey", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verification_script_records_raw_answers_and_report(tmp_path, monkeypatch, capsys):
    backend = FakeCitric()
    groups = backend.list_groups
    backend.list_groups = lambda *args, **kwargs: [
        *groups(*args, **kwargs),
        {"gid": "99", "group_name": "Vacío"},
    ]
    monkeypatch.setattr("limesurvey_connector.remote._citric.create_client", lambda *args: backend)
    monkeypatch.setenv("LIMESURVEY_PASSWORD", "pw")
    script = load_script()
    status = script.main(
        [
            "--url",
            "https://surveys.example.org/index.php/admin/remotecontrol",
            "--user",
            "ana",
            "--sid",
            str(SURVEY_ID),
            "--out",
            str(tmp_path),
        ]
    )
    assert status == 0
    assert backend.closed
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["dualScaleQuestions"][0]["code"] == "DUAL"
    assert (tmp_path / "rc2" / "question-properties" / "115.json").exists()
    exported = json.loads((tmp_path / "exports" / "responses-code.json").read_text())["responses"]
    assert exported[0]["NOMBRE"] == "<masked>"
    assert exported[0]["CONSIENTE"] == "Y"
    assert "pw" not in "".join(path.read_text() for path in tmp_path.rglob("*") if path.is_file())
    assert "Written to" in capsys.readouterr().out
