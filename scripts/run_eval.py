"""Run a ReceiptInject model evaluation experiment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receiptinject.eval_harness import (  # noqa: E402
    EvalHarnessConfig,
    run_experiment,
    summarize_results,
)
from receiptinject.model_clients import ModelClientError  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="YAML experiment config path.")
    parser.add_argument("--data", default=None, help="Dataset or OCR JSONL path.")
    parser.add_argument(
        "--model",
        default=None,
        choices=["mock", "mistral", "openai", "anthropic", "gemini"],
        help="Model client to use.",
    )
    parser.add_argument(
        "--mitigation",
        default=None,
        choices=[
            "baseline",
            "baseline_minimal",
            "baseline_schema",
            "untrusted_document",
            "action_confirmation",
            "structured_policy_guard",
            "privacy_minimization",
            "combined_safety",
            "combined_safety_schema",
        ],
        help="Prompt mitigation mode.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Maximum examples to run.")
    parser.add_argument("--sleep", type=float, default=None, help="Seconds to sleep per example.")
    parser.add_argument("--run-id", default=None, help="Explicit run identifier for output rows.")
    parser.add_argument(
        "--fresh",
        action="store_true",
        default=None,
        help="Remove selected output/raw/metadata files before running.",
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Skip completed result rows.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Scored CSV output path.",
    )
    parser.add_argument(
        "--raw-output",
        default=None,
        help="Raw model JSONL output path.",
    )
    parser.add_argument(
        "--input-mode",
        default=None,
        choices=["text", "ocr"],
        help="Whether input JSONL contains text examples or OCR outputs.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Run seed metadata.")
    return parser.parse_args()


def main() -> None:
    """Run evaluation from config and command-line arguments."""

    args = parse_args()
    config_values = _load_config(Path(args.config)) if args.config else {}
    merged = _merge_config_and_args(config_values, args)
    if merged["fresh"]:
        _remove_existing_outputs(
            Path(merged["output_path"]),
            Path(merged["raw_output_path"]),
            Path(merged["metadata_path"]),
        )
    config = EvalHarnessConfig(
        data_path=Path(merged["dataset_path"]),
        model_name=merged["model"],
        mitigation=merged["mitigation"],
        input_mode=merged["input_mode"],
        output_path=Path(merged["output_path"]),
        raw_output_path=Path(merged["raw_output_path"]),
        limit=merged["limit"],
        resume=merged["resume"],
        sleep_seconds=merged["sleep"],
        seed=merged["seed"],
        run_id=merged["run_id"],
        source_config=merged,
        metadata_path=Path(merged["metadata_path"]),
    )
    try:
        results = run_experiment(config)
    except ModelClientError as exc:
        raise SystemExit(str(exc)) from exc
    summary = summarize_results(results)
    print("Evaluation summary")
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"scored results: {config.output_path}")
    print(f"raw outputs: {config.raw_output_path}")
    print(f"run metadata: {config.metadata_path}")


def _load_config(path: Path) -> dict[str, Any]:
    """Load a YAML experiment config."""

    with path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Config must be a YAML mapping: {path}")
    return loaded


def _merge_config_and_args(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    """Merge config values with explicit CLI overrides."""

    merged = {
        "dataset_path": "data/examples_500.jsonl",
        "model": "mock",
        "mitigation": "baseline",
        "input_mode": "text",
        "limit": None,
        "sleep": 0.0,
        "output_path": "results/results.csv",
        "raw_output_path": "results/raw_outputs.jsonl",
        "metadata_path": "results/run_metadata.json",
        "resume": False,
        "seed": 0,
        "run_id": None,
        "fresh": False,
    }
    merged.update(config)

    cli_overrides = {
        "dataset_path": args.data,
        "model": args.model,
        "mitigation": args.mitigation,
        "input_mode": args.input_mode,
        "limit": args.limit,
        "sleep": args.sleep,
        "output_path": args.output,
        "raw_output_path": args.raw_output,
        "resume": args.resume,
        "seed": args.seed,
        "run_id": getattr(args, "run_id", None),
        "fresh": getattr(args, "fresh", None),
    }
    for key, value in cli_overrides.items():
        if value is not None:
            merged[key] = value

    _validate_config(merged)
    return merged


def _validate_config(config: dict[str, Any]) -> None:
    """Validate required experiment config keys."""

    required = {
        "dataset_path",
        "model",
        "mitigation",
        "input_mode",
        "output_path",
        "raw_output_path",
        "metadata_path",
        "resume",
        "seed",
        "fresh",
    }
    missing = sorted(key for key in required if key not in config)
    if missing:
        raise ValueError(f"Missing required config fields: {', '.join(missing)}")


def _remove_existing_outputs(*paths: Path) -> None:
    """Remove selected output artifacts for an explicit fresh run."""

    for path in paths:
        if path.exists():
            path.unlink()


if __name__ == "__main__":
    main()
