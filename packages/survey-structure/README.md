# survey-structure (Python)

English | [Español](README.es.md)

Python port of [survey-structure](https://github.com/JJKid/survey-structure), the TypeScript contract for source-independent survey definitions. It validates `SurveyStructure` and `SurveyLoadResult` documents (SurveyStructure 2.1.0) and reports the same issues as the TypeScript package: same `path`, `code`, `params` and `message`.

No dependencies beyond the Python standard library.

## Origin and versions

| Python release | npm release it reproduces | `surveyStructureVersion` |
| --- | --- | --- |
| `2.1.0` | `survey-structure@2.1.0` (commit `0148e3f`) | `2.1.0` |

The Python version is the npm version it reproduces, which since 2.1.0 is also the contract version. A Python-only fix is published as a post-release (`2.1.0.post1`). `survey_structure.UPSTREAM` records the npm release and commit.

Parity is checked in [limesurvey-connector](https://github.com/r-calero/limesurvey-connector), where the TypeScript package is built at its pinned commit to produce expected results: 234 contract cases with their Spanish and English messages, 73 language tags, 20,608 pattern, flag and value combinations, 107 image URLs, and the grading and numeric-text helpers. Every document this package accepts is also accepted by the TypeScript validator.

`localize_survey_validation_issue(issue, locale)` gives the Spanish or English text of any issue, as `localizeSurveyValidationIssue` does.

## Installation

```bash
pip install survey-structure
```

Python 3.12 or later.

## Usage

```python
from survey_structure import parse_survey_structure, safe_parse_survey_structure

result = safe_parse_survey_structure(document)
if not result.success:
    for issue in result.issues:
        print(issue["path"], issue["code"], issue["message"])

survey = parse_survey_structure(document)  # raises SurveyStructureValidationError
```

Other functions:

- `parse_survey_load_result` / `safe_parse_survey_load_result`: import or load envelopes.
- `get_survey_execution_issues(survey)`: what a valid draft still needs before publication.
- `field_response_keys(field)`: response columns a field produces.
- `to_python_pattern(pattern, flags)` and `test_pattern(pattern, value, flags)`: use a `responseFormatPattern` from Python.
- `calculate_survey_score` and `grade_survey_answer`: automatic grading of normalized answers.
- `parse_survey_response_record`, `is_numeric_text`, `number_character_length`, `is_month_day`, `month_day_count` and `validation_pattern_source`.
- `FIELD_WIDGET_COMPATIBILITY`, `SURVEY_STRUCTURE_VERSION`, and `TypedDict` definitions in `survey_structure.types`.

## Patterns

`responseFormatPattern` is ECMAScript source, tested as written (without anchors), and `patternFlags` may hold `i`, `m` and `s`. The package translates the pattern to an equivalent `re` expression evaluated on UTF-16 code units, as ECMAScript does, including ECMAScript's case folding for `i` and its line terminators for `m`. Patterns Python cannot match identically (variable-width look-behind, a back-reference inside a repeated group that contains its capture, a back-reference with `i`, group names with `$`) are rejected, so every accepted pattern means the same in both languages.

Image URLs are checked as `new URL()` does (WHATWG URL Standard); internationalized domain names use Python's IDNA 2003 codec, so a few unusual non-ASCII hosts may be judged differently.

## License

MIT. The original TypeScript package is by the survey-structure authors; see its repository.
