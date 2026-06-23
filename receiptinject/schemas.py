"""Typed Pydantic contracts for ReceiptInject benchmark examples and results."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class DocumentType(StrEnum):
    """Document families covered by the benchmark."""

    RECEIPT = "receipt"
    INVOICE = "invoice"
    BANK_STATEMENT = "bank_statement"
    POLICY_DOCUMENT = "policy_document"
    MIXED_BUNDLE = "mixed_bundle"


class AttackType(StrEnum):
    """Visible benchmark instruction categories."""

    NONE = "none"
    INSTRUCTION_OVERRIDE = "instruction_override"
    PRIVACY_EXFILTRATION = "privacy_exfiltration"
    ROLE_CONFUSION = "role_confusion"
    FAKE_POLICY = "fake_policy"
    HIDDEN_ACTION_REQUEST = "hidden_action_request"
    DATA_POISONING = "data_poisoning"
    CONFLICTING_INSTRUCTIONS = "conflicting_instructions"
    AUTHORITY_IMPERSONATION = "authority_impersonation"
    FORMAT_INJECTION = "format_injection"


class Difficulty(StrEnum):
    """Benchmark example difficulty labels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class BenchmarkExample(BaseModel):
    """One synthetic document-understanding safety evaluation example."""

    id: str
    doc_type: DocumentType
    attack_type: AttackType
    difficulty: Difficulty
    document_text: str
    expected_task: str
    ground_truth_fields: dict[str, Any] = Field(default_factory=dict)
    private_fields: dict[str, Any] = Field(default_factory=dict)
    unsafe_instruction_present: bool
    embedded_instruction_span: str | None = None
    safe_behavior_description: str
    expected_output_constraints: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("id", "document_text")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        """Require non-empty identifiers and document text."""

        if not value or not value.strip():
            raise ValueError("field must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_attack_consistency(self) -> BenchmarkExample:
        """Validate relationships between attack fields."""

        if not self.unsafe_instruction_present and self.attack_type != AttackType.NONE:
            raise ValueError("attack_type must be none when unsafe_instruction_present is false")

        if self.attack_type != AttackType.NONE:
            if self.embedded_instruction_span is None or not self.embedded_instruction_span.strip():
                raise ValueError(
                    "embedded_instruction_span must be non-empty for adversarial examples"
                )

        return self


class ModelOutput(BaseModel):
    """Normalized model output used by the scorer."""

    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    refused: bool
    unsafe_action_recommended: bool
    private_information_revealed: bool
    followed_document_instruction: bool
    suspicious_instruction_detected: bool
    confidence: float = Field(ge=0.0, le=1.0)
    notes: str


class EvalResult(BaseModel):
    """Scored result for one model on one benchmark example."""

    run_id: str
    timestamp: datetime
    dataset_path: str
    id: str
    doc_type: DocumentType
    attack_type: AttackType
    difficulty: Difficulty
    model_name: str
    mitigation: str
    input_mode: str
    extraction_accuracy: float = Field(ge=0.0, le=1.0)
    prompt_injection_compliance: float = Field(ge=0.0, le=1.0)
    privacy_leakage: float = Field(ge=0.0, le=1.0)
    unsafe_action_rate: float = Field(ge=0.0, le=1.0)
    hallucination: float = Field(ge=0.0, le=1.0)
    over_refusal: float = Field(ge=0.0, le=1.0)
    suspicious_instruction_detection: float = Field(ge=0.0, le=1.0)
    safe_completion_rate: float = Field(ge=0.0, le=1.0)
    utility_safety_tradeoff: float = Field(ge=0.0, le=1.0)
    refused: bool
    unsafe_action_recommended: bool
    private_information_revealed: bool
    followed_document_instruction: bool
    suspicious_instruction_detected: bool
    notes: str
    error: str | None = None

    @field_validator("run_id", "dataset_path", "id", "model_name", "mitigation", "input_mode")
    @classmethod
    def require_non_empty_metadata(cls, value: str) -> str:
        """Require non-empty identifying metadata."""

        if not value or not value.strip():
            raise ValueError("field must be non-empty")
        return value
