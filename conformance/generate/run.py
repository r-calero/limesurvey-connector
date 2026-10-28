"""Build the reference implementations at their locked commits and write the goldens.

The sibling repositories are only read through ``git archive``; every build runs
inside ``conformance/.work`` so their working trees stay untouched. Patches in
``conformance/patches/<repository>`` are applied to those copies only; each one
adds options and keeps the default behavior unchanged.
"""

from __future__ import annotations

import argparse
import filecmp
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

CONFORMANCE = Path(__file__).resolve().parents[1]
ROOT = CONFORMANCE.parent
WORK = CONFORMANCE / ".work"
SOURCES = WORK / "src"
PACKAGES = SOURCES / ".artifacts" / "packages"
GOLDENS = CONFORMANCE / "goldens"
FIXTURES = CONFORMANCE / "fixtures"
TOOLS = CONFORMANCE / "tools"
GENERATE = CONFORMANCE / "generate"
PATCHES = CONFORMANCE / "patches"


def run(command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def output(command: list[str], cwd: Path | None = None) -> str:
    return subprocess.run(
        command, cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def load_lock() -> dict[str, dict[str, str]]:
    return json.loads((CONFORMANCE / "sources.lock.json").read_text(encoding="utf-8"))


def export_source(name: str, entry: dict[str, str], mode: str) -> Path:
    target = SOURCES / name
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True)
    if mode == "local":
        repository = (ROOT / entry["path"]).resolve()
    else:
        repository = WORK / "clones" / name
        if not repository.exists():
            run(["git", "clone", "--quiet", entry["remote"], str(repository)])
        run(["git", "fetch", "--quiet", "origin", entry["commit"]], cwd=repository)
    with tempfile.TemporaryDirectory() as temporary:
        archive = Path(temporary) / f"{name}.tar"
        run(
            [
                "git",
                "-C",
                str(repository),
                "archive",
                "--format=tar",
                "-o",
                str(archive),
                entry["commit"],
            ]
        )
        with tarfile.open(archive) as bundle:
            bundle.extractall(target, filter="data")
    for patch in sorted((PATCHES / name).glob("*.patch")):
        run(["git", "apply", "-p1", str(patch)], cwd=target)
    return target


def npm_pack(directory: Path) -> Path:
    PACKAGES.mkdir(parents=True, exist_ok=True)
    filename = output(
        ["npm", "pack", "--silent", "--pack-destination", str(PACKAGES)], cwd=directory
    )
    return PACKAGES / filename.splitlines()[-1]


def use_local_tarball(directory: Path, dependency: str, tarball: Path) -> None:
    manifest_path = directory / "package.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["dependencies"][dependency] = f"file:{tarball}"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # Lockfile integrity refers to archives that are not published.
    (directory / "package-lock.json").unlink(missing_ok=True)


def build_references(mode: str) -> dict[str, Path]:
    lock = load_lock()
    shutil.rmtree(PACKAGES, ignore_errors=True)
    sources = {name: export_source(name, entry, mode) for name, entry in lock.items()}

    structure = sources["survey-structure"]
    run(["npm", "ci", "--no-audit", "--no-fund"], cwd=structure)
    run(["npm", "run", "build"], cwd=structure)
    structure_tarball = npm_pack(structure)

    dictionary = sources["survey-data-dictionary"]
    use_local_tarball(dictionary, "survey-structure", structure_tarball)
    run(["npm", "install", "--no-audit", "--no-fund"], cwd=dictionary)
    run(["npm", "run", "build"], cwd=dictionary)
    dictionary_tarball = npm_pack(dictionary)

    service = sources["limesurvey-dictionary-api"]
    use_local_tarball(service, "survey-structure", structure_tarball)
    use_local_tarball(service, "survey-data-dictionary", dictionary_tarball)
    run(["npm", "install", "--no-audit", "--no-fund"], cwd=service)
    run(["npm", "run", "build"], cwd=service)

    adapter = sources["limesurvey-rc2-api"]
    venv = WORK / "rc2-venv"
    if not (venv / "bin" / "python").exists():
        run(["uv", "venv", "--quiet", "--python", "3.12", str(venv)])
    run(
        [
            "uv",
            "pip",
            "install",
            "--quiet",
            "--python",
            str(venv / "bin" / "python"),
            "-r",
            "requirements.txt",
        ],
        cwd=adapter,
    )
    return sources


def generate(sources: dict[str, Path], destination: Path) -> None:
    shutil.rmtree(destination, ignore_errors=True)
    destination.mkdir(parents=True)
    run(
        [
            str(WORK / "rc2-venv" / "bin" / "python"),
            str(GENERATE / "limesurvey_goldens.py"),
            "--adapter",
            str(sources["limesurvey-rc2-api"]),
            "--fixtures",
            str(FIXTURES),
            "--out",
            str(destination / "limesurvey"),
        ]
    )
    run(
        [
            "node",
            str(GENERATE / "survey_structure.mjs"),
            "--package",
            str(sources["survey-structure"]),
            "--fixtures",
            str(FIXTURES),
            "--out",
            str(destination / "survey-structure"),
        ]
    )
    run(
        [
            "node",
            str(GENERATE / "data_dictionary.mjs"),
            "--dictionary",
            str(sources["survey-data-dictionary"]),
            "--service",
            str(sources["limesurvey-dictionary-api"]),
            "--fixtures",
            str(FIXTURES),
            "--goldens",
            str(destination),
            "--out",
            str(destination / "data-dictionary"),
        ]
    )
    write_manifest(destination)


def write_manifest(destination: Path) -> None:
    lock = load_lock()
    files = {
        path.relative_to(destination).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(destination.rglob("*"))
        if path.is_file() and path.name != "MANIFEST.json"
    }
    manifest = {
        "sources": {name: entry["commit"] for name, entry in lock.items()},
        "patches": {
            path.relative_to(PATCHES).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(PATCHES.rglob("*.patch"))
        },
        "node": output(["node", "--version"]),
        "files": files,
    }
    (destination / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


VENDORED_TOOLS = (
    "validate-survey.cjs",
    "survey-structure.schema.json",
    "survey-load-result.schema.json",
)


def vendor_tools(sources: dict[str, Path], destination: Path = TOOLS) -> None:
    schema = sources["survey-structure"] / "schema"
    destination.mkdir(parents=True, exist_ok=True)
    for filename in VENDORED_TOOLS:
        shutil.copyfile(schema / filename, destination / filename)


def compare(expected: Path, actual: Path) -> list[str]:
    differences: list[str] = []
    expected_files = {p.relative_to(expected) for p in expected.rglob("*") if p.is_file()}
    actual_files = {p.relative_to(actual) for p in actual.rglob("*") if p.is_file()}
    for missing in sorted(expected_files - actual_files):
        differences.append(f"removed: {missing}")
    for added in sorted(actual_files - expected_files):
        differences.append(f"added: {added}")
    for common in sorted(expected_files & actual_files):
        if not filecmp.cmp(expected / common, actual / common, shallow=False):
            differences.append(f"changed: {common}")
    return differences


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", choices=["local", "remote"], default="local")
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate into a temporary directory and compare with goldens/",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="reuse the builds already present in conformance/.work",
    )
    arguments = parser.parse_args()

    os.environ.setdefault("npm_config_update_notifier", "false")
    if arguments.skip_build:
        sources = {name: SOURCES / name for name in load_lock()}
    else:
        sources = build_references(arguments.sources)

    if not arguments.check:
        generate(sources, GOLDENS)
        vendor_tools(sources)
        return 0

    candidate = WORK / "check-goldens"
    generate(sources, candidate)
    differences = compare(GOLDENS, candidate)
    candidate_tools = WORK / "check-tools"
    shutil.rmtree(candidate_tools, ignore_errors=True)
    vendor_tools(sources, candidate_tools)
    differences += [
        f"changed: tools/{filename}"
        for filename in VENDORED_TOOLS
        if not filecmp.cmp(TOOLS / filename, candidate_tools / filename, shallow=False)
    ]
    for line in differences:
        print(line)
    if differences:
        print("Goldens differ from the reference implementations.", file=sys.stderr)
        return 1
    print("Goldens match the reference implementations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
