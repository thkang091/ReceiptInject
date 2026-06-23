"""Tests for credibility-oriented audit and hard subset scripts."""

from __future__ import annotations

from receiptinject.dataset_generator import generate_dataset
from receiptinject.schemas import AttackType, Difficulty
from scripts.audit_dataset_diversity import build_diversity_report
from scripts.create_hard_subset import create_hard_subset


def test_dataset_diversity_audit_reports_repeated_values() -> None:
    """Diversity audit should surface repeated tracked values."""

    examples = generate_dataset(n=20, seed=42)
    duplicated = examples[1].model_copy(
        update={"ground_truth_fields": examples[0].ground_truth_fields}
    )
    report = build_diversity_report([examples[0], duplicated, *examples[2:]], "memory")
    assert "Repeated Ground Truth Values" in report
    assert "Count" in report


def test_hard_subset_has_adversarial_examples_and_hard_lean() -> None:
    """Hard subset should be 20 benign / 30 adversarial and mostly medium/hard."""

    subset = create_hard_subset(generate_dataset(n=500, seed=42), n=50, seed=123)
    benign = sum(example.attack_type == AttackType.NONE for example in subset)
    adversarial = len(subset) - benign
    medium_or_hard = sum(
        example.difficulty in {Difficulty.MEDIUM, Difficulty.HARD} for example in subset
    )

    assert benign == 20
    assert adversarial == 30
    assert medium_or_hard >= 40
    assert len({example.doc_type for example in subset}) == 5
    assert len({example.id for example in subset}) == 50
