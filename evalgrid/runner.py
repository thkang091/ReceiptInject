"""EvalGrid concurrent, resumable evaluation runner."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evalgrid.benchmark import get_benchmark_plugin
from evalgrid.cache import SQLiteResponseCache, make_cache_key
from evalgrid.config import EvalGridConfig
from evalgrid.cost_tracker import CostTracker
from evalgrid.providers import BaseProvider, ProviderError, get_provider
from evalgrid.rate_limit import AsyncRateLimiter
from evalgrid.schemas import EvalJob, EvalJobStatus, EvalRunMetadata, ModelResponse
from evalgrid.storage import (
    append_csv_row,
    append_raw_jsonl,
    ensure_csv_header,
    load_completed_keys,
    raw_record_from_response,
)


class EvalGridRunner:
    """Run an EvalGrid benchmark experiment."""

    def __init__(
        self,
        config: EvalGridConfig,
        *,
        provider: BaseProvider | None = None,
    ) -> None:
        self.config = config
        self.plugin = get_benchmark_plugin(config.benchmark_name)
        self.provider = provider or get_provider(config.provider)
        self.cache = SQLiteResponseCache(config.cache_path) if config.use_cache else None
        self.cost_tracker = CostTracker()
        self.run_id = config.run_id or self._default_run_id()

    def run(self) -> EvalRunMetadata:
        """Run synchronously by driving async worker pool."""

        return asyncio.run(self.run_async())

    async def run_async(self) -> EvalRunMetadata:
        """Run benchmark jobs concurrently with retry and recovery."""

        started_at = datetime.now(UTC)
        tasks = self.plugin.load_tasks(self.config.dataset_path, self.config.limit)
        completed_keys = (
            load_completed_keys(
                self.config.output_results_path,
                provider=self.config.provider,
                model_name=self.config.model_name,
                mitigation=self.config.mitigation,
            )
            if self.config.resume
            else set()
        )
        jobs = [
            EvalJob(
                run_id=self.run_id,
                task=task,
                request=self.plugin.build_request(
                    task,
                    self.config.provider,
                    self.config.model_name,
                    self.config.mitigation,
                ),
                status=(
                    EvalJobStatus.SKIPPED
                    if task.task_id in completed_keys
                    else EvalJobStatus.PENDING
                ),
                max_attempts=self.config.max_attempts,
            )
            for task in tasks
        ]

        fieldnames = ensure_csv_header(
            self.config.output_results_path,
            extra_fields=self._extra_score_fields(),
        )
        limiter = AsyncRateLimiter(
            max_concurrency=self.config.max_concurrency,
            sleep_between_requests=self.config.sleep_between_requests,
        )

        runnable = [job for job in jobs if job.status != EvalJobStatus.SKIPPED]
        results = await asyncio.gather(
            *(self._run_job(job, limiter, fieldnames) for job in runnable),
        )
        completed = sum(result.status == EvalJobStatus.COMPLETED for result in results)
        failed = sum(result.status == EvalJobStatus.FAILED for result in results)
        skipped = sum(job.status == EvalJobStatus.SKIPPED for job in jobs)
        cache_hits = sum(
            result.status == EvalJobStatus.COMPLETED and result.attempt_count == 0
            for result in results
        )
        metadata = EvalRunMetadata(
            run_id=self.run_id,
            benchmark_name=self.config.benchmark_name,
            dataset_path=self.config.dataset_path,
            model_provider=self.config.provider,
            model_name=self.config.model_name,
            config_path=self.config.config_path,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            total_tasks=len(tasks),
            completed_tasks=completed,
            failed_tasks=failed,
            skipped_tasks=skipped,
            cache_hits=cache_hits,
            estimated_cost=self.cost_tracker.estimated_cost,
        )
        self._write_metadata(metadata)
        self.cost_tracker.save_summary(self.config.cost_summary_path)
        return metadata

    async def _run_job(
        self,
        job: EvalJob,
        limiter: AsyncRateLimiter,
        fieldnames: list[str],
    ) -> EvalJob:
        """Run one job with cache, retry, and failure capture."""

        job = job.model_copy(update={"status": EvalJobStatus.RUNNING})
        cache_key = make_cache_key(job.request)
        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                response = cached.model_copy(update={"task_id": job.task.task_id})
                return self._persist_job_result(
                    job.model_copy(update={"status": EvalJobStatus.COMPLETED}),
                    response,
                    fieldnames,
                    cached=True,
                )

        last_error: str | None = None
        for attempt in range(1, job.max_attempts + 1):
            job = job.model_copy(update={"attempt_count": attempt})
            try:
                async with limiter:
                    response = await asyncio.to_thread(
                        self.provider.complete,
                        job.request,
                        job.task.task_id,
                    )
                if response.error:
                    raise ProviderError(response.error)
                response = self.cost_tracker.record(job.request, response)
                if self.cache is not None:
                    self.cache.set(cache_key, response)
                return self._persist_job_result(
                    job.model_copy(update={"status": EvalJobStatus.COMPLETED}),
                    response,
                    fieldnames,
                )
            except Exception as exc:  # noqa: BLE001 - per-task failure recovery.
                last_error = str(exc)
                if attempt < job.max_attempts and is_retryable_error(last_error):
                    await asyncio.sleep(retry_delay_seconds(last_error, attempt))
                else:
                    break

        failed_response = ModelResponse(
            task_id=job.task.task_id,
            model_provider=job.request.model_provider,
            model_name=job.request.model_name,
            raw_output=None,
            parsed_output=None,
            error=last_error or "unknown provider error",
        )
        return self._persist_job_result(
            job.model_copy(update={"status": EvalJobStatus.FAILED}),
            failed_response,
            fieldnames,
        )

    def _persist_job_result(
        self,
        job: EvalJob,
        response: ModelResponse,
        fieldnames: list[str],
        cached: bool = False,
    ) -> EvalJob:
        """Write raw/scored outputs for one job."""

        score = self.plugin.score_response(job.task, response)
        row: dict[str, Any] = {
            "run_id": self.run_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "task_id": job.task.task_id,
            "benchmark_name": job.task.benchmark_name,
            "dataset_path": self.config.dataset_path,
            "model_provider": job.request.model_provider,
            "model_name": job.request.model_name,
            "mitigation": self.config.mitigation,
            "input_mode": "text",
            "status": job.status.value,
            "attempt_count": job.attempt_count,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "latency_seconds": response.latency_seconds,
            "cost_estimate": response.cost_estimate,
            "cached": cached,
            "error": response.error,
            **score,
        }
        append_csv_row(self.config.output_results_path, fieldnames, row)
        raw = raw_record_from_response(self.run_id, response)
        raw["cached"] = cached
        raw["mitigation"] = self.config.mitigation
        append_raw_jsonl(self.config.raw_outputs_path, raw)
        return job

    def _extra_score_fields(self) -> list[str]:
        """Return known ReceiptInject-compatible score fields."""

        return [
            "id",
            "doc_type",
            "attack_type",
            "difficulty",
            "extraction_accuracy",
            "prompt_injection_compliance",
            "privacy_leakage",
            "unsafe_action_rate",
            "hallucination",
            "over_refusal",
            "suspicious_instruction_detection",
            "safe_completion_rate",
            "utility_safety_tradeoff",
            "refused",
            "unsafe_action_recommended",
            "private_information_revealed",
            "followed_document_instruction",
            "suspicious_instruction_detected",
            "notes",
        ]

    def _write_metadata(self, metadata: EvalRunMetadata) -> None:
        """Write run metadata JSON."""

        path = Path(self.config.metadata_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(metadata.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _default_run_id(self) -> str:
        """Create a deterministic-ish run ID from config and timestamp."""

        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return (
            f"evalgrid-{self.config.benchmark_name}-{self.config.provider}-"
            f"{self.config.mitigation}-{timestamp}"
        )


def is_retryable_error(error: str | None) -> bool:
    """Classify provider errors that are worth retrying."""

    if not error:
        return False
    lowered = error.lower()
    non_retryable = [
        "missing mistral_api_key",
        "api key",
        "authentication",
        "unauthorized",
        "forbidden",
    ]
    if any(marker in lowered for marker in non_retryable):
        return False
    retryable = [
        "429",
        "rate limit",
        "timeout",
        "temporarily",
        "connection",
        "api error",
        "invalid json",
        "failed to return valid json",
        "service unavailable",
        "status 500",
        "status 502",
        "status 503",
        "status 504",
    ]
    return any(marker in lowered for marker in retryable)


def retry_delay_seconds(error: str | None, attempt: int) -> float:
    """Return retry delay with conservative 429 handling."""

    retry_after = _retry_after_seconds(error)
    if retry_after is not None:
        return retry_after
    lowered = (error or "").lower()
    if "429" in lowered or "rate limit" in lowered:
        return 5.0 * (2 ** max(attempt - 1, 0))
    return float(2 ** max(attempt - 1, 0))


def _retry_after_seconds(error: str | None) -> float | None:
    """Extract Retry-After seconds from common error string shapes."""

    if not error:
        return None
    lowered = error.lower()
    marker = "retry-after"
    if marker not in lowered:
        return None
    tail = lowered.split(marker, maxsplit=1)[1]
    for token in tail.replace(":", " ").replace("=", " ").split():
        try:
            return max(float(token), 0.0)
        except ValueError:
            continue
    return None
