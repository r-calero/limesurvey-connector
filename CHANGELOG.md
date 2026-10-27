# Changelog

## 0.1.0 - 2026-10-26

- Project structure, packaging with optional `api` and `pandas` extras, and CI.
- Conformance suite: goldens generated from survey-structure, survey-data-dictionary, limesurvey-rc2-api and limesurvey-dictionary-api at pinned commits.
- `/health` endpoint.
- Intentional change `system-columns`: LimeSurvey system columns are kept and typed when translating responses, no column is dropped by default, and dictionaries accept `includeSystemFields`.
- `survey_structure`: SurveyStructure 2.0.0 and SurveyLoadResult validation with issues identical to the TypeScript reference, publication readiness checks, response keys, `TypedDict` types and the conservative `validation.pattern` policy.
- Base install no longer depends on pydantic; it moved to the `api` extra.
- `validation.pattern` is translated to an equivalent `re` expression instead of rejecting ECMAScript-only syntax; `to_python_pattern` and `test_pattern` are public.
- The contract moved to its own package, `survey-structure` (`packages/survey-structure`), which mirrors the npm version it reproduces; `limesurvey_connector.survey_structure` re-exports it.
- `survey-data-dictionary` package (`packages/survey-data-dictionary`): dictionaries, CSV export, response translation, tabular mapping and runtime schemas, matching the TypeScript package.
- `limesurvey_connector.limesurvey.responses`: LimeSurvey CSV exports read as papaparse does, declared export formats, and the `system-columns` change (`translate_csv`, `translate_records`, `with_system_fields`).
- Number formatting and `JSON.stringify` follow ECMAScript in every generated message and CSV cell.
- LimeSurvey normalization (`limesurvey_connector.limesurvey.normalization`, `load_lss`): `.lss` files and RemoteControl 2 payloads to `SurveyLoadResult`, ported from limesurvey-rc2-api with its tests and validated with the Python contract instead of Node.
- Library logging uses a `NullHandler`; nothing is printed unless the application configures logging.
- `survey_structure.localize_survey_validation_issue`: Spanish and English diagnostics, identical to the reference in every case.
- `limesurvey_connector.remote.LimeSurveyClient`: RemoteControl 2 sessions, survey loading with bounded concurrency, retries and a total time limit, dictionaries, single-field detail and response export; URL policy and error classification ported from limesurvey-rc2-api.
- REST service (`limesurvey_connector.api`): API key and session JWT authentication, the routes of limesurvey-dictionary-api plus survey list, structure, field detail, translated responses and readiness; Redis storage, rate limits, localized errors, Dockerfile and Compose file.
- Surveys with an empty question group load through RemoteControl 2; the reference adapter fails on them ("No questions found").
- `scripts/verify_limesurvey.py`: records raw RemoteControl 2 answers and masked exports of a real survey under `conformance/private/` and reports unrecognized columns.
- Checked against a real LimeSurvey 3.x survey: `.lss` files with DBVersion 355 are accepted; question type E (increase/same/decrease) is supported; dual-scale questions are read from `answeroptions_multiscale` at the question level or split by `scale_id`, and LimeSurvey versions that lose a scale are reported with a pointer to the `.lss` file.
- Dictionaries use LimeSurvey's underscore column names (`Q_SQ001comment` for option comments, `Q_other` and `Q_othercomment` for "other" texts); bracketed code headings in CSV and JSON exports are converted when read; the RemoteControl JSON export is unwrapped and its ids become `responseIds`.
- Timing columns (`interviewtime`, `groupTime<id>`, `<code>Time`) are recognized, and `includeTimingFields` adds them to dictionaries.
- vv exports: the empty last column produced by the trailing tab is dropped, and `{question_not_shown}` is translated as missing while keeping the placeholder as its source value.
- Dual-scale questions without their own scale headers are labeled in the survey language (`Escala 1`/`Escala 2` in Spanish) instead of always `Scale 1`/`Scale 2`.
- SurveyStructure 2.1.0: `survey-structure` and `survey-data-dictionary` are released as `2.1.0`, the npm version they reproduce (npm never published 3.0.0). `contractVersion` becomes `surveyStructureVersion`, `validation` becomes `responseValidation` (`pattern` becomes `responseFormatPattern` with `patternFlags`), and source `extensions` become `originDetails`; documents in the 2.0.0 format are rejected, as in the TypeScript package.
- New in the contract port: `pattern-match` conditions, group navigation and randomization, option visibility and exclusive options, matrix cells, row visibility, row requirement and grading, numeric text and multiple numeric input rules, calendar bounds, `month-day` dates, images, REDCap origin details, new import diagnostics, automatic grading (`calculate_survey_score`), `parse_survey_response_record` and the numeric-text helpers.
- Patterns are tested as written (no implicit anchors) with ECMAScript semantics for the `i`, `m` and `s` flags; image URLs are validated as `new URL()` does.
- Dictionaries carry `surveyStructureVersion`, honor explicit comment keys, keep numbers stored as text as strings, accept scalar source aliases and generate SGQA aliases only for LimeSurvey surveys.
- LimeSurvey normalization follows limesurvey-rc2-api 2.1.0: question types U, 5, A, C, E and K, subquestion and array-filter visibility, exclusive options, date bounds and dropdowns, response-count limits, imported regular expressions, images, hidden and randomized questions, unconverted attribute reports, stricter language selection and the tests of the reference normalizer. LimeSurvey's own names are kept for other texts and list comments (`Q_other`, `Q_comment`).
- RemoteControl client: an unavailable language is rejected before loading questions (`LS_LANGUAGE_NOT_AVAILABLE`), rows of other languages are dropped, and subquestions LimeSurvey lists under a stale group are recovered and checked against their parent.
- The REST API reports `surveyStructureVersion` and `acceptedSurveyStructureVersions`, as limesurvey-dictionary-api 2.1.0 does.
