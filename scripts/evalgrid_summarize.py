"""Summarize EvalGrid CSV results."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

METRICS = [
    "extraction_accuracy",
    "prompt_injection_compliance",
    "privacy_leakage",
    "unsafe_action_rate",
    "hallucination",
    "over_refusal",
    "suspicious_instruction_detection",
    "safe_completion_rate",
    "utility_safety_tradeoff",
]


def parse_args() -> argparse.Namespace:
    """Parse arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/evalgrid_results.csv")
    parser.add_argument("--metadata", default="results/evalgrid_run_metadata.json")
    parser.add_argument("--raw", default="results/evalgrid_raw_outputs.jsonl")
    parser.add_argument("--out", default="results/evalgrid_summary.md")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--all-runs", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Write summary Markdown."""

    args = parse_args()
    rows = load_rows(Path(args.results))
    metadata = load_metadata(Path(args.metadata))
    raw_rows = load_jsonl(Path(args.raw))
    rows, raw_rows, selected_run_id, excluded_rows = select_run_rows(
        rows=rows,
        raw_rows=raw_rows,
        metadata=metadata,
        run_id=args.run_id,
        all_runs=args.all_runs,
    )
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_summary(
            rows,
            metadata,
            Path(args.results),
            raw_rows,
            selected_run_id=selected_run_id,
            excluded_rows=excluded_rows,
            all_runs=args.all_runs,
        ),
        encoding="utf-8",
    )
    if excluded_rows:
        print(
            f"Excluded {excluded_rows} rows from other runs. "
            "Use --all-runs to summarize everything."
        )
    print(f"EvalGrid summary written: {output_path}")


def load_rows(path: Path) -> list[dict[str, str]]:
    """Load CSV rows."""

    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_metadata(path: Path) -> dict:
    """Load metadata JSON if present."""

    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    """Load JSONL records if present."""

    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def select_run_rows(
    *,
    rows: list[dict[str, str]],
    raw_rows: list[dict],
    metadata: dict,
    run_id: str | None,
    all_runs: bool,
) -> tuple[list[dict[str, str]], list[dict], str | None, int]:
    """Filter rows to one run unless all-runs is requested."""

    if all_runs:
        return rows, raw_rows, None, 0
    selected_run_id = run_id or metadata.get("run_id")
    if not selected_run_id:
        return rows, raw_rows, None, 0
    filtered_rows = [row for row in rows if row.get("run_id") == selected_run_id]
    filtered_raw = [row for row in raw_rows if row.get("run_id") == selected_run_id]
    return filtered_rows, filtered_raw, selected_run_id, len(rows) - len(filtered_rows)


def render_summary(
    rows: list[dict[str, str]],
    metadata: dict,
    results_path: Path,
    raw_rows: list[dict],
    *,
    selected_run_id: str | None = None,
    excluded_rows: int = 0,
    all_runs: bool = False,
) -> str:
    """Render Markdown summary."""

    model_label = (
        f"{metadata.get('model_provider', 'unknown')}/"
        f"{metadata.get('model_name', 'unknown')}"
    )
    lines = [
        "# EvalGrid Summary",
        "",
        f"Results: `{results_path}`",
        f"Run ID: `{selected_run_id or metadata.get('run_id', 'all-runs')}`",
        f"Benchmark: `{metadata.get('benchmark_name', 'unknown')}`",
        f"Model: `{model_label}`",
        f"Total tasks: {metadata.get('total_tasks', 'unknown')}",
        f"Rows summarized: {len(rows)}",
        f"Completed rows: {sum(row.get('status') == 'completed' for row in rows)}",
        f"Failed rows: {sum(row.get('status') == 'failed' for row in rows)}",
        f"Completed tasks: {metadata.get('completed_tasks', 'unknown')}",
        f"Failed tasks: {metadata.get('failed_tasks', 'unknown')}",
        f"Skipped tasks: {metadata.get('skipped_tasks', 'unknown')}",
        f"Cache hits: {metadata.get('cache_hits', 'unknown')}",
        f"Estimated cost: ${float(metadata.get('estimated_cost', 0.0)):.6f}",
        f"Average latency: {average_latency(rows):.3f}s",
        f"Cache hit rate: {cache_hit_rate(rows, raw_rows)}",
        f"Old rows excluded: {excluded_rows if not all_runs else 0}",
        "",
    ]
    if excluded_rows and not all_runs:
        lines.extend(
            [
                (
                    f"Excluded {excluded_rows} rows from other runs. "
                    "Use `--all-runs` to summarize everything."
                ),
                "",
            ]
        )
    if not rows:
        lines.append("_No result rows._")
        return "\n".join(lines)

    lines.extend(
        [
            "## Metrics by Mitigation",
            "",
            metric_table(rows, ["mitigation"]),
            "",
            "## Metrics by Document Type",
            "",
            metric_table(rows, ["doc_type"]),
            "",
            "## Metrics by Attack Type",
            "",
            metric_table(rows, ["attack_type"]),
            "",
            "## Metrics by Model/Mitigation/Input Mode",
            "",
            metric_table(rows, ["model_name", "mitigation", "input_mode"]),
            "",
            "## Top Errors",
            "",
            top_errors(rows),
            "",
        ]
    )
    return "\n".join(lines)


def metric_table(rows: list[dict[str, str]], group_keys: list[str]) -> str:
    """Render grouped metric table."""

    groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        group_key = tuple(
            row.get(key, "text" if key == "input_mode" else "") for key in group_keys
        )
        groups[group_key].append(row)
    columns = [*group_keys, "n", *METRICS]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for group_key, group in sorted(groups.items()):
        values = [*group_key, str(len(group))]
        for metric in METRICS:
            numbers = [_to_float(row.get(metric)) for row in group]
            values.append(f"{sum(numbers) / len(numbers):.3f}" if numbers else "0.000")
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def average_latency(rows: list[dict[str, str]]) -> float:
    """Calculate average latency from result rows."""

    numbers = [_to_float(row.get("latency_seconds")) for row in rows]
    return sum(numbers) / len(numbers) if numbers else 0.0


def cache_hit_rate(rows: list[dict[str, str]], raw_rows: list[dict]) -> str:
    """Calculate cache hit rate when cached flags are available."""

    cached_values = [row.get("cached") for row in rows if row.get("cached") not in {None, ""}]
    if not cached_values:
        cached_values = [str(row.get("cached")) for row in raw_rows if "cached" in row]
    if not cached_values:
        return "not available"
    hits = sum(value.lower() == "true" for value in cached_values)
    return f"{hits / len(cached_values):.3f} ({hits}/{len(cached_values)})"


def top_errors(rows: list[dict[str, str]], limit: int = 5) -> str:
    """Render most common error messages."""

    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        error = (row.get("error") or "").strip()
        if error:
            counts[error] += 1
    if not counts:
        return "_No task-level errors recorded._"
    lines = [
        "| error | count |",
        "| --- | --- |",
    ]
    for error, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]:
        safe_error = error.replace("|", "\\|")
        lines.append(f"| {safe_error} | {count} |")
    return "\n".join(lines)


def _to_float(value: str | None) -> float:
    """Parse float cell."""

    try:
        return float(value or 0.0)
    except ValueError:
        return 0.0


if __name__ == "__main__":
    main()
