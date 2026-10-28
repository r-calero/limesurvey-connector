# 8. `survey-structure` is published as its own package

Date: 2026-09-30
Status: accepted

## Context

The contract validation has no dependencies and is useful without LimeSurvey: any Python project that exchanges `SurveyStructure` documents with the TypeScript tools can use it. ADR 1 anticipated splitting subpackages later.

## Decision

- `packages/survey-structure` is a second distribution in the same uv workspace, with the import name `survey_structure` and no runtime dependencies.
- `limesurvey-connector` depends on it; `limesurvey_connector.survey_structure` re-exports it so existing imports keep working.
- Its version is the npm release it reproduces (`2.1.0` for `survey-structure@2.1.0`). While parity is incomplete it is a development release (`2.1.0.dev0`); Python-only fixes are post-releases. `survey_structure.UPSTREAM` records the npm release and commit.
- The README states the origin and links to the TypeScript repository. The conformance suite stays in this repository, where the reference can be built.
- A test fails if `survey_structure` imports the connector or any third-party package.

## Consequences

- The package can be released on PyPI independently of the connector.
- `survey-data-dictionary` follows the same pattern (`packages/survey-data-dictionary`, import `survey_data_dictionary`, version `2.1.0` for npm `survey-data-dictionary@2.1.0`), re-exported as `limesurvey_connector.data_dictionary`. It depends only on `survey-structure`.

## Update 2026-10-15

The npm packages never published 3.0.0: their version moved to 2.1.0, which is also the contract version (`surveyStructureVersion`). The Python packages follow that numbering and are released as `2.1.0` once their conformance suite passes against the pinned 2.1.0 commits; no 3.0.0 is published on PyPI.
