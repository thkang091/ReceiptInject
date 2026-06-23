"""YAML configuration for EvalGrid."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class EvalGridConfig(BaseModel):
    """Configuration for one EvalGrid run."""

    benchmark_name: str = "receiptinject"
    dataset_path: str = "data/examples_50.jsonl"
    provider: str = "mock"
    model_name: str = "mock"
    mitigation: str = "combined_safety"
    limit: int | None = None
    max_concurrency: int = 1
    sleep_between_requests: float = 0.0
    max_attempts: int = 3
    use_cache: bool = True
    cache_path: str = "results/evalgrid_cache.sqlite"
    output_results_path: str = "results/evalgrid_results.csv"
    raw_outputs_path: str = "results/evalgrid_raw_outputs.jsonl"
    metadata_path: str = "results/evalgrid_run_metadata.json"
    cost_summary_path: str = "results/cost_summary.md"
    resume: bool = True
    run_id: str | None = None
    config_path: str | None = None
    fresh: bool = False
    clear_cache: bool = False


def load_config(path: str | Path) -> EvalGridConfig:
    """Load YAML config."""

    config_path = Path(path)
    with config_path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"EvalGrid config must be a YAML mapping: {config_path}")
    loaded["config_path"] = str(config_path)
    return EvalGridConfig.model_validate(loaded)


def apply_overrides(config: EvalGridConfig, overrides: dict[str, Any]) -> EvalGridConfig:
    """Apply non-None CLI overrides."""

    data = config.model_dump()
    for key, value in overrides.items():
        if value is not None:
            data[key] = value
    return EvalGridConfig.model_validate(data)
