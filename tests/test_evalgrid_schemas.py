"""Tests for EvalGrid schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from evalgrid.schemas import (
    EvalJob,
    EvalRunMetadata,
    EvalTask,
    ModelRequest,
    ModelResponse,
)


def test_eval_task_requires_non_empty_core_fields() -> None:
    """EvalTask should validate required text fields."""

    task = EvalTask(
        task_id="t1",
        benchmark_name="receiptinject",
        input_text="document",
    )
    assert task.task_id == "t1"
    with pytest.raises(ValidationError):
        EvalTask(task_id="", benchmark_name="receiptinject", input_text="document")


def test_model_request_and_response_validate() -> None:
    """Request and response schemas should accept normalized payloads."""

    request = ModelRequest(
        model_provider="mock",
        model_name="mock",
        system_prompt="system",
        user_prompt="user",
        response_format={"type": "json_object"},
    )
    response = ModelResponse(
        task_id="t1",
        model_provider=request.model_provider,
        model_name=request.model_name,
        parsed_output={"ok": True},
    )
    assert response.parsed_output == {"ok": True}


def test_eval_job_and_metadata_validate() -> None:
    """Job and run metadata should validate basic run contracts."""

    task = EvalTask(task_id="t1", benchmark_name="receiptinject", input_text="document")
    request = ModelRequest(
        model_provider="mock",
        model_name="mock",
        system_prompt="system",
        user_prompt="user",
    )
    job = EvalJob(run_id="run", task=task, request=request)
    assert job.status == "pending"

    metadata = EvalRunMetadata(
        run_id="run",
        benchmark_name="receiptinject",
        dataset_path="data/examples.jsonl",
        model_provider="mock",
        model_name="mock",
        started_at=datetime.now(UTC),
        total_tasks=1,
    )
    assert metadata.total_tasks == 1
