"""Command-line helpers for EvalGrid."""

from __future__ import annotations

import argparse
from pathlib import Path

from evalgrid.config import EvalGridConfig, apply_overrides, load_config
from evalgrid.runner import EvalGridRunner


def parse_run_args() -> argparse.Namespace:
    """Parse evalgrid run CLI arguments."""

    parser = argparse.ArgumentParser(description="Run an EvalGrid experiment.")
    parser.add_argument("--config", required=True, help="YAML EvalGrid config path.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--mitigation", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--max-concurrency", type=int, default=None)
    parser.add_argument("--output-results-path", default=None)
    parser.add_argument("--raw-outputs-path", default=None)
    parser.add_argument("--metadata-path", default=None)
    parser.add_argument("--use-cache", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Clear configured run output files first.",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear configured cache file first.",
    )
    return parser.parse_args()


def run_from_args(args: argparse.Namespace) -> None:
    """Run EvalGrid from parsed args."""

    config = load_config(Path(args.config))
    config = apply_overrides(
        config,
        {
            "limit": args.limit,
            "provider": args.provider,
            "model_name": args.model_name,
            "mitigation": args.mitigation,
            "run_id": args.run_id,
            "max_concurrency": args.max_concurrency,
            "output_results_path": args.output_results_path,
            "raw_outputs_path": args.raw_outputs_path,
            "metadata_path": args.metadata_path,
            "use_cache": args.use_cache,
            "resume": args.resume,
            "fresh": True if args.fresh else None,
            "clear_cache": True if args.clear_cache else None,
        },
    )
    clear_selected_files(config)
    metadata = EvalGridRunner(config).run()
    print("EvalGrid run complete")
    print(f"run_id: {metadata.run_id}")
    print(f"completed_tasks: {metadata.completed_tasks}")
    print(f"failed_tasks: {metadata.failed_tasks}")
    print(f"estimated_cost: {metadata.estimated_cost:.6f}")


def default_config() -> EvalGridConfig:
    """Return default config for tests."""

    return EvalGridConfig()


def clear_selected_files(config: EvalGridConfig) -> list[Path]:
    """Clear only files explicitly selected by fresh/clear-cache options."""

    targets: list[Path] = []
    if config.fresh:
        targets.extend(
            [
                Path(config.output_results_path),
                Path(config.raw_outputs_path),
                Path(config.metadata_path),
            ]
        )
    if config.clear_cache:
        targets.append(Path(config.cache_path))

    cleared: list[Path] = []
    for target in targets:
        if target.exists():
            target.unlink()
            cleared.append(target)
            print(f"Cleared file: {target}")
        else:
            print(f"File not present, nothing to clear: {target}")
    return cleared
