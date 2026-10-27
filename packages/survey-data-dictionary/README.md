# survey-data-dictionary (Python)

English | [Español](README.es.md)

Python port of [survey-data-dictionary](https://github.com/JJKid/survey-data-dictionary). It turns a `SurveyStructure` into a data dictionary (response columns, allowed values and aliases), serializes it to CSV, and translates response records or tabular data with it. Results match the TypeScript package.

Depends only on [survey-structure](../survey-structure) (the Python port of the contract).

## Origin and versions

| Python release | npm release it reproduces | `surveyStructureVersion` |
| --- | --- | --- |
| `2.1.0` | `survey-data-dictionary@2.1.0` (commit `99b1bd1`) | `2.1.0` |

The Python version follows the npm version it reproduces; Python-only fixes are post-releases. `survey_data_dictionary.UPSTREAM` records the npm release and commit. Parity is checked in [limesurvey-connector](https://github.com/r-calero/limesurvey-connector) against results produced by the TypeScript package.

## Usage

```python
from survey_data_dictionary import build_survey_dictionary, dictionary_to_csv, translate_dataset

dictionary = build_survey_dictionary(structure, aliases={"external_consent": "Q1"})
csv_text = dictionary_to_csv(dictionary)
translated = translate_dataset(dictionary, [{"Q1": "A1"}], response_ids=["r-1"])
```

- `build_survey_dictionary(structure, *, aliases, source_issues, strict)`: validates the survey first and raises `SurveyStructureValidationError` for an invalid one.
- `get_question_dictionary(dictionary, code)`: entries of one question.
- `translate_response` / `translate_dataset`: values keep `sourceValue` and gain `displayValue`; unknown keys are preserved in `unmappedValues`.
- `map_tabular_dataset(dictionary, headers, rows, ...)`: align rows by position without collapsing repeated headers.
- `dictionary_to_csv`, `translated_dataset_to_csv`: CSV with spreadsheet formulas neutralized.
- `safe_parse_survey_dictionary`, `safe_parse_survey_response_dataset`: runtime validation of dictionaries and datasets received from elsewhere.

`ABSENT` marks an omitted optional value (JavaScript `undefined`); `None` is JSON `null`.

## License

MIT. The original TypeScript package is by the survey-data-dictionary authors; see its repository.
