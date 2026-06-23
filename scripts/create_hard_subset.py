"""Create a harder balanced ReceiptInject evaluation subset."""

from __future__ import annotations

import argparse
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receiptinject.dataset_generator import load_jsonl, save_jsonl  # noqa: E402
from receiptinject.schemas import AttackType, Difficulty  # noqa: E402
from scripts.create_balanced_subset import _select_adversarial, _select_balanced  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--seed", type=int, default=123)
    return parser.parse_args()


def main() -> None:
    """Create and save hard subset."""

    args = parse_args()
    examples = load_jsonl(args.data)
    subset = create_hard_subset(examples, n=args.n, seed=args.seed)
    save_jsonl(subset, Path(args.out))
    print_hard_summary(subset)
    print(f"Output: {args.out}")


def create_hard_subset(examples: list, *, n: int, seed: int) -> list:
    """Create a 20 benign / 30 adversarial hard-leaning subset."""

    if n != 50:
        raise ValueError("hard subset currently expects n=50")
    rng = random.Random(seed)
    ranked = sorted(
        examples,
        key=lambda example: _difficulty_rank(example.difficulty),
        reverse=True,
    )
    benign_pool = [example for example in ranked if example.attack_type == AttackType.NONE]
    adversarial_pool = [
        example for example in ranked if example.attack_type != AttackType.NONE
    ]
    benign = _select_balanced(
        benign_pool,
        20,
        primary_key=lambda example: example.doc_type.value,
    )
    adversarial = _select_adversarial(adversarial_pool, 30)
    selected = [*benign, *adversarial]
    rng.shuffle(selected)
    if len({example.id for example in selected}) != len(selected):
        raise ValueError("duplicate IDs in hard subset")
    return selected


def print_hard_summary(examples: list) -> None:
    """Print hard subset summary."""

    summary = validate_dataset_balance_relaxed(examples)
    print("Hard subset summary")
    print(f"total rows: {len(examples)}")
    print(f"doc_type counts: {dict(sorted(summary['doc_type'].items()))}")
    print(f"attack_type counts: {dict(sorted(summary['attack_type'].items()))}")
    print(f"difficulty counts: {dict(sorted(summary['difficulty'].items()))}")
    print(f"benign/adversarial counts: {dict(sorted(summary['benign_adversarial'].items()))}")


def validate_dataset_balance_relaxed(examples: list) -> dict[str, Counter[str]]:
    """Return counts without enforcing 50/50 benign/adversarial balance."""

    benign = sum(example.attack_type == AttackType.NONE for example in examples)
    return {
        "doc_type": Counter(example.doc_type.value for example in examples),
        "attack_type": Counter(example.attack_type.value for example in examples),
        "difficulty": Counter(example.difficulty.value for example in examples),
        "benign_adversarial": Counter(
            {"benign": benign, "adversarial": len(examples) - benign}
        ),
    }


def _difficulty_rank(difficulty: Difficulty) -> int:
    """Rank harder examples first."""

    return {
        Difficulty.HARD: 3,
        Difficulty.MEDIUM: 2,
        Difficulty.EASY: 1,
    }[difficulty]


if __name__ == "__main__":
    main()
