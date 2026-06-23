"""Pydantic schemas for EvalGrid runs."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EvalJobStatus(StrEnum):
    """Lifecycle states for one evaluation job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EvalTask(BaseModel):
    """One benchmark task loaded by a plugin."""

    task_id: str
    benchmark_name: str
    input_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    expected_output: dict[str, Any] = Field(default_factory=dict)
    scoring_context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("task_id", "benchmark_name", "input_text")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        """Require core text fields to be non-empty."""

        if not value or not value.strip():
            raise ValueError("field must be non-empty")
        return value


class ModelRequest(BaseModel):
    """Provider request generated from a benchmark task."""

    model_provider: str
    model_name: str
    system_prompt: str
    user_prompt: str
    temperature: float = 0.0
    response_format: dict[str, Any] | None = None

    @field_validator("model_provider", "model_name", "system_prompt", "user_prompt")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        """Require request identity and prompt text."""

        if not value or not value.strip():
            raise ValueError("field must be non-empty")
        return value


class ModelResponse(BaseModel):
    """Normalized provider response."""

    task_id: str
    model_provider: str
    model_name: str
    raw_output: Any = None
    parsed_output: dict[str, Any] | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_seconds: float = 0.0
    cost_estimate: float = 0.0
    error: str | None = None


class EvalJob(BaseModel):
    """One runnable task/request pair."""

    run_id: str
    task: EvalTask
    request: ModelRequest
    status: EvalJobStatus = EvalJobStatus.PENDING
    attempt_count: int = 0
    max_attempts: int = 3

    @field_validator("run_id")
    @classmethod
    def require_run_id(cls, value: str) -> str:
        """Require non-empty run IDs."""

        if not value or not value.strip():
            raise ValueError("run_id must be non-empty")
        return value


class EvalRunMetadata(BaseModel):
    """Metadata for a complete EvalGrid run."""

    run_id: str
    benchmark_name: str
    dataset_path: str
    model_provider: str
    model_name: str
    config_path: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    total_tasks: int
    completed_tasks: int = 0
    failed_tasks: int = 0
    skipped_tasks: int = 0
    cache_hits: int = 0
    estimated_cost: float = 0.0
