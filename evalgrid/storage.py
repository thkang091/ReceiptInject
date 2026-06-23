"""Storage helpers for EvalGrid artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from evalgrid.schemas import ModelResponse

RESULT_FIELDNAMES = [
    "run_id",
    "timestamp",
    "task_id",
    "benchmark_name",
    "dataset_path",
    "model_provider",
    "model_name",
    "mitigation",
    "input_mode",
    "status",
    "attempt_count",
    "input_tokens",
    "output_tokens",
    "latency_seconds",
    "cost_estimate",
    "cached",
    "error",
]


def ensure_csv_header(path: str | Path, extra_fields: list[str]) -> list[str]:
    """Ensure scored CSV has a header and return fieldnames."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [*RESULT_FIELDNAMES, *extra_fields]
    if output_path.exists() and output_path.stat().st_size > 0:
        with output_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            existing = next(reader)
        return existing
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
    return fieldnames


def append_csv_row(path: str | Path, fieldnames: list[str], row: dict[str, Any]) -> None:
    """Append one scored row."""

    with Path(path).open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writerow({field: row.get(field) for field in fieldnames})


def append_raw_jsonl(path: str | Path, record: dict[str, Any]) -> None:
    """Append one raw output record."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")


def load_completed_keys(
    path: str | Path,
    *,
    provider: str,
    model_name: str,
    mitigation: str,
) -> set[str]:
    """Load task IDs already completed for resume."""

    output_path = Path(path)
    if not output_path.exists():
        return set()
    completed: set[str] = set()
    with output_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if (
                row.get("model_provider") == provider
                and row.get("model_name") == model_name
                and row.get("mitigation") == mitigation
                and row.get("status") == "completed"
            ):
                completed.add(str(row.get("task_id")))
    return completed


def raw_record_from_response(run_id: str, response: ModelResponse) -> dict[str, Any]:
    """Build raw JSONL record from response."""

    return {
        "run_id": run_id,
        "task_id": response.task_id,
        "model_provider": response.model_provider,
        "model_name": response.model_name,
        "raw_output": response.raw_output,
        "parsed_output": response.parsed_output,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "latency_seconds": response.latency_seconds,
        "cost_estimate": response.cost_estimate,
        "error": response.error,
    }
