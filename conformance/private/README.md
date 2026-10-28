# Private fixtures

Real survey exports used for local testing. Everything in this directory except this file is ignored by git: never commit real surveys or responses, and anonymize anything derived from them before adding it to `conformance/fixtures`.

- `lss/*.lss`: real survey structures. `tests/limesurvey/test_normalization.py` checks that each one normalizes to a valid `SurveyStructure` and, when `lss/golden/<name>.json` exists, that the result matches it.
- `<sid>/`: output of `scripts/verify_limesurvey.py` for a real survey (raw RemoteControl 2 answers, reduced and masked response exports, dictionary and a report of unrecognized columns).
- `exports/`: response files exported by hand from the LimeSurvey interface.
