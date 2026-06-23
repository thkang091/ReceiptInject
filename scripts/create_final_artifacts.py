"""Create clean final ReceiptInject artifacts for application review."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receiptinject.analysis import METRIC_COLUMNS  # noqa: E402
from receiptinject.failure_cases import (  # noqa: E402
    FailureCase,
    build_failure_cases,
    embedded_instruction_summary,
    load_examples_by_id,
    load_raw_outputs_by_key,
    model_behavior_summary,
)

FAILURE_METRICS = [
    "prompt_injection_compliance",
    "privacy_leakage",
    "unsafe_action_rate",
    "hallucination",
    "over_refusal",
]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/results.csv", help="Scored CSV path.")
    parser.add_argument("--raw", default="results/raw_outputs.jsonl", help="Raw outputs JSONL.")
    parser.add_argument("--data", default="data/examples_500.jsonl", help="Dataset JSONL path.")
    parser.add_argument("--out", default="results/final", help="Final artifact directory.")
    parser.add_argument(
        "--ocr",
        default="data/ocr_outputs/ocr_results.jsonl",
        help="OCR results JSONL path for OCR pilot counts.",
    )
    parser.add_argument(
        "--manifest",
        default="data/rendered_docs/manifest.jsonl",
        help="Rendered-document manifest for copying examples.",
    )
    parser.add_argument(
        "--include-mock",
        action="store_true",
        help="Include mock rows. By default only real model rows are selected.",
    )
    return parser.parse_args()


def main() -> None:
    """Create final artifacts."""

    args = parse_args()
    outputs = create_final_artifacts(
        results_path=Path(args.results),
        raw_path=Path(args.raw),
        data_path=Path(args.data),
        out_dir=Path(args.out),
        ocr_path=Path(args.ocr),
        manifest_path=Path(args.manifest),
        include_mock=args.include_mock,
    )
    print("Final artifacts written:")
    for path in outputs:
        print(f"- {path}")


def create_final_artifacts(
    results_path: Path,
    raw_path: Path,
    data_path: Path,
    out_dir: Path,
    ocr_path: Path = Path("data/ocr_outputs/ocr_results.jsonl"),
    manifest_path: Path = Path("data/rendered_docs/manifest.jsonl"),
    include_mock: bool = False,
) -> list[Path]:
    """Create final CSV, Markdown reports, metadata, and validation files."""

    out_dir.mkdir(parents=True, exist_ok=True)
    all_rows = load_result_rows(results_path)
    selected_rows = select_final_rows(all_rows, data_path=data_path, include_mock=include_mock)
    raw_records = load_raw_outputs_by_key(raw_path)
    examples = load_examples_by_id(data_path) if data_path.exists() else {}
    failure_cases = build_failure_cases(selected_rows, examples, raw_records)
    ocr_stats = load_ocr_stats(ocr_path)
    copied_examples = copy_representative_rendered_examples(manifest_path, out_dir / "examples")

    paths = {
        "results": out_dir / "final_results.csv",
        "summary": out_dir / "final_summary.md",
        "failure_cases": out_dir / "final_failure_cases.md",
        "interpretation": out_dir / "final_interpretation.md",
        "metadata": out_dir / "final_run_metadata.json",
        "validation": out_dir / "final_validation.md",
    }

    write_results_csv(selected_rows, paths["results"], all_rows)
    paths["summary"].write_text(
        render_final_summary(selected_rows, results_path, data_path, ocr_stats),
        encoding="utf-8",
    )
    paths["failure_cases"].write_text(
        render_final_failure_cases(failure_cases, selected_rows),
        encoding="utf-8",
    )
    paths["interpretation"].write_text(
        render_final_interpretation(selected_rows),
        encoding="utf-8",
    )
    paths["metadata"].write_text(
        json.dumps(
            build_run_metadata(
                selected_rows,
                results_path,
                raw_path,
                data_path,
                ocr_stats,
                copied_examples,
            ),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    paths["validation"].write_text(
        render_final_validation(data_path),
        encoding="utf-8",
    )
    return list(paths.values())


def load_result_rows(path: Path) -> list[dict[str, Any]]:
    """Load scored rows from CSV."""

    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for metric in METRIC_COLUMNS:
            row[metric] = _safe_float(row.get(metric))
    return rows


def select_final_rows(
    rows: list[dict[str, Any]],
    data_path: Path,
    include_mock: bool = False,
) -> list[dict[str, Any]]:
    """Select real model rows for the requested dataset."""

    dataset_ids = set(load_examples_by_id(data_path)) if data_path.exists() else set()
    dataset_rows = [
        row
        for row in rows
        if _normalize_path(row.get("dataset_path", "")) == _normalize_path(data_path)
        or (row.get("input_mode") == "ocr" and str(row.get("id")) in dataset_ids)
    ]
    candidate_rows = dataset_rows or rows
    if not include_mock:
        candidate_rows = [row for row in candidate_rows if row.get("model_name") != "mock"]
    preferred_run_rows = [
        row
        for row in candidate_rows
        if str(row.get("run_id", "")).startswith(
            ("openai_test_", "openai_hard_", "mistral_text_", "mistral_ocr_")
        )
    ]
    return preferred_run_rows or candidate_rows


def write_results_csv(
    rows: list[dict[str, Any]],
    path: Path,
    all_rows: list[dict[str, Any]],
) -> None:
    """Write selected final result rows."""

    fieldnames = list(all_rows[0].keys()) if all_rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        if not fieldnames:
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_final_summary(
    rows: list[dict[str, Any]],
    results_path: Path,
    data_path: Path,
    ocr_stats: dict[str, Any],
) -> str:
    """Render final summary Markdown."""

    lines = [
        "# Preliminary Real-Model Results",
        "",
        f"Source results: `{results_path}`",
        f"Dataset path: `{data_path}`",
        "",
    ]
    if not rows:
        lines.extend(
            [
                "No real non-mock model results were found yet. Run a real-model "
                "evaluation command first.",
                "",
                "## OCR Pilot Results",
                "",
                render_ocr_section(rows, ocr_stats),
                "",
            ]
        )
        return "\n".join(lines)

    run_ids = sorted({str(row.get("run_id", "")) for row in rows if row.get("run_id")})
    models = sorted({str(row.get("model_name", "")) for row in rows if row.get("model_name")})
    lines.extend(
        [
            f"Model name(s): {', '.join(models)}",
            f"Run IDs included: {', '.join(run_ids)}",
            f"Number of evaluated examples: {len(rows)}",
            "",
            "These are preliminary real-model results on a synthetic benchmark. Automated "
            "scorers are useful for controlled comparison but have limitations; manual "
            "inspection is still needed before drawing strong conclusions.",
            "",
            "## Baseline vs Combined Safety",
            "",
            render_baseline_comparison(rows),
            "",
            "## Metric Table",
            "",
            render_metric_table(group_metric_rows(rows)),
            "",
            "## Cautious Interpretation",
            "",
            cautious_interpretation(rows),
            "",
            "## OCR Pilot Results",
            "",
            render_ocr_section(rows, ocr_stats),
            "",
        ]
    )
    return "\n".join(lines)


def render_final_failure_cases(
    cases: list[FailureCase],
    rows: list[dict[str, Any]],
) -> str:
    """Render 5-10 representative real-model failure cases."""

    lines = [
        "# Final Failure Cases",
        "",
        "All examples are synthetic. Embedded instructions are summarized rather than reproduced.",
        "",
    ]
    if not rows:
        lines.append("No real non-mock rows were available for failure-case export.")
        return "\n".join(lines)
    if not cases:
        lines.append("No scored failure cases were found in the selected real-model rows.")
        return "\n".join(lines)

    selected = select_representative_cases(cases, rows)
    for index, case in enumerate(selected, start=1):
        lines.extend(
            [
                f"## {index}. `{case.id}`",
                "",
                f"- Model: `{case.row.get('model_name', 'unknown')}`",
                f"- Mitigation: `{case.row.get('mitigation', 'unknown')}`",
                f"- Document type: `{case.row.get('doc_type', 'unknown')}`",
                f"- Attack type: `{case.row.get('attack_type', 'unknown')}`",
                f"- Difficulty: `{case.row.get('difficulty', 'unknown')}`",
                f"- Triggered metrics: {', '.join(case.triggered_metrics) or 'none'}",
                f"- Embedded instruction summary: {embedded_instruction_summary(case.example)}",
                f"- Model behavior summary: {model_behavior_summary(case)}",
                f"- Why it matters: {case_why_it_matters(case)}",
                "- Manual inspection note: This automated label should be manually reviewed "
                "against the synthetic document and raw model output before making claims.",
                "",
            ]
        )
    return "\n".join(lines)


def render_final_interpretation(rows: list[dict[str, Any]]) -> str:
    """Render cautious final interpretation."""

    lines = [
        "# Final Interpretation",
        "",
        "These preliminary results should be interpreted cautiously. ReceiptInject uses a "
        "synthetic benchmark, and its automated scorers are intentionally simple and "
        "auditable rather than a substitute for human review.",
        "",
    ]
    if not rows:
        lines.extend(
            [
                "No real non-mock results were found yet, so this artifact does not make "
                "empirical claims about model behavior.",
                "",
                "## OCR Pipeline Notes",
                "",
                "OCR quality may affect extraction accuracy. The OCR pilot is small-sample "
                "and does not represent production document reliability. Manual inspection "
                "is needed. The benchmark uses synthetic rendered documents only.",
            ]
        )
        return "\n".join(lines)

    comparison = metric_by_mitigation(rows)
    lines.extend(
        [
            "## What the Preliminary Results Suggest",
            "",
            cautious_interpretation(rows),
            "",
            "## Where Combined Safety Helped",
            "",
            compare_metric_text(comparison, lower_is_better=True),
            "",
            "## Where It Failed",
            "",
            "Any non-zero safety failure metric in `combined_safety` should be treated as "
            "a candidate failure for manual inspection, not as conclusive evidence by itself.",
            "",
            "## Scorer Limitations",
            "",
            "The scorers use transparent heuristics over structured model outputs. They can "
            "miss semantic nuance, depend on model self-report flags, and should be paired "
            "with manual review of raw outputs.",
            "",
            "## Synthetic Dataset Limitations",
            "",
            "The dataset avoids real private data and uses visible benchmark instructions. "
            "It does not cover hidden text, steganography, all OCR artifacts, or the full "
            "distribution of real institutional documents.",
            "",
            "## Why Manual Inspection Is Needed",
            "",
            "Manual inspection is needed to verify whether automated labels correspond to "
            "substantive failures, whether extracted fields are practically useful, and "
            "whether mitigation prompts cause unacceptable utility loss.",
            "",
            "## Future Work",
            "",
            "Future work should add human annotation, more OCR layouts, more model providers, "
            "cost/latency tracking, richer semantic scorers, and controlled tool-use simulations.",
            "",
            "## OCR Pipeline Notes",
            "",
            "OCR quality may affect extraction accuracy and safety metrics. The OCR pilot is "
            "small-sample and does not represent production document reliability. Manual "
            "inspection is needed to distinguish OCR degradation from model behavior. "
            "ReceiptInject uses synthetic rendered documents only; no real private documents "
            "should be used.",
            "",
        ]
    )
    return "\n".join(lines)


def render_final_validation(data_path: Path) -> str:
    """Run lightweight validation commands and render their statuses."""

    commands = [
        ["python", "scripts/validate_dataset.py", "--data", str(data_path)],
        ["pytest"],
        ["ruff", "check", "."],
    ]
    statuses = [(command, run_command_status(command)) for command in commands]
    lines = [
        "# Final Validation",
        "",
        "| Command | Status |",
        "| --- | --- |",
    ]
    for command, status in statuses:
        lines.append(f"| `{' '.join(command)}` | {status} |")
    lines.extend(
        [
            "",
            "Confirmation: No real private data used.",
            "",
        ]
    )
    return "\n".join(lines)


def build_run_metadata(
    rows: list[dict[str, Any]],
    results_path: Path,
    raw_path: Path,
    data_path: Path,
    ocr_stats: dict[str, Any],
    copied_examples: list[str],
) -> dict[str, Any]:
    """Build final run metadata."""

    return {
        "results_path": str(results_path),
        "raw_output_path": str(raw_path),
        "dataset_path": str(data_path),
        "rows": len(rows),
        "run_ids": sorted({str(row.get("run_id", "")) for row in rows if row.get("run_id")}),
        "models": sorted({str(row.get("model_name", "")) for row in rows if row.get("model_name")}),
        "mitigations": sorted(
            {str(row.get("mitigation", "")) for row in rows if row.get("mitigation")}
        ),
        "input_modes": sorted(
            {str(row.get("input_mode", "")) for row in rows if row.get("input_mode")}
        ),
        "synthetic_data_only": True,
        "mock_rows_included": any(row.get("model_name") == "mock" for row in rows),
        "ocr_stats": ocr_stats,
        "copied_rendered_examples": copied_examples,
    }


def group_metric_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate metrics by model, mitigation, and input mode."""

    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("model_name", "")),
            str(row.get("mitigation", "")),
            str(row.get("input_mode", "")),
        )
        groups[key].append(row)

    table: list[dict[str, Any]] = []
    for (model_name, mitigation, input_mode), group in sorted(groups.items()):
        aggregate = {
            "model_name": model_name,
            "mitigation": mitigation,
            "input_mode": input_mode,
            "n": len(group),
        }
        for metric in METRIC_COLUMNS:
            aggregate[metric] = sum(_safe_float(row.get(metric)) for row in group) / len(group)
        table.append(aggregate)
    return table


def render_metric_table(rows: list[dict[str, Any]]) -> str:
    """Render aggregate metric table."""

    if not rows:
        return "_No rows._"
    columns = ["model_name", "mitigation", "input_mode", "n", *METRIC_COLUMNS]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                value = f"{value:.3f}"
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def render_baseline_comparison(rows: list[dict[str, Any]]) -> str:
    """Render baseline vs combined_safety comparison."""

    grouped = metric_by_mitigation(rows)
    baseline_name, combined_name = _comparison_pair(grouped)
    if not baseline_name or not combined_name:
        return "_Both baseline and mitigation rows are needed for direct comparison._"

    lines = [
        f"| Metric | {baseline_name} | {combined_name} | Delta Mitigation-Baseline |",
        "| --- | ---: | ---: | ---: |",
    ]
    for metric in METRIC_COLUMNS:
        baseline = grouped[baseline_name].get(metric, 0.0)
        combined = grouped[combined_name].get(metric, 0.0)
        lines.append(
            f"| {metric} | {baseline:.3f} | {combined:.3f} | {combined - baseline:.3f} |"
        )
    return "\n".join(lines)


def render_ocr_section(rows: list[dict[str, Any]], ocr_stats: dict[str, Any]) -> str:
    """Render OCR pilot summary and text-vs-OCR comparison."""

    ocr_rows = [row for row in rows if row.get("input_mode") == "ocr"]
    lines = [
        f"OCR documents attempted: {ocr_stats['attempted']}",
        f"OCR failures: {ocr_stats['failures']}",
        f"OCR failure rate: {ocr_stats['failure_rate']:.3f}",
        "",
    ]
    if not ocr_rows:
        lines.append("No OCR evaluation rows were found in the selected real-model results.")
        return "\n".join(lines)

    run_ids = sorted({str(row.get("run_id", "")) for row in ocr_rows if row.get("run_id")})
    models = sorted({str(row.get("model_name", "")) for row in ocr_rows if row.get("model_name")})
    mitigations = sorted(
        {str(row.get("mitigation", "")) for row in ocr_rows if row.get("mitigation")}
    )
    lines.extend(
        [
            f"OCR examples evaluated: {len(ocr_rows)}",
            f"Run ID(s): {', '.join(run_ids)}",
            f"Model: {', '.join(models)}",
            f"Mitigation: {', '.join(mitigations)}",
            "Input mode: ocr",
            "",
            "### OCR Metric Table",
            "",
            render_metric_table(group_metric_rows(ocr_rows)),
            "",
            "### Text-vs-OCR Comparison",
            "",
            render_text_vs_ocr_comparison(rows),
            "",
            "OCR pilot results are preliminary and small-sample. OCR quality may affect "
            "extraction accuracy and safety metrics; manual inspection is needed.",
        ]
    )
    return "\n".join(lines)


def render_text_vs_ocr_comparison(rows: list[dict[str, Any]]) -> str:
    """Compare combined_safety text and OCR rows when both exist."""

    compare_rows = [
        row
        for row in rows
        if row.get("model_name") == "mistral"
        and row.get("mitigation") == "combined_safety"
        and row.get("input_mode") in {"text", "ocr"}
    ]
    by_mode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in compare_rows:
        by_mode[str(row.get("input_mode"))].append(row)
    if "text" not in by_mode or "ocr" not in by_mode:
        return "_Matching text-only and OCR combined_safety Mistral rows were not found._"

    lines = [
        "| Metric | Text Mean | OCR Mean | OCR-Text Delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for metric in METRIC_COLUMNS:
        text_mean = _metric_mean(by_mode["text"], metric)
        ocr_mean = _metric_mean(by_mode["ocr"], metric)
        lines.append(
            f"| {metric} | {text_mean:.3f} | {ocr_mean:.3f} | "
            f"{ocr_mean - text_mean:.3f} |"
        )
    lines.append("")
    lines.append("Latency/runtime fields were not available in the selected result rows.")
    return "\n".join(lines)


def metric_by_mitigation(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Return metric means keyed by mitigation."""

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("mitigation", ""))].append(row)
    output: dict[str, dict[str, float]] = {}
    for mitigation, group in groups.items():
        output[mitigation] = {
            metric: sum(_safe_float(row.get(metric)) for row in group) / len(group)
            for metric in METRIC_COLUMNS
        }
    return output


def load_ocr_stats(path: Path) -> dict[str, Any]:
    """Load OCR attempted/failure counts from OCR JSONL."""

    if not path.exists():
        return {"path": str(path), "attempted": 0, "failures": 0, "failure_rate": 0.0}
    attempted = 0
    failures = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            attempted += 1
            record = json.loads(line)
            if record.get("ocr_error"):
                failures += 1
    return {
        "path": str(path),
        "attempted": attempted,
        "failures": failures,
        "failure_rate": failures / attempted if attempted else 0.0,
    }


def copy_representative_rendered_examples(manifest_path: Path, out_dir: Path) -> list[str]:
    """Copy 2-3 representative rendered PDFs into final examples directory."""

    if not manifest_path.exists():
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    with manifest_path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    selected: list[dict[str, Any]] = []
    selectors = [
        lambda row: row.get("attack_type") == "none"
        and row.get("doc_type") in {"receipt", "invoice"},
        lambda row: row.get("attack_type") != "none",
        lambda row: row.get("doc_type") in {"policy_document", "mixed_bundle"},
    ]
    for selector in selectors:
        match = next((row for row in records if selector(row) and row not in selected), None)
        if match:
            selected.append(match)

    copied: list[str] = []
    for row in selected[:3]:
        source = Path(str(row.get("pdf_path") or row.get("image_path") or ""))
        if not source.exists():
            continue
        target = out_dir / f"{row.get('id')}_{row.get('doc_type')}{source.suffix}"
        shutil.copy2(source, target)
        copied.append(str(target))
    return copied


def cautious_interpretation(rows: list[dict[str, Any]]) -> str:
    """Return cautious natural-language interpretation."""

    grouped = metric_by_mitigation(rows)
    baseline_name, combined_name = _comparison_pair(grouped)
    if baseline_name and combined_name:
        safe_delta = grouped[combined_name]["safe_completion_rate"] - grouped[baseline_name][
            "safe_completion_rate"
        ]
        injection_delta = grouped[combined_name]["prompt_injection_compliance"] - grouped[
            baseline_name
        ]["prompt_injection_compliance"]
        return (
            f"In this preliminary run, compare `{combined_name}` against `{baseline_name}` as "
            f"a controlled prompt-mitigation contrast. Safe completion changed by "
            f"{safe_delta:.3f}; prompt-injection compliance changed by "
            f"{injection_delta:.3f}. These numbers are preliminary and require manual "
            "inspection of raw outputs."
        )
    return (
        "The selected real-model rows provide preliminary evidence for the listed "
        "configuration, but a baseline-vs-combined comparison requires both mitigations."
    )


def compare_metric_text(
    grouped: dict[str, dict[str, float]],
    lower_is_better: bool,
) -> str:
    """Describe where combined_safety moved safety metrics."""

    baseline_name, combined_name = _comparison_pair(grouped)
    if not baseline_name or not combined_name:
        return "Direct comparison is unavailable because one mitigation is missing."
    better: list[str] = []
    for metric in FAILURE_METRICS:
        delta = grouped[combined_name][metric] - grouped[baseline_name][metric]
        if (lower_is_better and delta < 0) or (not lower_is_better and delta > 0):
            better.append(f"`{metric}` ({delta:.3f})")
    if not better:
        return "No automated safety metric improved in the selected rows."
    return f"`{combined_name}` improved these automated failure metrics: " + ", ".join(better) + "."


def _comparison_pair(
    grouped: dict[str, dict[str, float]],
) -> tuple[str | None, str | None]:
    """Choose a baseline/mitigation pair available in rows."""

    pairs = [
        ("baseline_minimal", "combined_safety_schema"),
        ("baseline", "combined_safety"),
        ("baseline_schema", "combined_safety_schema"),
    ]
    for baseline_name, combined_name in pairs:
        if baseline_name in grouped and combined_name in grouped:
            return baseline_name, combined_name
    return None, None


def select_representative_cases(
    cases: list[FailureCase],
    rows: list[dict[str, Any]],
) -> list[FailureCase]:
    """Select 5-10 representative cases prioritized by failure type and comparisons."""

    selected: list[FailureCase] = []
    case_by_key = {(case.id, str(case.row.get("mitigation", ""))): case for case in cases}
    baseline_rows = {row["id"]: row for row in rows if row.get("mitigation") == "baseline"}
    combined_rows = {
        row["id"]: row for row in rows if row.get("mitigation") == "combined_safety"
    }

    improved_ids = [
        example_id
        for example_id, baseline in baseline_rows.items()
        if _failure_score(baseline) > 0
        and example_id in combined_rows
        and _failure_score(combined_rows[example_id]) == 0
    ]
    still_failed_ids = [
        example_id
        for example_id, combined in combined_rows.items()
        if _failure_score(combined) > 0
    ]
    for example_id in improved_ids[:3]:
        case = case_by_key.get((example_id, "baseline"))
        if case:
            selected.append(case)
    for example_id in still_failed_ids[:3]:
        case = case_by_key.get((example_id, "combined_safety"))
        if case:
            selected.append(case)

    for metric in FAILURE_METRICS:
        for case in sorted(cases, key=lambda item: (-item.severity, item.id)):
            if metric in case.triggered_metrics and case not in selected:
                selected.append(case)
                break

    for case in sorted(cases, key=lambda item: (-item.severity, item.id)):
        if len(selected) >= 10:
            break
        if case not in selected:
            selected.append(case)
    return selected[:10]


def case_why_it_matters(case: FailureCase) -> str:
    """Return a short explanation for a failure case."""

    metrics = set(case.triggered_metrics)
    if "prompt_injection_compliance" in metrics:
        return "The model appears to have treated untrusted document text as instruction."
    if "privacy_leakage" in metrics:
        return "The model appears to have revealed synthetic private fields unnecessarily."
    if "unsafe_action_rate" in metrics:
        return "The model moved from understanding a document toward external action."
    if "hallucination" in metrics:
        return "The output may include important unsupported values."
    if "over_refusal" in metrics:
        return "The model refused a task that should have been safely completable."
    return "The example triggered an automated failure metric and needs inspection."


def run_command_status(command: list[str]) -> str:
    """Run a validation command and return PASS/FAIL without dumping logs."""

    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return "FAIL (command not found)"
    if completed.returncode == 0:
        return "PASS"
    tail = (completed.stderr or completed.stdout).strip().splitlines()[-1:]
    detail = f": {tail[0]}" if tail else ""
    return f"FAIL{detail}"


def _failure_score(row: dict[str, Any]) -> float:
    """Return sum of failure metric values."""

    return sum(_safe_float(row.get(metric)) for metric in FAILURE_METRICS)


def _metric_mean(rows: list[dict[str, Any]], metric: str) -> float:
    """Return a metric mean for rows."""

    if not rows:
        return 0.0
    return sum(_safe_float(row.get(metric)) for row in rows) / len(rows)


def _safe_float(value: Any) -> float:
    """Coerce a metric cell to float."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_path(path: str | Path | Any) -> str:
    """Normalize relative path text for comparisons."""

    return Path(str(path)).as_posix().lstrip("./")


if __name__ == "__main__":
    main()
