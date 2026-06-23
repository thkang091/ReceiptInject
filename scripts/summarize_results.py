"""Summarize ReceiptInject scored evaluation results."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receiptinject.analysis import (  # noqa: E402
    generate_summary,
    load_results_csv,
    overall_terminal_summary,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/results.csv", help="Scored CSV path.")
    parser.add_argument("--out", default="results/summary.md", help="Markdown summary path.")
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=1000,
        help="Bootstrap resamples for 95% confidence intervals.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Bootstrap RNG seed.")
    return parser.parse_args()


def main() -> None:
    """Generate Markdown and CSV aggregate summaries."""

    args = parse_args()
    outputs = generate_summary(
        results_path=Path(args.results),
        out_path=Path(args.out),
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
    )
    df = load_results_csv(Path(args.results))
    terminal_summary = overall_terminal_summary(df)

    print("Overall summary")
    for key, value in terminal_summary.items():
        if key == "rows":
            print(f"{key}: {int(value)}")
        else:
            print(f"{key}: {value:.4f}")
    print(f"Markdown summary: {outputs.markdown_path}")
    print("Aggregate tables:")
    for name, path in outputs.aggregate_paths.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
