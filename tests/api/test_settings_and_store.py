import asyncio
import time

import pytest

from limesurvey_connector.api.app import _close_expired_sessions
from limesurvey_connector.api.settings import Settings
from limesurvey_connector.api.store import MemoryStore, StoredSession
from tests.support.fake_limesurvey import FakeGateway

SECRET = "x" * 40


def test_production_requires_explicit_configuration():
    base = {"APP_ENV": "production", "API_KEYS": SECRET, "JWT_KEYS": f"k1:{SECRET}"}
    with pytest.raises(ValueError, match="REDIS_URL"):
        Settings.from_env(base)
    with pytest.raises(ValueError, match="CORS_ORIGINS"):
        Settings.from_env({**base, "REDIS_URL": "redis://r"})
    settings = Settings.from_env(
        {
            **base,
            "REDIS_URL": "redis://r",
            "CORS_ORIGINS": "https://dcw.example.org",
            "ALLOWED_LIMESURVEY_HOSTS": "Surveys.example.org",
        }
    )
    assert settings.is_production
    assert settings.allowed_limesurvey_hosts == ("surveys.example.org",)
    assert settings.allow_in_memory_state is False


@pytest.mark.parametrize("value", ["short", "replace_with_" + "x" * 40])
def test_weak_secrets_are_rejected(value):
    with pytest.raises(ValueError, match="API_KEYS"):
        Settings.from_env({"API_KEYS": value, "JWT_KEYS": f"k1:{SECRET}"})


def test_jwt_keys_format():
    with pytest.raises(ValueError, match="key id"):
        Settings.from_env({"API_KEYS": SECRET, "JWT_KEYS": SECRET})
    settings = Settings.from_env({"API_KEYS": SECRET, "JWT_KEYS": f"new:{SECRET}, old:{'y' * 40}"})
    assert [key for key, _ in settings.jwt_keys] == ["new", "old"]


def test_expired_sessions_are_logged_out():
    store, gateway = MemoryStore(), FakeGateway()

    async def scenario():
        await store.set_session(
            "s1", StoredSession("https://x/admin/remotecontrol", "ana", "k1", "c", time.time() - 1)
        )
        stop = asyncio.Event()
        task = asyncio.create_task(_close_expired_sessions(store, gateway, stop))
        await asyncio.sleep(0)
        stop.set()
        await task

    asyncio.run(scenario())
    assert gateway.backends["k1"].closed


def test_redis_store_sessions_cache_and_counters():
    import fakeredis

    from limesurvey_connector.api.store import RedisStore

    async def scenario():
        store = RedisStore(client=fakeredis.FakeAsyncRedis(decode_responses=True))
        assert await store.is_ready()
        live = StoredSession("https://x/admin/remotecontrol", "ana", "k1", "c", time.time() + 60)
        old = StoredSession("https://x/admin/remotecontrol", "ana", "k2", "c", time.time() - 1)
        await store.set_session("live", live)
        await store.set_session("old", old)
        assert await store.get_session("live") == live
        assert await store.get_session("old") is None
        assert [session_id for session_id, _ in await store.take_expired_sessions()] == ["old"]
        assert await store.take_expired_sessions() == []
        await store.delete_session("live")
        assert await store.get_session("live") is None
        await store.set_json("key", {"a": [1]}, 60)
        assert await store.get_json("key") == {"a": [1]}
        assert (await store.increment("rate", 60))[0] == 1
        assert (await store.increment("rate", 60))[0] == 2

    asyncio.run(scenario())
