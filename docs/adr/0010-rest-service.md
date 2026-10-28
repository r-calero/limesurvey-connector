# 10. REST service

Date: 2026-09-30
Status: accepted

## Context

The service combines what limesurvey-dictionary-api (public API) and limesurvey-rc2-api (LimeSurvey adapter) do as two processes. Data Curation Workspace is its main consumer (ADR 4).

## Decision

- One FastAPI process (`limesurvey_connector.api`) plus Redis. There is no internal hop, so the internal service JWT of the references disappears.
- `limesurvey_connector.remote.LimeSurveyClient` is a synchronous library; the service runs its calls in worker threads with total time limits (login 10 s, survey list 10 s, survey load 120 s, response export 60 s).
- Routes keep the paths, query parameters, error codes and response headers of limesurvey-dictionary-api where they overlap. New routes: survey list, structure, single field, translated responses and publication readiness.
- Error bodies are `{code, message, details?}`. Messages follow `Accept-Language` (es or en), falling back to `APP_LOCALE`; contract diagnostics include path, JSON pointer, rule and context as in the reference.
- Limits: requests per IP per minute, logins per IP and username, response exports per session and survey, body size, `.lss` size, response export size and field count.
- Load results are cached in Redis per account, survey and language for `CACHE_TTL_SECONDS`; responses are never cached.
- Expired sessions are logged out of LimeSurvey by a background task; with several replicas only the one that claims the expiry entry does it.

## Differences from the references

- The per-account limit on concurrent LimeSurvey calls is enforced per process, not through Redis across replicas.
- The rc2-api concurrency optimizer (disabled by default there) is not ported.
- Session tokens are JWTs instead of opaque strings (ADR 4).
- A question group without questions is loaded as empty. LimeSurvey answers `list_questions` for such a group with the status "No questions found", which Citric raises as an error; limesurvey-rc2-api lets it abort the whole survey load.

## Consequences

- One container and Redis replace three containers.
- Behavior shared with the references is covered by the conformance goldens, including an end-to-end golden of the rc2-api remote loader fed with recorded RemoteControl 2 answers.
