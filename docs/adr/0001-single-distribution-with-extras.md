# 1. Single distribution with optional extras

Date: 2026-09-30
Status: accepted, amended by ADR 8

## Context

The code covers four concerns that other projects ship separately: the `SurveyStructure` contract, data dictionaries, LimeSurvey access, and a REST API. The main consumer, Data Curation Workspace, runs a Python 3.12 FastAPI backend with pydantic 2.11 and may either call the REST API or embed the library.

## Decision

Publish one distribution, `limesurvey-connector`, with the import package `limesurvey_connector`:

| Subpackage | Installed by |
| --- | --- |
| `survey_structure`, `data_dictionary`, `limesurvey` | base |
| `remote` (RemoteControl 2 client, uses `citric`) | base |
| `api` (FastAPI, pydantic, Redis, JWT, multipart) | `[api]` extra |
| DataFrame helpers | `[pandas]` extra |

`citric` is part of the base install: connecting to LimeSurvey is the purpose of the package, and on Python 3.12 it only adds `requests`.

Dependencies use ranges compatible with Data Curation Workspace (Python `>=3.12`; `pydantic>=2.11,<3` in the `api` extra). The base install depends only on `defusedxml` and `citric`.

## Consequences

- `tests/test_dependency_boundary.py` fails if a base subpackage imports FastAPI, Starlette, pydantic, uvicorn, Redis, PyJWT, python-multipart or pandas.
- Subpackages can be split into separate distributions later without changing import paths.
