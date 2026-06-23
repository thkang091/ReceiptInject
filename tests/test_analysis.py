"""Tests for result analysis and summaries."""

from pathlib import Path

import pandas as pd

from receiptinject.analysis import (
    aggregate_metrics,
    bootstrap_mean_ci,
    generate_summary,
    load_results_csv,
    overall_terminal_summary,
)


def _write_results_csv(path: Path) -> None:
    """Write a tiny scored-results CSV fixture."""

    rows = [
        {
            "run_id": "r1",
            "timestamp": "2026-01-01T00:00:00Z",
            "dataset_path": "data/examples.jsonl",
            "id": "a",
            "doc_type": "receipt",
            "attack_type": "none",
            "difficulty": "easy",
            "model_name": "mock",
            "mitigation": "baseline",
            "input_mode": "text",
            "extraction_accuracy": 1.0,
            "prompt_injection_compliance": 0.0,
            "privacy_leakage": 0.0,
            "unsafe_action_rate": 0.0,
            "hallucination": 0.0,
            "over_refusal": 0.0,
            "suspicious_instruction_detection": 1.0,
            "safe_completion_rate": 1.0,
            "utility_safety_tradeoff": 1.0,
        },
        {
            "run_id": "r1",
            "timestamp": "2026-01-01T00:00:01Z",
            "dataset_path": "data/examples.jsonl",
            "id": "b",
            "doc_type": "invoice",
            "attack_type": "instruction_override",
            "difficulty": "hard",
            "model_name": "mock",
            "mitigation": "baseline",
            "input_mode": "ocr",
            "extraction_accuracy": 0.0,
            "prompt_injection_compliance": 1.0,
            "privacy_leakage": 0.0,
            "unsafe_action_rate": 0.0,
            "hallucination": 1.0,
            "over_refusal": 0.0,
            "suspicious_instruction_detection": 0.0,
            "safe_completion_rate": 0.0,
            "utility_safety_tradeoff": 0.0,
        },
    ]
    pd.DataFrame(rows).to_csv(path, index=False)


def test_bootstrap_mean_ci_is_deterministic() -> None:
    """Bootstrap confidence intervals should be deterministic for a seed."""

    first = bootstrap_mean_ci([0.0, 1.0, 1.0], samples=100, seed=3)
    second = bootstrap_mean_ci([0.0, 1.0, 1.0], samples=100, seed=3)
    assert first == second
    assert 0.0 <= first[0] <= first[1] <= 1.0


def test_aggregate_metrics_groups_rows(tmp_path: Path) -> None:
    """Aggregate tables should include counts and means."""

    path = tmp_path / "results.csv"
    _write_results_csv(path)
    df = load_results_csv(path)
    table = aggregate_metrics(df, ["model_name", "mitigation"], bootstrap_samples=50)
    assert len(table) == 1
    assert table.loc[0, "n"] == 2
    assert table.loc[0, "extraction_accuracy"] == 0.5


def test_generate_summary_writes_markdown_and_csv_tables(tmp_path: Path) -> None:
    """Summary generation should write Markdown and aggregate CSV artifacts."""

    results_path = tmp_path / "results.csv"
    out_path = tmp_path / "summary.md"
    _write_results_csv(results_path)
    outputs = generate_summary(results_path, out_path, bootstrap_samples=50)

    assert outputs.markdown_path.exists()
    markdown = out_path.read_text(encoding="utf-8")
    assert "ReceiptInject Results Summary" in markdown
    assert "Metrics by Difficulty" in markdown
    assert "Metrics by Attack Type" in markdown
    assert (tmp_path / "overall_by_model_mitigation.csv").exists()
    assert (tmp_path / "text_vs_ocr.csv").exists()


def test_overall_terminal_summary_uses_actual_rows(tmp_path: Path) -> None:
    """Terminal summary should reflect actual CSV rows."""

    results_path = tmp_path / "results.csv"
    _write_results_csv(results_path)
    summary = overall_terminal_summary(load_results_csv(results_path))
    assert summary["rows"] == 2.0
    assert summary["extraction_accuracy"] == 0.5
