"""Tests for balanced real-evaluation subset creation."""

from __future__ import annotations

from collections import Counter

from receiptinject.dataset_generator import generate_dataset
from receiptinject.schemas import AttackType
from scripts.create_balanced_subset import create_balanced_subset


def test_balanced_subset_is_deterministic() -> None:
    """Same seed and input should produce identical subset IDs."""

    examples = generate_dataset(n=500, seed=42)
    first = create_balanced_subset(examples, n=50, seed=42)
    second = create_balanced_subset(examples, n=50, seed=42)

    assert [example.id for example in first] == [example.id for example in second]


def test_balanced_subset_is_half_benign_and_adversarial() -> None:
    """Subset should include both benign and adversarial examples evenly."""

    examples = generate_dataset(n=500, seed=42)
    subset = create_balanced_subset(examples, n=100, seed=42)
    counts = Counter(
        "benign" if example.attack_type == AttackType.NONE else "adversarial"
        for example in subset
    )

    assert len(subset) == 100
    assert counts == {"benign": 50, "adversarial": 50}


def test_balanced_subset_spreads_document_and_attack_types() -> None:
    """Subset should cover all document types and all adversarial attack types when possible."""

    examples = generate_dataset(n=500, seed=42)
    subset = create_balanced_subset(examples, n=100, seed=42)
    doc_types = {example.doc_type for example in subset}
    adversarial_attack_types = {
        example.attack_type for example in subset if example.attack_type != AttackType.NONE
    }

    assert len(doc_types) == 5
    assert adversarial_attack_types == {
        attack_type for attack_type in AttackType if attack_type != AttackType.NONE
    }


def test_balanced_subset_rejects_too_large_request() -> None:
    """Subset size cannot exceed the source dataset."""

    examples = generate_dataset(n=10, seed=42)

    try:
        create_balanced_subset(examples, n=11, seed=42)
    except ValueError as exc:
        assert "exceeds dataset size" in str(exc)
    else:
        raise AssertionError("expected ValueError")
