"""Generate the scaled 300-example ReceiptInject suite."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receiptinject.dataset_generator import (  # noqa: E402
    generate_300_suite,
    save_jsonl,
    validate_dataset_balance,
)
from receiptinject.schemas import AttackType  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/examples_300.jsonl")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    """Generate and save the 300-example suite."""

    args = parse_args()
    examples = generate_300_suite(seed=args.seed)
    save_jsonl(examples, args.output)
    summary = validate_dataset_balance(examples)

    print("Generated ReceiptInject 300-example suite")
    print(f"output: {args.output}")
    print(f"seed: {args.seed}")
    print(f"total examples: {len(examples)}")
    print(f"document type counts: {_format_counter(summary['doc_type'])}")
    print(f"attack type counts: {_format_counter(summary['attack_type'])}")
    print(f"difficulty counts: {_format_counter(summary['difficulty'])}")
    print(
        "benign/adversarial counts: "
        f"{_format_counter(summary['benign_adversarial'])}"
    )


def _format_counter(counter: Counter[str]) -> dict[str, int]:
    """Return a stable dict representation for printed summaries."""

    keys = sorted(counter)
    if AttackType.NONE.value in counter:
        keys = [AttackType.NONE.value, *[key for key in keys if key != AttackType.NONE.value]]
    return {key: counter[key] for key in keys}


if __name__ == "__main__":
    main()
