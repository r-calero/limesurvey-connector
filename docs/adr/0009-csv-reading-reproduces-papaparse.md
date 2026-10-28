# 9. CSV reading reproduces papaparse

Date: 2026-09-30
Status: accepted

## Context

limesurvey-dictionary-api reads LimeSurvey CSV exports with papaparse 5.7 (delimiter guessing, line-ending detection, quote handling, empty-line skipping). Python's `csv` module guesses delimiters, splits lines and reports malformed quotes differently, so the same file could map to different columns.

## Decision

- `limesurvey_connector/limesurvey/_papaparse.py` ports the parts of papaparse the API uses: leading BOM removal, line-ending detection, delimiter guessing over `, \t | ; RS US`, the quoted-field state machine with its `MissingQuotes` and `InvalidQuotes` errors, and `skipEmptyLines: true`.
- `responses.csv_to_canonical_responses` reproduces `csv-dataset.ts`: `vv` exports use their second header row, the first header loses a BOM, `N/A` is the default missing marker, and a declared export format is checked against the mapped headers.
- The reader is verified against papaparse itself on 34 edge cases, and end to end against the reference translation of every CSV fixture.

## Consequences

- A CSV export is read the same way by both implementations, so row alignment, response ids and parse errors match.
- The reader is internal to the connector; the dictionary package only receives headers and rows.
