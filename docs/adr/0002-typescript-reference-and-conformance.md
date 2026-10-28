# 2. TypeScript packages are the reference; parity is verified with goldens

Date: 2026-09-30
Status: accepted

## Context

`survey-structure` and `survey-data-dictionary` (TypeScript) define the contract and dictionary behavior. They remain in use by other applications, including front ends that may parse a `SurveyStructure` produced by this package. `limesurvey-rc2-api` holds the Python normalization code and `limesurvey-dictionary-api` the public HTTP behavior.

## Decision

- The four projects are the reference implementations. This package reproduces their behavior; it does not redefine it.
- `conformance/sources.lock.json` pins one commit per project.
- `conformance/generate/run.py` exports each project with `git archive` into `conformance/.work`, builds it there and records its output for the inputs in `conformance/fixtures` under `conformance/goldens`, with a `MANIFEST.json` of hashes.
- Goldens are committed. They are regenerated explicitly (`make goldens`) and checked for drift (`make goldens-check`, weekly workflow).
- `conformance/tools/validate-survey.cjs` is the TypeScript validator built from the pinned `survey-structure`. Tests use it to check that every `SurveyStructure` and `SurveyLoadResult` this package emits is accepted by the reference contract. It is never used at runtime.

## Consequences

- Any change in a reference project shows up as a golden difference that names the files affected.
- Node 22 is needed to regenerate goldens and to run the round-trip tests, not to use the package.
