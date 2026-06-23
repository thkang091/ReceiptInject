"""Tests for EvalGrid SQLite cache."""

from pathlib import Path

from evalgrid.cache import SQLiteResponseCache, make_cache_key
from evalgrid.schemas import ModelRequest, ModelResponse


def _request() -> ModelRequest:
    return ModelRequest(
        model_provider="mock",
        model_name="mock",
        system_prompt="system",
        user_prompt="user",
        temperature=0.0,
        response_format={"type": "json_object"},
    )


def test_make_cache_key_is_stable() -> None:
    """Identical requests should produce identical cache keys."""

    assert make_cache_key(_request()) == make_cache_key(_request())


def test_sqlite_response_cache_round_trips(tmp_path: Path) -> None:
    """Cache should persist ModelResponse payloads."""

    cache = SQLiteResponseCache(tmp_path / "cache.sqlite")
    request = _request()
    key = make_cache_key(request)
    response = ModelResponse(
        task_id="task-1",
        model_provider="mock",
        model_name="mock",
        raw_output={"ok": True},
        parsed_output={"ok": True},
    )

    assert not cache.has(key)
    cache.set(key, response)
    assert cache.has(key)
    assert cache.get(key) == response
