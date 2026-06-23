"""Create balanced non-overlapping dev/test subsets for ReceiptInject."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receiptinject.dataset_generator import load_jsonl, save_jsonl  # noqa: E402
from scripts.create_balanced_subset import (  # noqa: E402
    create_balanced_subset,
    print_subset_summary,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True)
    parser.add_argument("--dev-out", required=True)
    parser.add_argument("--test-out", required=True)
    parser.add_argument("--n-dev", type=int, default=50)
    parser.add_argument("--n-test", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    """Create and save deterministic balanced dev/test splits."""

    args = parse_args()
    examples = load_jsonl(args.data)
    dev = create_balanced_subset(examples, n=args.n_dev, seed=args.seed)
    dev_ids = {example.id for example in dev}
    remaining = [example for example in examples if example.id not in dev_ids]
    test = create_balanced_subset(remaining, n=args.n_test, seed=args.seed + 1)

    overlap = dev_ids.intersection(example.id for example in test)
    if overlap:
        raise ValueError(f"dev/test overlap detected: {sorted(overlap)[:5]}")

    save_jsonl(dev, Path(args.dev_out))
    save_jsonl(test, Path(args.test_out))

    print("DEV SPLIT")
    print_subset_summary(dev)
    print(f"Output: {args.dev_out}")
    print("")
    print("TEST SPLIT")
    print_subset_summary(test)
    print(f"Output: {args.test_out}")


if __name__ == "__main__":
    main()
