"""Tests for balanced dev/test split creation."""

from __future__ import annotations

from receiptinject.dataset_generator import generate_dataset
from receiptinject.schemas import AttackType
from scripts.create_balanced_subset import create_balanced_subset


def test_dev_test_splits_have_no_overlapping_ids() -> None:
    """Balanced dev/test subsets should not reuse example IDs."""

    examples = generate_dataset(n=500, seed=42)
    dev = create_balanced_subset(examples, n=50, seed=42)
    dev_ids = {example.id for example in dev}
    test = create_balanced_subset(
        [example for example in examples if example.id not in dev_ids],
        n=50,
        seed=43,
    )
    test_ids = {example.id for example in test}

    assert not dev_ids.intersection(test_ids)
    assert sum(example.attack_type == AttackType.NONE for example in dev) == 25
    assert sum(example.attack_type == AttackType.NONE for example in test) == 25
