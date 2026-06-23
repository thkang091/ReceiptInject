"""Aggregate analysis and reporting helpers for ReceiptInject results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from receiptinject.schemas import EvalResult

METRIC_COLUMNS = [
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

CI_METRICS = [
    "extraction_accuracy",
    "prompt_injection_compliance",
    "privacy_leakage",
    "unsafe_action_rate",
    "safe_completion_rate",
]

GROUPINGS = {
    "overall_by_model_mitigation": ["model_name", "mitigation"],
    "by_document_type": ["doc_type"],
    "by_attack_type": ["attack_type"],
    "by_difficulty": ["difficulty"],
    "text_vs_ocr": ["input_mode"],
    "safety_utility_tradeoff": ["model_name", "mitigation", "input_mode"],
}


@dataclass(frozen=True)
class AnalysisOutputs:
    """Paths and tables produced by result summarization."""

    markdown_path: Path
    aggregate_paths: dict[str, Path]
    tables: dict[str, pd.DataFrame]


def load_results_csv(path: str | Path) -> pd.DataFrame:
    """Load scored result rows from CSV without inventing missing data."""

    results_path = Path(path)
    if not results_path.exists():
        raise FileNotFoundError(f"Results CSV does not exist: {results_path}")
    df = pd.read_csv(results_path)
    if df.empty:
        raise ValueError(f"Results CSV has no rows: {results_path}")
    missing = [column for column in METRIC_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Results CSV is missing metric columns: {', '.join(missing)}")
    for column in METRIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def aggregate_metrics(
    df: pd.DataFrame,
    group_cols: list[str],
    bootstrap_samples: int = 1000,
    seed: int = 0,
) -> pd.DataFrame:
    """Aggregate metric means and bootstrap confidence intervals by group."""

    for column in group_cols:
        if column not in df.columns:
            raise ValueError(f"Cannot group by missing column `{column}`")

    rows: list[dict[str, Any]] = []
    grouped = df.groupby(group_cols, dropna=False, sort=True)
    for group_key, group in grouped:
        row = _group_key_to_row(group_cols, group_key)
        row["n"] = int(len(group))
        for metric in METRIC_COLUMNS:
            row[metric] = float(group[metric].mean())
        for metric in CI_METRICS:
            low, high = bootstrap_mean_ci(
                group[metric].dropna().tolist(),
                samples=bootstrap_samples,
                seed=seed + len(rows) * 997 + len(metric),
            )
            row[f"{metric}_ci_low"] = low
            row[f"{metric}_ci_high"] = high
        rows.append(row)
    return pd.DataFrame(rows)


def bootstrap_mean_ci(
    values: list[float],
    samples: int = 1000,
    seed: int = 0,
) -> tuple[float, float]:
    """Return a deterministic bootstrap 95% confidence interval for the mean."""

    clean_values = [float(value) for value in values if pd.notna(value)]
    if not clean_values:
        return (0.0, 0.0)
    if len(clean_values) == 1 or samples <= 0:
        mean = clean_values[0] if len(clean_values) == 1 else sum(clean_values) / len(clean_values)
        return (float(mean), float(mean))

    import random

    rng = random.Random(seed)
    means: list[float] = []
    n = len(clean_values)
    for _ in range(samples):
        sample = [clean_values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    low_index = int(0.025 * (samples - 1))
    high_index = int(0.975 * (samples - 1))
    return (float(means[low_index]), float(means[high_index]))


def generate_summary(
    results_path: str | Path,
    out_path: str | Path,
    bootstrap_samples: int = 1000,
    seed: int = 0,
) -> AnalysisOutputs:
    """Generate Markdown and CSV aggregate tables from scored result rows."""

    df = load_results_csv(results_path)
    markdown_path = Path(out_path)
    output_dir = markdown_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    tables: dict[str, pd.DataFrame] = {}
    aggregate_paths: dict[str, Path] = {}
    for name, group_cols in GROUPINGS.items():
        if name == "text_vs_ocr" and df["input_mode"].nunique(dropna=False) < 2:
            table = aggregate_metrics(df, group_cols, bootstrap_samples, seed)
        else:
            table = aggregate_metrics(df, group_cols, bootstrap_samples, seed)
        tables[name] = table
        path = output_dir / f"{name}.csv"
        table.to_csv(path, index=False)
        aggregate_paths[name] = path

    markdown_path.write_text(
        render_markdown_summary(
            df=df,
            tables=tables,
            results_path=Path(results_path),
            bootstrap_samples=bootstrap_samples,
        ),
        encoding="utf-8",
    )
    return AnalysisOutputs(
        markdown_path=markdown_path,
        aggregate_paths=aggregate_paths,
        tables=tables,
    )


def render_markdown_summary(
    df: pd.DataFrame,
    tables: dict[str, pd.DataFrame],
    results_path: Path,
    bootstrap_samples: int,
) -> str:
    """Render a Markdown summary report."""

    lines = [
        "# ReceiptInject Results Summary",
        "",
        f"Source results: `{results_path}`",
        f"Rows summarized: {len(df)}",
        f"Bootstrap resamples: {bootstrap_samples}",
        "",
        "This report summarizes actual scored CSV rows only. It does not invent results.",
        "High scores on synthetic easy/medium examples do not prove production safety.",
        "",
    ]
    sections = [
        ("Overall Metrics by Model and Mitigation", "overall_by_model_mitigation"),
        ("Metrics by Document Type", "by_document_type"),
        ("Metrics by Attack Type", "by_attack_type"),
        ("Metrics by Difficulty", "by_difficulty"),
        ("Text vs OCR Comparison", "text_vs_ocr"),
        ("Safety/Utility Tradeoff", "safety_utility_tradeoff"),
    ]
    for title, key in sections:
        lines.extend([f"## {title}", "", _markdown_table(tables[key]), ""])
    if _has_hard_adversarial_rows(df):
        lines.extend(
            [
                "## Hard/Adversarial Subset Note",
                "",
                "This result file contains hard-difficulty or adversarial rows. Treat these "
                "as a more credibility-relevant stress slice than easy benign examples, "
                "while still recognizing that all data is synthetic and requires manual review.",
                "",
            ]
        )
    return "\n".join(lines)


def _has_hard_adversarial_rows(df: pd.DataFrame) -> bool:
    """Return whether rows include hard or adversarial examples."""

    has_hard = "difficulty" in df.columns and (df["difficulty"] == "hard").any()
    has_adversarial = "attack_type" in df.columns and (df["attack_type"] != "none").any()
    return bool(has_hard or has_adversarial)


def overall_terminal_summary(df: pd.DataFrame) -> dict[str, float]:
    """Return compact metrics for terminal output."""

    summary = {"rows": float(len(df))}
    for metric in METRIC_COLUMNS:
        summary[metric] = float(df[metric].mean())
    return summary


def summarize_scores(scores: list[EvalResult]) -> dict[str, float]:
    """Summarize in-memory EvalResult objects for compatibility."""

    if not scores:
        return {"count": 0.0}
    return {
        "count": float(len(scores)),
        "mean_extraction_accuracy": sum(score.extraction_accuracy for score in scores)
        / len(scores),
    }


def _group_key_to_row(group_cols: list[str], group_key: Any) -> dict[str, Any]:
    """Convert a pandas group key into named columns."""

    if len(group_cols) == 1:
        if isinstance(group_key, tuple):
            group_key = group_key[0]
        return {group_cols[0]: group_key}
    return dict(zip(group_cols, group_key, strict=True))


def _markdown_table(df: pd.DataFrame) -> str:
    """Render a small DataFrame as Markdown."""

    if df.empty:
        return "_No rows._"
    render_df = df.copy()
    for column in render_df.columns:
        if pd.api.types.is_float_dtype(render_df[column]):
            render_df[column] = render_df[column].map(lambda value: f"{value:.3f}")
    columns = [str(column) for column in render_df.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in render_df.itertuples(index=False, name=None):
        values = [_escape_markdown_cell(value) for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _escape_markdown_cell(value: Any) -> str:
    """Escape a value for a Markdown table cell."""

    return str(value).replace("|", "/")
