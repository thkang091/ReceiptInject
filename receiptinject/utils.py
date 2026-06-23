"""Shared parsing utilities for provider JSON outputs."""

from __future__ import annotations

import json
from typing import Any

from receiptinject.schemas import ModelOutput


def strip_markdown_fences(text: str) -> str:
    """Remove common markdown code fences around model JSON."""

    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def extract_first_json_object(text: str) -> dict[str, Any]:
    """Extract and parse the first valid JSON object from text."""

    cleaned = strip_markdown_fences(text)
    decoder = json.JSONDecoder()
    for index, char in enumerate(cleaned):
        if char != "{":
            continue
        try:
            parsed, _end = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("Could not parse a JSON object from model output.")


def normalize_model_output(obj: Any) -> dict[str, Any]:
    """Normalize provider output into the ReceiptInject ModelOutput schema."""

    if isinstance(obj, str):
        obj = extract_first_json_object(obj)
    if not isinstance(obj, dict):
        raise ValueError("Model output must be a JSON object.")

    confidence = obj.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    normalized = {
        "extracted_fields": obj.get("extracted_fields") or {},
        "refused": bool(obj.get("refused", False)),
        "unsafe_action_recommended": bool(obj.get("unsafe_action_recommended", False)),
        "private_information_revealed": bool(obj.get("private_information_revealed", False)),
        "followed_document_instruction": bool(obj.get("followed_document_instruction", False)),
        "suspicious_instruction_detected": bool(
            obj.get("suspicious_instruction_detected", False)
        ),
        "confidence": min(max(confidence, 0.0), 1.0),
        "notes": str(obj.get("notes", "")),
    }
    if not isinstance(normalized["extracted_fields"], dict):
        normalized["extracted_fields"] = {}
    return ModelOutput.model_validate(normalized).model_dump(mode="json")
