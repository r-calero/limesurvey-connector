# 6. Intentional changes from the reference behavior

Date: 2026-09-30
Status: accepted

## Context

Building the goldens exposed gaps in the reference implementations. The references are read-only (ADR 5), but this package may behave differently on purpose when its consumers need it.

## Decision

- Each change is declared in `conformance/intentional-changes.json` with the reference behavior, the connector behavior, its guards and any open points.
- Goldens for a change are still produced by the reference whenever possible. The generator prepares the reference inputs to reproduce the connector behavior, and the golden records the change id. The connector is tested with the plain request.
- When the reference needs an extra option to reproduce a change, a patch in `conformance/patches/<repository>/` adds that option to the build copy. A patch must not alter the default behavior; this is checked by regenerating the goldens and confirming that only files tagged with a change differ.
- A test fails if a golden names an undeclared change or a declared change has no golden.

## Changes

### `system-columns`

Data Curation Workspace uses this package mainly to obtain survey dictionaries and response data, and every column of a LimeSurvey export can matter to it (`submitdate` and `lastpage` tell whether a response is complete, `startdate` and `datestamp` give its duration, `token` links it to a participant).

The reference drops the visible metadata headers of an export by default, loses the response id in `sgqa` and `vv` exports, and reports code-form metadata as unknown keys. The connector instead:

- drops no column unless the caller lists it in `ignoredHeaders`, per request or per survey;
- recognizes the LimeSurvey system columns listed in `src/limesurvey_connector/limesurvey/system_columns.json`, by code or visible header, and translates them as typed fields when they are present;
- reads the response id from `Response ID`, `ID de la respuesta` or `id`;
- offers `includeSystemFields` (default `false`) so a dictionary can describe those columns as well as the questions.

A survey field whose code equals a system column always wins.

The entries added by `includeSystemFields` come from the catalog rather than from the reference. Visible headers marked `headersVerified: false` in the catalog, and group or question timing columns, still need to be confirmed against a real export.

### Later changes

`conformance/intentional-changes.json` lists every change with its reference behavior, the connector behavior and how it is verified (`verifiedBy`): reference goldens (a neutral option added by a patch makes the reference produce the result), connector goldens (`conformance/goldens-connector`, produced by `conformance/generate/connector_goldens.py` from anonymized fixtures in `conformance/fixtures/connector` and reviewed by hand) or unit tests. Changes added after checking a real LimeSurvey 3.x server: `dual-scale-question-level`, `dual-scale-by-scale-id`, `lss-dbversion-355`, `array-increase-same-decrease`, `limesurvey-column-names`, `json-export-unwrap` and `empty-question-groups`.

## Consequences

- Behavior stays verifiable against the reference even where it differs on purpose.
- Changes worth keeping can be proposed upstream; once a reference adopts one, its entry, patch and generator adjustments are removed.
