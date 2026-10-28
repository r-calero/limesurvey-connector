import pytest

from tests.support.conformance import (
    CONFORMANCE,
    FIXTURES,
    GOLDENS,
    manifest,
    read_json,
    sha256,
    validation_cases,
)

pytestmark = pytest.mark.conformance


def test_manifest_lists_every_golden_with_its_hash():
    listed = manifest()["files"]
    present = {
        path.relative_to(GOLDENS).as_posix(): path
        for path in GOLDENS.rglob("*")
        if path.is_file() and path.name != "MANIFEST.json"
    }
    assert set(listed) == set(present)
    changed = [name for name, path in present.items() if sha256(path) != listed[name]]
    assert changed == []


def test_manifest_matches_locked_sources_and_patches():
    lock = read_json(CONFORMANCE / "sources.lock.json")
    assert manifest()["sources"] == {name: entry["commit"] for name, entry in lock.items()}
    patches = CONFORMANCE / "patches"
    assert manifest()["patches"] == {
        path.relative_to(patches).as_posix(): sha256(path)
        for path in sorted(patches.rglob("*.patch"))
    }


def test_goldens_reference_existing_fixtures():
    referenced = [read_json(path)["input"] for path in (GOLDENS / "limesurvey").rglob("*.json")]
    for directory in (GOLDENS / "data-dictionary").iterdir():
        origin = read_json(directory / "dictionary.json")["fixture"]
        if origin.startswith("fixtures/"):
            referenced.append(origin.removeprefix("fixtures/"))
    missing = [name for name in referenced if not (FIXTURES / name).is_file()]
    assert missing == []


def test_validation_cases_cover_both_outcomes():
    outcomes = {case["success"] for case in validation_cases()}
    assert outcomes == {True, False}


def test_intentional_changes_are_declared_and_used():
    changes = read_json(CONFORMANCE / "intentional-changes.json")["changes"]
    declared = {change["id"] for change in changes}
    by_reference = {
        change["id"] for change in changes if "reference-goldens" in change["verifiedBy"]
    }
    used = set()
    for path in [
        *(GOLDENS / "data-dictionary").rglob("*.json"),
        *(GOLDENS / "limesurvey").rglob("*.json"),
    ]:
        golden = read_json(path)
        if isinstance(golden, dict) and "change" in golden:
            used.add(golden["change"])
    assert used <= declared
    assert by_reference <= used
    assert all(change["verifiedBy"] for change in changes)
