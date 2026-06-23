"""Tests for EvalGrid run hygiene and real-provider safeguards."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from evalgrid.cli import clear_selected_files
from evalgrid.config import EvalGridConfig, load_config
from evalgrid.providers import MistralProvider, OpenAIProvider, ProviderError, get_provider
from receiptinject.model_clients import MISTRAL_MISSING_KEY_MESSAGE, ModelClientError
from scripts.evalgrid_summarize import render_summary, select_run_rows


def test_summary_filters_by_metadata_run_id() -> None:
    """Summaries should default to the run_id in metadata."""

    rows = [
        {"run_id": "old", "status": "failed", "error": "old error", "mitigation": "baseline"},
        {
            "run_id": "new",
            "status": "completed",
            "error": "",
            "mitigation": "combined_safety",
        },
    ]
    raw_rows = [{"run_id": "old", "cached": False}, {"run_id": "new", "cached": True}]
    filtered, filtered_raw, run_id, excluded = select_run_rows(
        rows=rows,
        raw_rows=raw_rows,
        metadata={"run_id": "new"},
        run_id=None,
        all_runs=False,
    )

    assert run_id == "new"
    assert excluded == 1
    assert [row["run_id"] for row in filtered] == ["new"]
    assert [row["run_id"] for row in filtered_raw] == ["new"]
    summary = render_summary(
        filtered,
        {"run_id": "new", "estimated_cost": 0.0},
        Path("results.csv"),
        filtered_raw,
        selected_run_id=run_id,
        excluded_rows=excluded,
    )
    assert "old error" not in summary
    assert "Excluded 1 rows from other runs" in summary


def test_fresh_clears_only_selected_files(tmp_path: Path) -> None:
    """Fresh mode should clear outputs without touching unrelated files or cache."""

    results = tmp_path / "results.csv"
    raw = tmp_path / "raw.jsonl"
    metadata = tmp_path / "metadata.json"
    cache = tmp_path / "cache.sqlite"
    unrelated = tmp_path / "keep.txt"
    for path in [results, raw, metadata, cache, unrelated]:
        path.write_text("x", encoding="utf-8")

    config = EvalGridConfig(
        output_results_path=str(results),
        raw_outputs_path=str(raw),
        metadata_path=str(metadata),
        cache_path=str(cache),
        fresh=True,
        clear_cache=False,
    )
    cleared = clear_selected_files(config)

    assert set(cleared) == {results, raw, metadata}
    assert not results.exists()
    assert not raw.exists()
    assert not metadata.exists()
    assert cache.exists()
    assert unrelated.exists()


def test_missing_mistral_key_fails_gracefully_without_secret(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing-key path should not print a secret value."""

    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_MODEL", raising=False)
    monkeypatch.setattr("evalgrid.providers.find_dotenv", lambda usecwd=True: "")
    monkeypatch.setattr("evalgrid.providers.MistralModelClient", _MissingKeyClient)
    provider = MistralProvider()
    captured = capsys.readouterr()
    assert "MISTRAL_API_KEY loaded: no" in captured.out

    request = _mistral_request()
    with pytest.raises(ProviderError) as exc_info:
        provider.complete(request, "task-1")
    assert "Missing MISTRAL_API_KEY" in str(exc_info.value)
    assert "test-secret" not in captured.out
    assert "test-secret" not in str(exc_info.value)


def test_mistral_config_is_conservative() -> None:
    """Real-provider config should be intentionally rate-limit conservative."""

    config = load_config("configs/evalgrid_receiptinject_mistral.yaml")
    assert config.provider == "mistral"
    assert config.limit == 5
    assert config.max_concurrency == 1
    assert config.sleep_between_requests >= 3.0
    assert config.max_attempts >= 5


def test_openai_evalgrid_config_exists_and_validates() -> None:
    """OpenAI EvalGrid config should be available for smoke runs."""

    config = load_config("configs/evalgrid_receiptinject_openai.yaml")
    assert config.provider == "openai"
    assert config.model_name == "gpt-4o-mini"
    assert config.dataset_path == "data/eval_subset_50.jsonl"
    assert config.max_concurrency == 1


def test_evalgrid_provider_factory_supports_openai() -> None:
    """Provider factory should route openai to the real OpenAI provider."""

    assert isinstance(get_provider("openai"), OpenAIProvider)


def test_openai_provider_missing_key_fails_gracefully(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """OpenAI provider should fail clearly without printing secrets."""

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("evalgrid.providers.find_dotenv", lambda usecwd=True: "")
    monkeypatch.setattr("evalgrid.providers.OpenAIModelClient", _MissingOpenAIKeyClient)
    provider = OpenAIProvider()
    captured = capsys.readouterr()
    assert "OPENAI_API_KEY loaded: no" in captured.out

    with pytest.raises(ProviderError) as exc_info:
        provider.complete(_openai_request(), "task-1")
    assert "Missing OPENAI_API_KEY" in str(exc_info.value)
    assert "test-secret" not in captured.out
    assert "test-secret" not in str(exc_info.value)


def test_summary_cli_inputs_can_read_run_scoped_rows(tmp_path: Path) -> None:
    """CSV shape should support run-scoped filtering."""

    results = tmp_path / "results.csv"
    with results.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["run_id", "status", "error"])
        writer.writeheader()
        writer.writerow({"run_id": "old", "status": "failed", "error": "old"})
        writer.writerow({"run_id": "new", "status": "completed", "error": ""})
    rows = list(csv.DictReader(results.open(encoding="utf-8")))
    metadata = json.loads('{"run_id": "new"}')

    filtered, _raw, _run_id, excluded = select_run_rows(
        rows=rows,
        raw_rows=[],
        metadata=metadata,
        run_id=None,
        all_runs=False,
    )

    assert len(filtered) == 1
    assert excluded == 1


def _mistral_request():
    from evalgrid.schemas import ModelRequest

    return ModelRequest(
        model_provider="mistral",
        model_name="mistral-large-latest",
        system_prompt="system",
        user_prompt="user",
    )


class _MissingKeyClient:
    """Fake Mistral client that raises the same missing-key error."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ModelClientError(MISTRAL_MISSING_KEY_MESSAGE)


class _MissingOpenAIKeyClient:
    """Fake OpenAI client that raises the same missing-key error."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        from receiptinject.model_clients import OPENAI_MISSING_KEY_MESSAGE

        raise ModelClientError(OPENAI_MISSING_KEY_MESSAGE)


def _openai_request():
    from evalgrid.schemas import ModelRequest

    return ModelRequest(
        model_provider="openai",
        model_name="gpt-4o-mini",
        system_prompt="system",
        user_prompt="user",
    )
