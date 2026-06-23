"""Create matplotlib figures for ReceiptInject scored evaluation results."""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

METRICS_BY_MITIGATION = [
    ("unsafe_action_rate", "Unsafe Action Rate", "unsafe_action_rate_by_mitigation.png"),
    ("privacy_leakage", "Privacy Leakage", "privacy_leakage_by_mitigation.png"),
    (
        "prompt_injection_compliance",
        "Prompt Injection Compliance",
        "prompt_injection_compliance_by_mitigation.png",
    ),
    ("extraction_accuracy", "Extraction Accuracy", "extraction_accuracy_by_mitigation.png"),
]

MODEL_COMPARISON_METRICS = [
    "extraction_accuracy",
    "safe_completion_rate",
    "utility_safety_tradeoff",
]

TEXT_OCR_METRICS = [
    "extraction_accuracy",
    "safe_completion_rate",
    "prompt_injection_compliance",
    "privacy_leakage",
    "unsafe_action_rate",
]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/results.csv", help="Scored CSV path.")
    parser.add_argument("--out", default="results/figures", help="Directory for PNG figures.")
    parser.add_argument(
        "--output-dir",
        dest="out",
        help="Backward-compatible alias for --out.",
    )
    return parser.parse_args()


def main() -> None:
    """Generate requested figures from an existing results CSV."""

    args = parse_args()
    results_path = Path(args.results)
    out_dir = Path(args.out)

    try:
        rows = load_rows(results_path)
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    out_dir.mkdir(parents=True, exist_ok=True)
    made: list[Path] = []

    for metric, title, filename in METRICS_BY_MITIGATION:
        path = make_metric_by_mitigation(rows, metric, title, out_dir / filename)
        if path is not None:
            made.append(path)

    path = make_safety_utility_tradeoff(rows, out_dir / "safety_utility_tradeoff.png")
    if path is not None:
        made.append(path)

    path = make_model_comparison(rows, out_dir / "model_comparison.png")
    if path is not None:
        made.append(path)

    path = make_text_vs_ocr_comparison(rows, out_dir / "text_vs_ocr_comparison.png")
    if path is not None:
        made.append(path)

    print(f"Figures written: {len(made)}")
    for path in made:
        print(f"- {path}")


def load_rows(path: Path) -> list[dict[str, Any]]:
    """Load CSV result rows and coerce metric columns to floats."""

    if not path.exists():
        raise FileNotFoundError(f"Results CSV does not exist: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if not rows:
        raise ValueError(f"Results CSV has no rows: {path}")

    needed = {
        "model_name",
        "mitigation",
        "input_mode",
        "extraction_accuracy",
        "prompt_injection_compliance",
        "privacy_leakage",
        "unsafe_action_rate",
        "safe_completion_rate",
        "utility_safety_tradeoff",
    }
    missing = sorted(needed.difference(rows[0]))
    if missing:
        raise ValueError(f"Results CSV is missing required columns: {', '.join(missing)}")

    for row in rows:
        for metric in needed.intersection(row):
            if metric in {"model_name", "mitigation", "input_mode"}:
                continue
            row[metric] = _to_float(row.get(metric))
    return rows


def make_metric_by_mitigation(
    rows: list[dict[str, Any]],
    metric: str,
    title: str,
    path: Path,
) -> Path | None:
    """Create a bar chart for one metric grouped by mitigation mode."""

    means = grouped_metric_means(rows, ["mitigation"], metric)
    if not means:
        print(f"Skipping {path.name}: no numeric `{metric}` values found.")
        return None

    labels = [key[0] for key in means]
    values = list(means.values())
    fig, ax = plt.subplots(figsize=figure_size_for_labels(labels))
    ax.bar(labels, values)
    ax.set_title(f"{title} by Mitigation")
    ax.set_xlabel("Mitigation")
    ax.set_ylabel(title)
    ax.set_ylim(0, y_axis_upper(values))
    ax.tick_params(axis="x", labelrotation=25)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    save_figure(fig, path)
    return path


def make_safety_utility_tradeoff(rows: list[dict[str, Any]], path: Path) -> Path | None:
    """Create a scatter plot of utility against safety completion."""

    required = ["extraction_accuracy", "safe_completion_rate", "utility_safety_tradeoff"]
    if any(not has_numeric_values(rows, metric) for metric in required):
        print(
            f"Skipping {path.name}: need numeric extraction_accuracy, "
            "safe_completion_rate, and utility_safety_tradeoff."
        )
        return None

    grouped = grouped_rows(rows, ["model_name", "mitigation"])
    points: list[tuple[str, float, float, float]] = []
    for key, group in grouped.items():
        label = " / ".join(key)
        points.append(
            (
                label,
                mean(row["extraction_accuracy"] for row in group),
                mean(row["safe_completion_rate"] for row in group),
                mean(row["utility_safety_tradeoff"] for row in group),
            )
        )
    if not points:
        print(f"Skipping {path.name}: no grouped rows available.")
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    x_values = [point[1] for point in points]
    y_values = [point[2] for point in points]
    sizes = [80 + 260 * max(0.0, point[3]) for point in points]
    ax.scatter(x_values, y_values, s=sizes, alpha=0.75)
    for label, x_value, y_value, _tradeoff in points:
        ax.annotate(label, (x_value, y_value), xytext=(5, 5), textcoords="offset points")
    ax.set_title("Safety/Utility Tradeoff")
    ax.set_xlabel("Extraction Accuracy")
    ax.set_ylabel("Safe Completion Rate")
    ax.set_xlim(0, y_axis_upper(x_values))
    ax.set_ylim(0, y_axis_upper(y_values))
    ax.grid(alpha=0.25)
    fig.tight_layout()
    save_figure(fig, path)
    return path


def make_model_comparison(rows: list[dict[str, Any]], path: Path) -> Path | None:
    """Create a grouped bar chart when multiple models are present."""

    models = sorted({str(row["model_name"]) for row in rows if row.get("model_name")})
    if len(models) < 2:
        print(f"Skipping {path.name}: only one model found.")
        return None

    grouped = grouped_metric_table(rows, ["model_name"], MODEL_COMPARISON_METRICS)
    if not grouped:
        print(f"Skipping {path.name}: no model metric values found.")
        return None
    return make_grouped_bar_chart(
        grouped,
        MODEL_COMPARISON_METRICS,
        title="Model Comparison",
        xlabel="Model",
        ylabel="Metric Mean",
        path=path,
    )


def make_text_vs_ocr_comparison(rows: list[dict[str, Any]], path: Path) -> Path | None:
    """Create a grouped bar chart comparing text and OCR input modes."""

    modes = sorted({str(row["input_mode"]) for row in rows if row.get("input_mode")})
    if "ocr" not in modes:
        print(f"Skipping {path.name}: no OCR rows found.")
        return None
    if len(modes) < 2:
        print(f"Skipping {path.name}: OCR rows exist, but no second input mode to compare.")
        return None

    grouped = grouped_metric_table(rows, ["input_mode"], TEXT_OCR_METRICS)
    if not grouped:
        print(f"Skipping {path.name}: no input-mode metric values found.")
        return None
    return make_grouped_bar_chart(
        grouped,
        TEXT_OCR_METRICS,
        title="Text vs OCR Comparison",
        xlabel="Input Mode",
        ylabel="Metric Mean",
        path=path,
    )


def make_grouped_bar_chart(
    grouped: dict[str, dict[str, float]],
    metrics: list[str],
    title: str,
    xlabel: str,
    ylabel: str,
    path: Path,
) -> Path:
    """Create a grouped bar chart from label -> metric -> value."""

    labels = list(grouped)
    x_positions = list(range(len(labels)))
    width = 0.8 / max(1, len(metrics))
    fig, ax = plt.subplots(figsize=figure_size_for_labels(labels, extra_width=2.0))
    for index, metric in enumerate(metrics):
        offsets = [x + (index - (len(metrics) - 1) / 2) * width for x in x_positions]
        values = [grouped[label].get(metric, 0.0) for label in labels]
        ax.bar(offsets, values, width=width, label=metric.replace("_", " ").title())
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x_positions, labels, rotation=20, ha="right")
    ax.set_ylim(0, y_axis_upper([value for label in labels for value in grouped[label].values()]))
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    save_figure(fig, path)
    return path


def grouped_metric_table(
    rows: list[dict[str, Any]],
    group_cols: list[str],
    metrics: list[str],
) -> dict[str, dict[str, float]]:
    """Return label -> metric means for grouped rows."""

    groups = grouped_rows(rows, group_cols)
    table: dict[str, dict[str, float]] = {}
    for key, group in groups.items():
        label = " / ".join(key)
        table[label] = {}
        for metric in metrics:
            values = numeric_values(group, metric)
            if values:
                table[label][metric] = mean(values)
    return {label: values for label, values in table.items() if values}


def grouped_metric_means(
    rows: list[dict[str, Any]],
    group_cols: list[str],
    metric: str,
) -> dict[tuple[str, ...], float]:
    """Return metric means keyed by group tuple."""

    means: dict[tuple[str, ...], float] = {}
    for key, group in grouped_rows(rows, group_cols).items():
        values = numeric_values(group, metric)
        if values:
            means[key] = mean(values)
    return dict(sorted(means.items(), key=lambda item: item[0]))


def grouped_rows(
    rows: list[dict[str, Any]],
    group_cols: list[str],
) -> dict[tuple[str, ...], list[dict[str, Any]]]:
    """Group rows by a tuple of string column values."""

    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = tuple(str(row.get(column, "unknown") or "unknown") for column in group_cols)
        groups[key].append(row)
    return dict(sorted(groups.items(), key=lambda item: item[0]))


def numeric_values(rows: list[dict[str, Any]], metric: str) -> list[float]:
    """Collect finite numeric metric values from rows."""

    values: list[float] = []
    for row in rows:
        value = row.get(metric)
        if isinstance(value, int | float) and math.isfinite(float(value)):
            values.append(float(value))
    return values


def has_numeric_values(rows: list[dict[str, Any]], metric: str) -> bool:
    """Return whether at least one finite numeric value exists for a metric."""

    return bool(numeric_values(rows, metric))


def mean(values: Any) -> float:
    """Return the arithmetic mean for a finite non-empty iterable."""

    values_list = [float(value) for value in values]
    return sum(values_list) / len(values_list)


def _to_float(value: Any) -> float:
    """Coerce a CSV cell to float or NaN."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def y_axis_upper(values: list[float]) -> float:
    """Choose a neat upper y-axis bound for bounded metrics."""

    clean = [value for value in values if math.isfinite(value)]
    if not clean:
        return 1.0
    highest = max(clean)
    if highest <= 1.0:
        return 1.0
    return highest * 1.1


def figure_size_for_labels(labels: list[str], extra_width: float = 0.0) -> tuple[float, float]:
    """Scale figure width modestly for long mitigation/model labels."""

    longest = max((len(label) for label in labels), default=8)
    width = max(7.0, min(13.0, 4.5 + len(labels) * 0.8 + longest * 0.08 + extra_width))
    return (width, 4.8)


def save_figure(fig: plt.Figure, path: Path) -> None:
    """Save and close a matplotlib figure."""

    fig.savefig(path, dpi=160)
    plt.close(fig)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
