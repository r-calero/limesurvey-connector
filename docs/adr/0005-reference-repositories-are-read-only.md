# 5. Reference repositories are read-only

Date: 2026-09-30
Status: accepted

## Context

The TypeScript packages, `limesurvey-rc2-api` and `limesurvey-dictionary-api` continue as independent projects with their own consumers.

## Decision

- This project never writes to those repositories. The conformance tooling reads them with `git archive` at a pinned commit and builds copies inside `conformance/.work`. Patches that add options for intentional changes (ADR 6) are applied to those copies only.
- Code taken from `limesurvey-rc2-api` is copied and adapted here; both copies evolve independently, and the LimeSurvey goldens detect behavioral divergence.

## Consequences

- Updating a reference means changing its commit in `sources.lock.json` and regenerating the goldens.

## Application: LimeSurvey normalization (2026-09-30)

`limesurvey_connector/limesurvey/normalization` is a copy of `services/survey_structure` from limesurvey-rc2-api at the pinned commit, with three changes: contract validation uses the Python `survey_structure` package instead of a Node subprocess, the unsupported-condition log goes to the module logger instead of `uvicorn.error`, and imports and types were adapted to this package. Its tests were ported as well. The LimeSurvey goldens compare both copies on every run.
