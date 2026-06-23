"""Generate a balanced synthetic ReceiptInject dataset."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receiptinject.dataset_generator import (  # noqa: E402
    generate_dataset,
    save_jsonl,
    validate_dataset_balance,
)
from receiptinject.schemas import AttackType  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=500, help="Number of synthetic examples.")
    parser.add_argument("--output", default="data/examples_500.jsonl", help="Output JSONL path.")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic generation seed.")
    return parser.parse_args()


def main() -> None:
    """Run dataset generation and print balance statistics."""

    args = parse_args()
    examples = generate_dataset(n=args.n, seed=args.seed)
    save_jsonl(examples, Path(args.output))
    summary = validate_dataset_balance(examples)
    _print_summary(total=len(examples), summary=summary)
    print(f"Output: {args.output}")


def _print_summary(total: int, summary: dict[str, Counter[str]]) -> None:
    """Print a compact dataset summary."""

    print("Dataset summary")
    print(f"total examples: {total}")
    print(f"document type counts: {_format_counter(summary['doc_type'])}")
    print(f"attack type counts: {_format_counter(summary['attack_type'])}")
    print(f"difficulty counts: {_format_counter(summary['difficulty'])}")
    print(
        "benign/adversarial counts: "
        f"{_format_counter(summary['benign_adversarial'])}"
    )


def _format_counter(counter: Counter[str]) -> dict[str, int]:
    """Return a stable plain-dict representation for printing."""

    keys = sorted(counter)
    if AttackType.NONE.value in counter:
        keys = [AttackType.NONE.value, *[key for key in keys if key != AttackType.NONE.value]]
    return {key: counter[key] for key in keys}


if __name__ == "__main__":
    main()
