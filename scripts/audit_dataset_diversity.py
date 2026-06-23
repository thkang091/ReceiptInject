"""Audit synthetic dataset diversity and repeated benchmark values."""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receiptinject.dataset_generator import load_jsonl  # noqa: E402

TRACKED_FIELD_NAMES = {
    "account_label",
    "invoice_id",
    "transaction_id",
    "total",
    "receipt_total",
    "invoice_total",
    "merchant",
    "vendor",
    "institution",
    "bundle_id",
    "document_id",
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    return parser.parse_args()


def main() -> None:
    """Write diversity audit Markdown."""

    args = parse_args()
    examples = load_jsonl(args.data)
    report = build_diversity_report(examples, dataset_path=args.data)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(_terminal_summary(examples))
    print(f"Diversity audit: {out_path}")


def build_diversity_report(examples: list[Any], dataset_path: str) -> str:
    """Build a Markdown diversity report."""

    duplicate_text_count = len(examples) - len({example.document_text for example in examples})
    repeated_by_field = _repeated_ground_truth_values(examples)
    by_doc_type = _top_repeated_values_by_doc_type(examples)
    lines = [
        "# ReceiptInject Dataset Diversity Audit",
        "",
        f"Dataset: `{dataset_path}`",
        f"Total examples: {len(examples)}",
        f"Duplicate document_text count: {duplicate_text_count}",
        "",
        "## Repeated Ground Truth Values",
        "",
        _field_repetition_table(repeated_by_field),
        "",
        "## Top Repeated Values by Document Type",
        "",
    ]
    for doc_type, values in sorted(by_doc_type.items()):
        lines.extend([f"### {doc_type}", "", _counter_table(values), ""])
    return "\n".join(lines)


def _terminal_summary(examples: list[Any]) -> str:
    """Return compact terminal summary."""

    duplicate_text_count = len(examples) - len({example.document_text for example in examples})
    repeated = _repeated_ground_truth_values(examples)
    repeated_total = sum(sum(counter.values()) for counter in repeated.values())
    return (
        "Dataset diversity audit summary\n"
        f"total examples: {len(examples)}\n"
        f"duplicate document_text count: {duplicate_text_count}\n"
        f"repeated tracked value occurrences: {repeated_total}"
    )


def _repeated_ground_truth_values(examples: list[Any]) -> dict[str, Counter[str]]:
    """Return repeated tracked field values."""

    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for example in examples:
        for field_name, value in example.ground_truth_fields.items():
            if field_name in TRACKED_FIELD_NAMES:
                counters[field_name][_stringify_value(value)] += 1
    return {
        field: Counter({value: count for value, count in counter.items() if count > 1})
        for field, counter in counters.items()
    }


def _top_repeated_values_by_doc_type(examples: list[Any]) -> dict[str, Counter[str]]:
    """Return top repeated tracked values by document type."""

    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for example in examples:
        for field_name, value in example.ground_truth_fields.items():
            if field_name in TRACKED_FIELD_NAMES:
                counters[example.doc_type.value][f"{field_name}: {_stringify_value(value)}"] += 1
    return {
        doc_type: Counter({value: count for value, count in counter.items() if count > 1})
        for doc_type, counter in counters.items()
    }


def _field_repetition_table(repeated: dict[str, Counter[str]]) -> str:
    """Render repeated values by field."""

    lines = ["| Field | Repeated value | Count |", "| --- | --- | ---: |"]
    any_rows = False
    for field_name, counter in sorted(repeated.items()):
        for value, count in counter.most_common(10):
            lines.append(f"| {field_name} | `{value}` | {count} |")
            any_rows = True
    return "\n".join(lines) if any_rows else "_No repeated tracked field values._"


def _counter_table(counter: Counter[str]) -> str:
    """Render counter table."""

    if not counter:
        return "_No repeated tracked values._"
    lines = ["| Value | Count |", "| --- | ---: |"]
    for value, count in counter.most_common(10):
        lines.append(f"| `{value}` | {count} |")
    return "\n".join(lines)


def _stringify_value(value: Any) -> str:
    """Stable display for field values."""

    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


if __name__ == "__main__":
    main()
