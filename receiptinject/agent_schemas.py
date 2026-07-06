"""Typed contracts for agentic ReceiptInject tasks and traces."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from receiptinject.schemas import AttackType, Difficulty, DocumentType


class AgentTask(BaseModel):
    """One synthetic document-agent task with simulated tool access."""

    task_id: str
    document_id: str
    document_type: DocumentType
    attack_type: AttackType
    difficulty: Difficulty
    user_goal: str
    document_text: str
    allowed_tools: list[str] = Field(default_factory=list)
    disallowed_tools: list[str] = Field(default_factory=list)
    expected_safe_behavior: str
    ground_truth_fields: dict[str, Any] = Field(default_factory=dict)
    forbidden_actions: list[str] = Field(default_factory=list)

    @field_validator("task_id", "document_id", "user_goal", "document_text")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        """Require non-empty identifying and prompt text."""

        if not value or not value.strip():
            raise ValueError("field must be non-empty")
        return value


class ToolCall(BaseModel):
    """One proposed or executed simulated tool call."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str
    authorized: bool

    @field_validator("tool_name")
    @classmethod
    def require_tool_name(cls, value: str) -> str:
        """Require a non-empty tool name."""

        if not value or not value.strip():
            raise ValueError("tool_name must be non-empty")
        return value


class AgentTrace(BaseModel):
    """Full model trace for one agentic evaluation task."""

    task_id: str
    model_provider: str
    model_name: str
    mitigation: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    final_answer: str
    refused: bool
    suspicious_instruction_detected: bool
    error: str | None = None


class AgentScore(BaseModel):
    """Scored agentic behavior for one task."""

    unauthorized_tool_call: float = Field(ge=0.0, le=1.0)
    unsafe_tool_call_rate: float = Field(ge=0.0, le=1.0)
    tool_injection_success: float = Field(ge=0.0, le=1.0)
    correct_tool_use: float = Field(ge=0.0, le=1.0)
    unnecessary_tool_use: float = Field(ge=0.0, le=1.0)
    tool_argument_error: float = Field(default=0.0, ge=0.0, le=1.0)
    safe_task_completion: float = Field(ge=0.0, le=1.0)
    extraction_accuracy: float = Field(ge=0.0, le=1.0)
    suspicious_instruction_detection: float = Field(ge=0.0, le=1.0)
    notes: str = ""
