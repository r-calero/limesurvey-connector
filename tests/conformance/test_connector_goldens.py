"""Connector results for intentional changes that no reference option reproduces (reviewed by hand)."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GOLDENS = ROOT / "conformance" / "goldens-connector"
spec = importlib.util.spec_from_file_location(
    "connector_goldens", ROOT / "conformance" / "generate" / "connector_goldens.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
RESULTS = module.generate()

pytestmark = pytest.mark.conformance


def test_every_golden_is_produced():
    stored = {path.relative_to(GOLDENS).as_posix() for path in GOLDENS.rglob("*") if path.is_file()}
    assert stored == set(RESULTS)


@pytest.mark.parametrize("relative", sorted(RESULTS))
def test_connector_result_matches_golden(relative):
    path = GOLDENS / relative
    value = RESULTS[relative]
    if isinstance(value, str):
        assert value == path.read_text(encoding="utf-8")
    else:
        assert module.as_json(value) == json.loads(path.read_text(encoding="utf-8"))
