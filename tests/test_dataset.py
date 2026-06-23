"""Tests for deterministic balanced dataset generation."""

from collections import Counter

import pytest

from receiptinject.dataset_generator import (
    audit_dataset,
    generate_dataset,
    load_jsonl,
    render_audit_report,
    save_jsonl,
    validate_dataset_balance,
)
from receiptinject.schemas import AttackType, Difficulty, DocumentType


def test_generate_dataset_is_deterministic() -> None:
    """Same n and seed should produce identical records."""

    first = generate_dataset(n=30, seed=42)
    second = generate_dataset(n=30, seed=42)
    assert first == second
    assert len(first) == 30


def test_generate_dataset_supports_legacy_count_argument() -> None:
    """Earlier scaffold callers used count as the size keyword."""

    examples = generate_dataset(count=3, seed=42)
    assert len(examples) == 3


def test_generate_500_matches_requested_document_composition() -> None:
    """The target 500-example dataset should match requested document counts."""

    examples = generate_dataset(n=500, seed=42)
    counts = Counter(example.doc_type for example in examples)
    assert counts == {
        DocumentType.RECEIPT: 125,
        DocumentType.INVOICE: 125,
        DocumentType.BANK_STATEMENT: 100,
        DocumentType.POLICY_DOCUMENT: 100,
        DocumentType.MIXED_BUNDLE: 50,
    }


def test_generate_500_matches_requested_difficulty_distribution() -> None:
    """The target 500-example dataset should match 35/45/20 difficulty counts."""

    examples = generate_dataset(n=500, seed=42)
    counts = Counter(example.difficulty for example in examples)
    assert counts == {
        Difficulty.EASY: 175,
        Difficulty.MEDIUM: 225,
        Difficulty.HARD: 100,
    }


def test_generate_500_is_half_benign_and_roughly_attack_balanced() -> None:
    """Half the target dataset should be benign, with adversarial types spread evenly."""

    examples = generate_dataset(n=500, seed=42)
    counts = Counter(example.attack_type for example in examples)
    assert counts[AttackType.NONE] == 250

    adversarial_counts = [
        counts[attack_type] for attack_type in AttackType if attack_type != AttackType.NONE
    ]
    assert sum(adversarial_counts) == 250
    assert max(adversarial_counts) - min(adversarial_counts) <= 1


def test_examples_have_required_private_fields_and_embedded_spans() -> None:
    """Generated examples should include private fields and visible spans when adversarial."""

    examples = generate_dataset(n=40, seed=5)
    required_private_keys = {
        "customer_name",
        "payment_last4",
        "account_last4",
        "account_holder",
        "internal_customer_id",
        "client_email",
        "internal_account_code",
        "internal_reviewer",
        "internal_case_id",
    }
    for example in examples:
        assert required_private_keys == set(example.private_fields)
        assert example.document_text
        assert example.expected_task
        assert example.ground_truth_fields
        assert example.safe_behavior_description
        assert example.expected_output_constraints
        assert example.tags
        if example.attack_type == AttackType.NONE:
            assert example.unsafe_instruction_present is False
            assert example.embedded_instruction_span is None
        else:
            assert example.unsafe_instruction_present is True
            assert example.embedded_instruction_span
            assert example.embedded_instruction_span in example.document_text


def test_save_and_load_jsonl_round_trip(tmp_path) -> None:
    """JSONL helpers should preserve Pydantic examples."""

    examples = generate_dataset(n=12, seed=9)
    path = tmp_path / "examples.jsonl"
    save_jsonl(examples, path)
    assert load_jsonl(path) == examples


def test_validate_dataset_balance_rejects_duplicate_ids() -> None:
    """Balance validation should catch duplicate example IDs."""

    examples = generate_dataset(n=4, seed=1)
    duplicated = [examples[0], examples[0], *examples[2:]]
    with pytest.raises(ValueError, match="ids must be unique"):
        validate_dataset_balance(duplicated)


def test_audit_dataset_passes_generated_dataset() -> None:
    """Generated datasets should pass the research-grade audit."""

    examples = generate_dataset(n=60, seed=10)
    report = audit_dataset(examples)
    assert report.passed
    assert report.error_count == 0


def test_audit_dataset_detects_duplicate_document_text() -> None:
    """The audit should reject repeated document bodies."""

    examples = generate_dataset(n=20, seed=11)
    duplicate = examples[1].model_copy(update={"document_text": examples[0].document_text})
    report = audit_dataset([examples[0], duplicate, *examples[2:]])
    assert not report.passed
    assert any(finding.check == "duplicate_document_text" for finding in report.findings)


def test_audit_dataset_detects_private_field_visible_without_allow_tag() -> None:
    """Private field values should not leak into document text by accident."""

    examples = generate_dataset(n=20, seed=12)
    private_value = examples[0].private_fields["client_email"]
    leaked = examples[0].model_copy(
        update={"document_text": f"{examples[0].document_text}\n{private_value}"}
    )
    report = audit_dataset([leaked, *examples[1:]])
    assert not report.passed
    assert any(finding.check == "private_field_placement" for finding in report.findings)


def test_audit_dataset_detects_broken_mixed_bundle_structure() -> None:
    """Mixed bundles should contain multiple document sections."""

    examples = generate_dataset(n=20, seed=13)
    bundle_index = next(
        index
        for index, example in enumerate(examples)
        if example.doc_type == DocumentType.MIXED_BUNDLE
    )
    broken = examples[bundle_index].model_copy(update={"document_text": "MIXED BUNDLE ONLY"})
    mutated = [*examples]
    mutated[bundle_index] = broken
    report = audit_dataset(mutated)
    assert not report.passed
    assert any(finding.check == "mixed_bundle_sections" for finding in report.findings)


def test_audit_report_renders_markdown_summary() -> None:
    """Audit reports should produce a readable Markdown artifact."""

    report = audit_dataset(generate_dataset(n=20, seed=14), dataset_path="data/test.jsonl")
    markdown = render_audit_report(report)
    assert "# ReceiptInject Dataset Audit" in markdown
    assert "Status: **PASS**" in markdown
