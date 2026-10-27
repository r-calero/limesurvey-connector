"""Session, cache and rate-limit storage: Redis, or memory for development and tests."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from redis.asyncio import Redis

_SESSION_PREFIX = "connector:session:"
_EXPIRATIONS = "connector:session-expirations"
_CACHE_PREFIX = "connector:cache:"
_RATE_PREFIX = "connector:rate:"


@dataclass(frozen=True)
class StoredSession:
    """What the service keeps for a LimeSurvey session; never the password."""

    lime_survey_url: str
    username: str
    remote_session_key: str
    client_id: str
    expires_at: float


class Store(Protocol):
    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def is_ready(self) -> bool: ...
    async def set_session(self, session_id: str, session: StoredSession) -> None: ...
    async def get_session(self, session_id: str) -> StoredSession | None: ...
    async def delete_session(self, session_id: str) -> None: ...
    async def take_expired_sessions(
        self, now: float | None = None
    ) -> list[tuple[str, StoredSession]]: ...
    async def get_json(self, key: str) -> Any: ...
    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None: ...
    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]: ...


class MemoryStore:
    """Single-process storage for development and tests."""

    def __init__(self) -> None:
        self._sessions: dict[str, StoredSession] = {}
        self._cache: dict[str, tuple[float, str]] = {}
        self._counters: dict[str, tuple[float, int]] = {}

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def is_ready(self) -> bool:
        return True

    async def set_session(self, session_id: str, session: StoredSession) -> None:
        self._sessions[session_id] = session

    async def get_session(self, session_id: str) -> StoredSession | None:
        session = self._sessions.get(session_id)
        return session if session is not None and session.expires_at > time.time() else None

    async def delete_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def take_expired_sessions(
        self, now: float | None = None
    ) -> list[tuple[str, StoredSession]]:
        current = time.time() if now is None else now
        expired = [
            (key, value) for key, value in self._sessions.items() if value.expires_at <= current
        ]
        for key, _ in expired:
            del self._sessions[key]
        return expired

    async def get_json(self, key: str) -> Any:
        entry = self._cache.get(key)
        if entry is None or entry[0] <= time.time():
            self._cache.pop(key, None)
            return None
        return json.loads(entry[1])

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._cache[key] = (time.time() + ttl_seconds, json.dumps(value))

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        now = time.time()
        reset_at, count = self._counters.get(key, (now + window_seconds, 0))
        if reset_at <= now:
            reset_at, count = now + window_seconds, 0
        self._counters[key] = (reset_at, count + 1)
        return count + 1, max(1, int(reset_at - now))


class RedisStore:
    """Shared storage. Sessions also sit in a sorted set so expired ones can be closed in LimeSurvey."""

    def __init__(self, url: str | None = None, *, client: Redis | None = None) -> None:
        if client is None:
            if url is None:
                raise ValueError("A Redis URL or client is required.")
            client = Redis.from_url(url, decode_responses=True, socket_connect_timeout=5)
        self._redis: Redis = client

    async def connect(self) -> None:
        await self._redis.ping()

    async def close(self) -> None:
        await self._redis.aclose()

    async def is_ready(self) -> bool:
        try:
            return bool(await self._redis.ping())
        except Exception:
            return False

    async def set_session(self, session_id: str, session: StoredSession) -> None:
        ttl = max(1, int(session.expires_at - time.time())) + 300
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.set(_SESSION_PREFIX + session_id, json.dumps(asdict(session)), ex=ttl)
            pipe.zadd(_EXPIRATIONS, {session_id: session.expires_at})
            await pipe.execute()

    async def get_session(self, session_id: str) -> StoredSession | None:
        raw = await self._redis.get(_SESSION_PREFIX + session_id)
        if not raw:
            return None
        session = StoredSession(**json.loads(raw))
        return session if session.expires_at > time.time() else None

    async def delete_session(self, session_id: str) -> None:
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.delete(_SESSION_PREFIX + session_id)
            pipe.zrem(_EXPIRATIONS, session_id)
            await pipe.execute()

    async def take_expired_sessions(
        self, now: float | None = None
    ) -> list[tuple[str, StoredSession]]:
        current = time.time() if now is None else now
        expired = []
        candidates = [
            str(item) for item in await self._redis.zrangebyscore(_EXPIRATIONS, 0, current)
        ]
        for session_id in candidates:
            # Only the replica that removes the entry closes the session.
            if not await self._redis.zrem(_EXPIRATIONS, session_id):
                continue
            raw = await self._redis.getdel(_SESSION_PREFIX + session_id)
            if raw:
                expired.append((session_id, StoredSession(**json.loads(raw))))
        return expired

    async def get_json(self, key: str) -> Any:
        raw = await self._redis.get(_CACHE_PREFIX + key)
        return json.loads(raw) if raw else None

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        await self._redis.set(_CACHE_PREFIX + key, json.dumps(value), ex=ttl_seconds)

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        name = _RATE_PREFIX + key
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.incr(name)
            pipe.expire(name, window_seconds, nx=True)
            pipe.ttl(name)
            count, _, ttl = await pipe.execute()
        return int(count), max(1, int(ttl))
