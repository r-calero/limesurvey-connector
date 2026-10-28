# 4. API keys for clients, JWT for LimeSurvey sessions

Date: 2026-09-30
Status: accepted

## Context

The REST service has two kinds of endpoints: those that talk to a LimeSurvey server through RemoteControl 2, and those that only transform data supplied by the caller. Data Curation Workspace authenticates its own users with an `HttpOnly` session cookie and stores third-party credentials encrypted on its backend.

## Decision

- `X-Api-Key` identifies the calling application. It is required to open a LimeSurvey session and for endpoints that do not use LimeSurvey: validation, dictionary generation from a `SurveyStructure` or `.lss`, and response translation.
- `POST /v1/limesurvey/sessions` logs in to LimeSurvey and returns a signed JWT (`Authorization: Bearer`). Every endpoint that uses the LimeSurvey session requires it: survey list, structure, field detail, dictionary, responses, and session close.
- Claims: `iss`, `aud` (client derived from the API key), `sub` (hash of LimeSurvey user and host), `jti` (session id), `iat`, `nbf`, `exp`, and `kid` in the header for key rotation.
- The LimeSurvey session key and password are never placed in the token. The session key is stored in Redis under `jti`; deleting the session revokes the token immediately.
- Verification pins the algorithm, checks `exp`, `nbf`, `iss` and `aud` with a small clock leeway, and requires the Redis session to exist and belong to the same client.
- No refresh tokens. When the token or the LimeSurvey session expires the client opens a new session.
- Tokens are meant to be held by the consumer's backend, not by browser code.

## Consequences

- Logout and expiry take effect without waiting for the token to expire.
- Consumers that embed the library call `limesurvey_connector.remote` directly and do not need a token.
