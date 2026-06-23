"""Create a balanced deterministic ReceiptInject evaluation subset."""

from __future__ import annotations

import argparse
import random
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Hashable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receiptinject.dataset_generator import (  # noqa: E402
    load_jsonl,
    save_jsonl,
    validate_dataset_balance,
)
from receiptinject.schemas import AttackType, BenchmarkExample  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Input BenchmarkExample JSONL path.")
    parser.add_argument("--out", required=True, help="Output subset JSONL path.")
    parser.add_argument("--n", type=int, required=True, help="Number of examples to select.")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic selection seed.")
    return parser.parse_args()


def main() -> None:
    """Create and save a balanced subset."""

    args = parse_args()
    examples = load_jsonl(args.data)
    subset = create_balanced_subset(examples, n=args.n, seed=args.seed)
    save_jsonl(subset, Path(args.out))
    print_subset_summary(subset)
    print(f"Output: {args.out}")


def create_balanced_subset(
    examples: list[BenchmarkExample],
    *,
    n: int,
    seed: int,
) -> list[BenchmarkExample]:
    """Return a deterministic subset balanced by safety label and document family."""

    if n <= 0:
        raise ValueError("n must be positive")
    if n > len(examples):
        raise ValueError(f"n={n} exceeds dataset size {len(examples)}")

    rng = random.Random(seed)
    shuffled = list(examples)
    rng.shuffle(shuffled)

    benign = [example for example in shuffled if example.attack_type == AttackType.NONE]
    adversarial = [example for example in shuffled if example.attack_type != AttackType.NONE]

    target_benign = min(n // 2, len(benign))
    target_adversarial = min(n - target_benign, len(adversarial))
    if target_benign + target_adversarial < n:
        remaining = n - target_benign - target_adversarial
        target_benign += min(remaining, len(benign) - target_benign)
        remaining = n - target_benign - target_adversarial
        target_adversarial += min(remaining, len(adversarial) - target_adversarial)
    if target_benign + target_adversarial < n:
        raise ValueError("not enough benign/adversarial examples to build subset")

    selected_benign = _select_balanced(
        benign,
        target_benign,
        primary_key=lambda example: example.doc_type.value,
    )
    selected_adversarial = _select_adversarial(adversarial, target_adversarial)

    selected_ids = {example.id for example in [*selected_benign, *selected_adversarial]}
    if len(selected_ids) < n:
        remaining_pool = [example for example in shuffled if example.id not in selected_ids]
        fill = _select_balanced(
            remaining_pool,
            n - len(selected_ids),
            primary_key=lambda example: (example.attack_type.value, example.doc_type.value),
        )
        selected = [*selected_benign, *selected_adversarial, *fill]
    else:
        selected = [*selected_benign, *selected_adversarial]

    rng.shuffle(selected)
    return selected[:n]


def _select_adversarial(
    examples: list[BenchmarkExample],
    target: int,
) -> list[BenchmarkExample]:
    """Select adversarial examples balanced first by attack type, then document type."""

    selected: list[BenchmarkExample] = []
    attack_quotas = _balanced_quotas(
        examples,
        target,
        key=lambda example: example.attack_type.value,
    )
    doc_quotas = _balanced_quotas(
        examples,
        target,
        key=lambda example: example.doc_type.value,
    )
    remaining_by_attack = {
        attack_type: [
            example for example in examples if example.attack_type.value == attack_type
        ]
        for attack_type in attack_quotas
    }
    attack_counts = {attack_type: 0 for attack_type in attack_quotas}
    doc_counts = {doc_type: 0 for doc_type in doc_quotas}

    while len(selected) < target:
        progressed = False
        for attack_type in sorted(attack_quotas, key=str):
            if attack_counts[attack_type] >= attack_quotas[attack_type]:
                continue
            bucket = remaining_by_attack[attack_type]
            if not bucket:
                continue
            index, example = _best_document_fit(bucket, doc_quotas, doc_counts)
            selected.append(example)
            del bucket[index]
            attack_counts[attack_type] += 1
            doc_counts[example.doc_type.value] = doc_counts.get(example.doc_type.value, 0) + 1
            progressed = True
            if len(selected) == target:
                break
        if not progressed:
            break

    selected_ids = {example.id for example in selected}
    if len(selected) < target:
        remaining = [example for example in examples if example.id not in selected_ids]
        selected.extend(
            _select_balanced(
                remaining,
                target - len(selected),
                primary_key=lambda example: (example.attack_type.value, example.doc_type.value),
            )
        )
    return selected[:target]


def _best_document_fit(
    bucket: list[BenchmarkExample],
    doc_quotas: dict[Hashable, int],
    doc_counts: dict[Hashable, int],
) -> tuple[int, BenchmarkExample]:
    """Return the bucket item that best fills the current document-type deficit."""

    best_index = 0
    best_score: tuple[int, int, int] | None = None
    for index, example in enumerate(bucket):
        doc_type = example.doc_type.value
        deficit = doc_quotas.get(doc_type, 0) - doc_counts.get(doc_type, 0)
        score = (deficit, -doc_counts.get(doc_type, 0), -index)
        if best_score is None or score > best_score:
            best_score = score
            best_index = index
    return best_index, bucket[best_index]


def _select_balanced(
    examples: list[BenchmarkExample],
    target: int,
    *,
    primary_key: Callable[[BenchmarkExample], Hashable],
) -> list[BenchmarkExample]:
    """Select examples according to balanced quotas for one grouping key."""

    if target <= 0:
        return []
    quotas = _balanced_quotas(examples, target, key=primary_key)
    selected: list[BenchmarkExample] = []
    for group in sorted(quotas, key=str):
        bucket = [example for example in examples if primary_key(example) == group]
        selected.extend(bucket[: quotas[group]])
    return selected[:target]


def _balanced_quotas(
    examples: list[BenchmarkExample],
    target: int,
    *,
    key: Callable[[BenchmarkExample], Hashable],
) -> dict[Hashable, int]:
    """Allocate near-even quotas across available groups."""

    buckets: dict[Hashable, list[BenchmarkExample]] = defaultdict(list)
    for example in examples:
        buckets[key(example)].append(example)

    groups = sorted(buckets, key=str)
    if not groups or target <= 0:
        return {}

    quotas = {group: 0 for group in groups}
    while sum(quotas.values()) < target:
        progressed = False
        for group in groups:
            if quotas[group] < len(buckets[group]):
                quotas[group] += 1
                progressed = True
                if sum(quotas.values()) == target:
                    break
        if not progressed:
            break
    return quotas


def print_subset_summary(examples: list[BenchmarkExample]) -> None:
    """Print the requested subset summary."""

    summary = validate_dataset_balance(examples)
    print("Balanced subset summary")
    print(f"total rows: {len(examples)}")
    print(f"doc_type counts: {_format_counter(summary['doc_type'])}")
    print(f"attack_type counts: {_format_counter(summary['attack_type'])}")
    print(f"difficulty counts: {_format_counter(summary['difficulty'])}")
    print(f"benign/adversarial counts: {_format_counter(summary['benign_adversarial'])}")


def _format_counter(counter: Counter[str]) -> dict[str, int]:
    """Return a stable plain-dict representation for printing."""

    keys = sorted(counter)
    if AttackType.NONE.value in counter:
        keys = [AttackType.NONE.value, *[key for key in keys if key != AttackType.NONE.value]]
    return {key: counter[key] for key in keys}


if __name__ == "__main__":
    main()
