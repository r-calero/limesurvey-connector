# limesurvey-connector

English | [Español](README.es.md)

Python package for working with LimeSurvey surveys:

- `SurveyStructure`: a source-independent survey contract (version 2.1.0), with validation and diagnostics in Spanish and English.
- Data dictionaries in JSON and CSV, and translation of response datasets.
- Import of `.lss` files and normalization of LimeSurvey surveys, without a server.
- A LimeSurvey RemoteControl 2 client.
- An optional REST service built with FastAPI.

> **Status:** pre-alpha. All features are implemented and verified against the reference implementations; they have not yet been exercised against a production LimeSurvey server.

## Installation

```bash
pip install limesurvey-connector            # library, including RemoteControl 2 access
pip install "limesurvey-connector[api]"     # REST service (FastAPI, Redis, JWT)
pip install "limesurvey-connector[pandas]"  # DataFrame helpers
```

Python 3.12 or later is required.

## Validate a SurveyStructure

The contract is published separately as [`survey-structure`](packages/survey-structure), a dependency-free Python port of the TypeScript package; `limesurvey_connector.survey_structure` re-exports it.

```python
from limesurvey_connector.survey_structure import safe_parse_survey_structure

result = safe_parse_survey_structure(document)
if not result.success:
    for issue in result.issues:
        print(issue["path"], issue["message"])
```

`parse_survey_structure` returns the validated document or raises `SurveyStructureValidationError`. Issues have the same `path`, `code`, `params` and `message` as the TypeScript package, so a front end using `survey-structure` gets the same diagnostics. `get_survey_execution_issues` lists what a valid draft still needs before publication.

`responseValidation.responseFormatPattern` is ECMAScript source, tested as written with its `patternFlags`; it is translated to an equivalent `re` expression, and the few patterns Python cannot match identically are rejected ([details](conformance/known-divergences.json)).

## Data dictionaries and responses

```python
from survey_data_dictionary import dictionary_to_csv
from limesurvey_connector.limesurvey import load_lss
from limesurvey_connector.limesurvey.dictionary import build_limesurvey_dictionary
from limesurvey_connector.limesurvey.responses import translate_csv

loaded = load_lss("survey.lss")  # SurveyLoadResult
dictionary = build_limesurvey_dictionary(loaded["survey"], source_issues=loaded["issues"])
# Questions plus LimeSurvey system columns
codebook = dictionary_to_csv(
    build_limesurvey_dictionary(loaded["survey"], include_system_fields=True)
)
result = translate_csv(dictionary, export_text, format="vv", delimiter="\t")
```

Dictionaries use LimeSurvey's own column names in underscore form (`Q1_SQ001`, `Q2_SQ001_0`, `Q11_SQ001comment`, `Q12_other`); exports with bracketed code headings (`Q1[SQ001]`) are converted when read. In `vv` exports, `{question_not_shown}` is translated as missing. `includeTimingFields` adds `interviewtime`, `groupTime<id>` and `<code>Time`.

The dictionary logic is published separately as [`survey-data-dictionary`](packages/survey-data-dictionary). `translate_csv` reads LimeSurvey exports the way the reference API does and keeps every column: system columns such as `submitdate` or `lastpage` are translated as typed fields, and only headers passed in `ignored_headers` are dropped.

## LimeSurvey RemoteControl 2

```python
from limesurvey_connector.remote import LimeSurveyClient

with LimeSurveyClient(url, username, password, allowed_hosts=["surveys.example.org"]) as ls:
    surveys = ls.list_surveys()
    dictionary = ls.get_dictionary(783587, language="es", include_system_fields=True)
    variable = ls.get_field(783587, "Q01", language="es")
    responses = ls.export_responses(783587, completion_status="complete")
```

Errors are `LimeSurveyError` subclasses with a stable `code` (`LS_SESSION_EXPIRED`, `LS_UNREACHABLE`, ...).

## REST service

```bash
cp .env.example .env   # fill in the secrets
docker compose up --build -d
```

The image installs the PyPI release named in `CONNECTOR_PYPI_VERSION`; leave it empty to build the current checkout.

Swagger is at `/docs`. Authentication (ADR 4):

1. `POST /v1/limesurvey/sessions` with `X-Api-Key` and `{url, username, password}` returns `accessToken`.
2. LimeSurvey routes take `Authorization: Bearer <accessToken>`; `DELETE /v1/limesurvey/sessions/current` revokes it.
3. Routes that do not contact LimeSurvey take only `X-Api-Key`.

| Route | Credential |
| --- | --- |
| `GET /v1/limesurvey/surveys` | Bearer |
| `GET /v1/limesurvey/surveys/{sid}/structure` | Bearer |
| `GET /v1/limesurvey/surveys/{sid}/fields/{questionCode}` | Bearer |
| `GET /v1/limesurvey/surveys/{sid}/dictionary` (`format`, `questionCode`, `includeSystemFields`, `refresh`) | Bearer |
| `GET /v1/limesurvey/surveys/{sid}/responses` (JSON or original CSV) | Bearer |
| `GET /v1/limesurvey/surveys/{sid}/responses/translated` | Bearer |
| `POST /v1/survey-structure/validate`, `/v1/survey-structure/readiness` | API key |
| `POST /v1/dictionaries/generate`, `/v1/dictionaries/from-lss`, `/v1/survey-structures/from-lss` | API key |
| `POST /v1/responses/translate` (records or CSV) | API key |
| `GET /v1/contract`, `/v1/compatibility` | API key |

Messages follow `Accept-Language` (es or en). Configuration is documented in `.env.example`.

## Development

Requirements: [uv](https://docs.astral.sh/uv/), and Node 22 for the conformance suite.

```bash
make sync        # create the environment with every package and extra
make lint        # ruff
make typecheck   # mypy --strict
make test        # pytest
```

Run the service locally:

```bash
uv run uvicorn limesurvey_connector.api.app:create_app --factory --reload
curl http://127.0.0.1:8000/health
```

## Conformance with the reference implementations

This package reproduces the behavior of four existing projects:

| Project | Language | Role |
| --- | --- | --- |
| [survey-structure](https://github.com/JJKid/survey-structure) | TypeScript | `SurveyStructure` contract |
| [survey-data-dictionary](https://github.com/JJKid/survey-data-dictionary) | TypeScript | Dictionaries and translation |
| [limesurvey-rc2-api](https://github.com/JJKid/limesurvey-rc2-api) | Python | RemoteControl 2 access and normalization |
| [limesurvey-dictionary-api](https://github.com/JJKid/limesurvey-dictionary-api) | TypeScript | Public REST API |

Those projects are not modified. `conformance/sources.lock.json` pins the commit used for each one, and `conformance/goldens/` stores the results they produce for the inputs in `conformance/fixtures/`. Deliberate improvements over the references are declared in `conformance/intentional-changes.json`. The tests compare this package against those results, and every `SurveyStructure` it produces must also pass the TypeScript validator in `conformance/tools/`.

```bash
make goldens         # rebuild the references at their pinned commits and rewrite the goldens
make goldens-check   # fail if the references no longer produce the committed goldens
```

Both commands expect the four repositories next to this one (`../survey-structure`, and so on). They are read through `git archive`; builds run inside `conformance/.work/`, which is ignored by git. Set `SOURCES=remote` to clone them from GitHub instead.

## Design decisions

See [docs/adr](docs/adr).

## License

[MIT](LICENSE).
