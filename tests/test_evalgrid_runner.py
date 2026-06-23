"""Tests for EvalGrid runner."""

import csv
import json
from pathlib import Path

from evalgrid.config import EvalGridConfig
from evalgrid.providers import BaseProvider
from evalgrid.runner import EvalGridRunner, is_retryable_error, retry_delay_seconds
from evalgrid.schemas import ModelRequest, ModelResponse
from receiptinject.dataset_generator import generate_dataset, save_jsonl


def _config(tmp_path: Path, data_path: Path) -> EvalGridConfig:
    return EvalGridConfig(
        benchmark_name="receiptinject",
        dataset_path=str(data_path),
        provider="mock",
        model_name="mock",
        mitigation="combined_safety",
        limit=3,
        max_concurrency=2,
        sleep_between_requests=0.0,
        max_attempts=2,
        use_cache=True,
        cache_path=str(tmp_path / "cache.sqlite"),
        output_results_path=str(tmp_path / "evalgrid_results.csv"),
        raw_outputs_path=str(tmp_path / "evalgrid_raw.jsonl"),
        metadata_path=str(tmp_path / "metadata.json"),
        cost_summary_path=str(tmp_path / "cost.md"),
        resume=True,
        run_id="test-run",
    )


def test_evalgrid_runner_mock_mode_writes_artifacts(tmp_path: Path) -> None:
    """Mock EvalGrid run should write CSV, raw JSONL, metadata, and cost summary."""

    data_path = tmp_path / "examples.jsonl"
    save_jsonl(generate_dataset(n=5, seed=42), data_path)
    config = _config(tmp_path, data_path)

    metadata = EvalGridRunner(config).run()

    assert metadata.total_tasks == 3
    assert metadata.completed_tasks == 3
    rows = list(csv.DictReader(Path(config.output_results_path).open()))
    assert len(rows) == 3
    assert rows[0]["benchmark_name"] == "receiptinject"
    assert rows[0]["model_provider"] == "mock"
    raw_lines = Path(config.raw_outputs_path).read_text(encoding="utf-8").splitlines()
    assert len(raw_lines) == 3
    metadata_json = json.loads(Path(config.metadata_path).read_text(encoding="utf-8"))
    assert metadata_json["run_id"] == "test-run"
    assert Path(config.cost_summary_path).exists()


def test_evalgrid_runner_resume_skips_completed_rows(tmp_path: Path) -> None:
    """Resume should skip task/provider/model/mitigation rows already completed."""

    data_path = tmp_path / "examples.jsonl"
    save_jsonl(generate_dataset(n=5, seed=43), data_path)
    config = _config(tmp_path, data_path)

    first = EvalGridRunner(config).run()
    second = EvalGridRunner(config).run()

    assert first.completed_tasks == 3
    assert second.completed_tasks == 0
    rows = list(csv.DictReader(Path(config.output_results_path).open()))
    assert len(rows) == 3


def test_evalgrid_runner_cache_avoids_duplicate_provider_calls(tmp_path: Path) -> None:
    """A cached second run should not call the provider again when resume is disabled."""

    data_path = tmp_path / "examples.jsonl"
    save_jsonl(generate_dataset(n=5, seed=44), data_path)
    config = _config(tmp_path, data_path).model_copy(update={"limit": 1, "resume": False})
    provider = _CountingProvider()

    first = EvalGridRunner(config, provider=provider).run()
    second = EvalGridRunner(config, provider=provider).run()

    assert first.completed_tasks == 1
    assert second.completed_tasks == 1
    assert provider.calls == 1
    rows = list(csv.DictReader(Path(config.output_results_path).open()))
    assert rows[-1]["cached"] == "True"


def test_429_errors_are_retryable_with_conservative_delay() -> None:
    """Rate limit errors should use slower retry timing."""

    assert is_retryable_error("Status 429 Rate limit exceeded")
    assert retry_delay_seconds("Status 429 Rate limit exceeded", attempt=1) >= 5.0


class _CountingProvider(BaseProvider):
    """Provider that counts calls and returns valid mock-shaped output."""

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, request: ModelRequest, task_id: str) -> ModelResponse:
        """Return a successful response."""

        self.calls += 1
        return ModelResponse(
            task_id=task_id,
            model_provider=request.model_provider,
            model_name=request.model_name,
            raw_output=_valid_output(),
            parsed_output=_valid_output(),
        )


def _valid_output() -> dict[str, object]:
    """Return valid ReceiptInject model output."""

    return {
        "extracted_fields": {"summary": "ok"},
        "refused": False,
        "unsafe_action_recommended": False,
        "private_information_revealed": False,
        "followed_document_instruction": False,
        "suspicious_instruction_detected": True,
        "confidence": 0.9,
        "notes": "counting provider",
    }
