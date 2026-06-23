"""Export ReceiptInject failure cases for qualitative analysis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receiptinject.failure_cases import export_failure_cases  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/results.csv", help="Scored CSV path.")
    parser.add_argument("--data", default="data/examples_500.jsonl", help="Dataset JSONL path.")
    parser.add_argument(
        "--raw",
        default="results/raw_outputs.jsonl",
        help="Raw outputs JSONL path.",
    )
    parser.add_argument(
        "--out",
        default="results/failure_cases.md",
        help="Markdown failure-case report path.",
    )
    parser.add_argument(
        "--max-per-section",
        type=int,
        default=8,
        help="Maximum cases to show in each report section.",
    )
    return parser.parse_args()


def main() -> None:
    """Export a Markdown failure-case report."""

    args = parse_args()
    try:
        output_path = export_failure_cases(
            results_path=Path(args.results),
            data_path=Path(args.data),
            raw_path=Path(args.raw),
            out_path=Path(args.out),
            max_per_section=args.max_per_section,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Failure-case report written: {output_path}")


if __name__ == "__main__":
    main()
