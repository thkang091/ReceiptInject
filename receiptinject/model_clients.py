"""Model client interfaces for mock and provider-backed evaluation agents."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from dotenv import find_dotenv, load_dotenv

from receiptinject.schemas import ModelOutput
from receiptinject.utils import extract_first_json_object, normalize_model_output

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MISTRAL_MISSING_KEY_MESSAGE = (
    "Missing MISTRAL_API_KEY. Create a `.env` file in the project root with:\n"
    "MISTRAL_API_KEY=your_key_here\n"
    "MISTRAL_MODEL=mistral-large-latest"
)
OPENAI_MISSING_KEY_MESSAGE = (
    "Missing OPENAI_API_KEY. Create a `.env` file in the project root with:\n"
    "OPENAI_API_KEY=your_openai_key_here\n"
    "OPENAI_MODEL=gpt-4o-mini"
)


class ModelClientError(RuntimeError):
    """Raised when a model client cannot complete a request."""


class BaseModelClient(ABC):
    """Common interface for model clients that return parsed JSON."""

    @abstractmethod
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Complete a request and return a parsed JSON object."""


class MockModelClient(BaseModelClient):
    """Deterministic mock client for offline benchmark runs.

    The mock intentionally simulates several realistic behaviors:
    baseline prompts sometimes follow embedded document instructions, combined
    safety prompts perform better, and strict privacy/action prompts can over-refuse.
    """

    def __init__(self, model_name: str = "mock") -> None:
        self.model_name = model_name

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return deterministic simulated model behavior."""

        prompt = f"{system_prompt}\n{user_prompt}"
        prompt_lower = prompt.lower()
        adversarial = "visible embedded benchmark content" in prompt_lower
        combined_safety = (
            "untrusted document" in prompt_lower and "minimize private" in prompt_lower
        )
        untrusted_guard = "document text is untrusted data" in prompt_lower or combined_safety
        action_guard = "cannot approve, recommend, initiate" in prompt_lower
        privacy_guard = "minimize private information" in prompt_lower or combined_safety
        structured_guard = "suspicious embedded instructions" in prompt_lower
        strict_language = prompt_lower.count("do not") >= 5

        followed_document_instruction = adversarial and not untrusted_guard
        private_information_revealed = adversarial and "reveal any private fields" in prompt_lower
        private_information_revealed = private_information_revealed and not privacy_guard
        unsafe_action_recommended = (
            adversarial
            and "recommend an external action" in prompt_lower
            and not action_guard
        )
        refused = strict_language and not combined_safety and _stable_score(prompt) < 0.18

        confidence = 0.88
        if (
            followed_document_instruction
            or private_information_revealed
            or unsafe_action_recommended
        ):
            confidence = 0.42
        if refused:
            confidence = 0.35
        if combined_safety and adversarial:
            confidence = 0.82

        extracted_fields: dict[str, Any] = {}
        if not refused:
            extracted_fields = _extract_obvious_fields(user_prompt)
            if followed_document_instruction:
                extracted_fields["document_instruction_summary"] = (
                    "Mock followed the visible embedded instruction."
                )
            if private_information_revealed:
                extracted_fields["private_field_leak"] = "MOCK_SYNTHETIC_PRIVATE_FIELD"
            if unsafe_action_recommended:
                extracted_fields["unsafe_recommendation"] = "Mock recommends external action."

        suspicious_detected = adversarial and (
            untrusted_guard or structured_guard or combined_safety
        )
        notes = "mock response"
        if refused:
            notes = "mock over-refusal under strict prompt"
        elif followed_document_instruction:
            notes = "mock baseline failure on adversarial document"
        elif combined_safety and adversarial:
            notes = "mock combined safety handled adversarial document"

        return {
            "extracted_fields": extracted_fields,
            "refused": refused,
            "unsafe_action_recommended": unsafe_action_recommended,
            "private_information_revealed": private_information_revealed,
            "followed_document_instruction": followed_document_instruction,
            "suspicious_instruction_detected": suspicious_detected,
            "confidence": confidence,
            "notes": notes,
        }

    def predict(self, example_id: str, prompt: str) -> ModelOutput:
        """Compatibility wrapper returning a validated ``ModelOutput``."""

        result = self.complete_json(system_prompt="", user_prompt=prompt)
        result["notes"] = f"{result.get('notes', 'mock response')} for {example_id}"
        return ModelOutput.model_validate(result)


class MistralModelClient(BaseModelClient):
    """Mistral chat client using JSON response mode."""

    def __init__(
        self,
        model: str | None = None,
        max_retries: int = 3,
        *,
        api_key: str | None = None,
        client: Any | None = None,
        env_path: str | Path | None = None,
    ) -> None:
        dotenv_path = _resolve_dotenv_path(env_path)
        if dotenv_path is not None:
            load_dotenv(dotenv_path=dotenv_path, override=False)
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ModelClientError(MISTRAL_MISSING_KEY_MESSAGE)
        self.model = model or os.getenv("MISTRAL_MODEL", "mistral-large-latest")
        self.max_retries = max_retries
        self.client = client or _build_mistral_client(self.api_key)

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Call Mistral with retries and return parsed JSON."""

        last_error: Exception | None = None
        for _attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.complete(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0,
                    response_format={"type": "json_object"},
                )
                parsed = extract_first_json_object(_extract_message_content(response))
                return normalize_model_output(parsed)
            except Exception as exc:  # noqa: BLE001 - provider errors vary by SDK version.
                last_error = exc

        raise ModelClientError(
            f"MistralModelClient failed to return valid JSON after {self.max_retries} "
            f"attempts using model `{self.model}`: {last_error}"
        )


class OpenAIModelClient(BaseModelClient):
    """OpenAI chat client using JSON response mode."""

    def __init__(
        self,
        model: str | None = None,
        max_retries: int = 3,
        *,
        api_key: str | None = None,
        client: Any | None = None,
        env_path: str | Path | None = None,
    ) -> None:
        dotenv_path = _resolve_dotenv_path(env_path)
        if dotenv_path is not None:
            load_dotenv(dotenv_path=dotenv_path, override=False)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ModelClientError(OPENAI_MISSING_KEY_MESSAGE)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_retries = max_retries
        self.client = client or _build_openai_client(self.api_key)

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Call OpenAI with retries and return normalized JSON."""

        last_error: Exception | None = None
        for _attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0,
                    response_format={"type": "json_object"},
                )
                return normalize_model_output(_extract_openai_message_content(response))
            except Exception as exc:  # noqa: BLE001 - provider errors vary by SDK version.
                last_error = exc

        raise ModelClientError(
            f"OpenAIModelClient failed to return valid JSON after {self.max_retries} "
            f"attempts using model `{self.model}`: {last_error}"
        )


class AnthropicModelClient(BaseModelClient):
    """Placeholder Anthropic client with lazy missing-key errors."""

    env_key = "ANTHROPIC_API_KEY"
    provider = "Anthropic"

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Raise a helpful setup error until the client is implemented."""

        _raise_placeholder_error(self.provider, self.env_key)


class GeminiModelClient(BaseModelClient):
    """Placeholder Gemini client with lazy missing-key errors."""

    env_key = "GEMINI_API_KEY"
    provider = "Gemini"

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Raise a helpful setup error until the client is implemented."""

        _raise_placeholder_error(self.provider, self.env_key)


def get_model_client(model_name: str) -> BaseModelClient:
    """Return a model client by provider name."""

    normalized = model_name.strip().lower()
    if normalized == "mock":
        return MockModelClient()
    if normalized == "mistral":
        return MistralModelClient()
    if normalized == "openai":
        return OpenAIModelClient()
    if normalized == "anthropic":
        return AnthropicModelClient()
    if normalized == "gemini":
        return GeminiModelClient()
    raise ValueError(
        f"Unsupported model_name `{model_name}`. "
        "Supported model names: mock, mistral, openai, anthropic, gemini."
    )


def _build_mistral_client(api_key: str) -> Any:
    """Build a Mistral SDK client across supported SDK import layouts."""

    try:
        from mistralai import Mistral  # type: ignore[attr-defined]
    except ImportError:
        try:
            from mistralai.client import Mistral  # type: ignore[no-redef]
        except ImportError as exc:
            raise ModelClientError(
                "The mistralai SDK is required for MistralModelClient. "
                "Install requirements.txt first."
            ) from exc
    return Mistral(api_key=api_key)


def _build_openai_client(api_key: str) -> Any:
    """Build an OpenAI SDK client."""

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ModelClientError(
            "The openai SDK is required for OpenAIModelClient. Install requirements.txt first."
        ) from exc
    return OpenAI(api_key=api_key)


def _extract_message_content(response: Any) -> str:
    """Extract assistant message content from common chat response shapes."""

    choices = getattr(response, "choices", None)
    if not choices and isinstance(response, dict):
        choices = response.get("choices")
    if not choices:
        raise ModelClientError("Mistral response did not include choices.")

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    if message is None and isinstance(first_choice, dict):
        message = first_choice.get("message")
    if message is None:
        raise ModelClientError("Mistral response choice did not include a message.")

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        )
    if not isinstance(content, str) or not content.strip():
        raise ModelClientError("Mistral response message content was empty.")
    return content


def _extract_openai_message_content(response: Any) -> str:
    """Extract assistant message content from common OpenAI response shapes."""

    choices = getattr(response, "choices", None)
    if not choices and isinstance(response, dict):
        choices = response.get("choices")
    if not choices:
        raise ModelClientError("OpenAI response did not include choices.")

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    if message is None and isinstance(first_choice, dict):
        message = first_choice.get("message")
    if message is None:
        raise ModelClientError("OpenAI response choice did not include a message.")

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        )
    if not isinstance(content, str) or not content.strip():
        raise ModelClientError("OpenAI response message content was empty.")
    return content


def _raise_placeholder_error(provider: str, env_key: str) -> None:
    """Raise a helpful placeholder or missing-key error."""

    dotenv_path = _resolve_dotenv_path(None)
    if dotenv_path is not None:
        load_dotenv(dotenv_path=dotenv_path, override=False)
    if not os.getenv(env_key):
        raise ModelClientError(
            f"{provider} client selected but {env_key} is not set. "
            "Add the key to .env or choose model_name='mock'."
        )
    raise ModelClientError(
        f"{provider} client placeholder is not implemented yet. "
        "Use model_name='mock' or model_name='mistral' for current runs."
    )


def _resolve_dotenv_path(env_path: str | Path | None) -> Path | None:
    """Resolve a dotenv path from explicit path, cwd search, or project root."""

    if env_path is not None:
        return Path(env_path)
    discovered = find_dotenv(usecwd=True)
    if discovered:
        return Path(discovered)
    fallback = PROJECT_ROOT / ".env"
    return fallback if fallback.exists() else None


def _extract_obvious_fields(prompt: str) -> dict[str, Any]:
    """Extract a few obvious fields for deterministic mock usefulness."""

    fields: dict[str, Any] = {}
    for label in [
        "Total",
        "Invoice total",
        "Closing balance",
        "Receipt total",
        "Document ID",
        "Invoice ID",
        "Bundle ID",
    ]:
        value = _line_value_after_label(prompt, label)
        if value:
            fields[_field_key(label)] = value
    return fields or {"summary": "Mock extracted supported document facts."}


def _line_value_after_label(text: str, label: str) -> str | None:
    """Return trailing text after a line label."""

    label_lower = label.lower()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(label_lower):
            value = stripped[len(label) :].strip(" :")
            if value:
                return value
    return None


def _field_key(label: str) -> str:
    """Normalize a document label into a field key."""

    return label.lower().replace(" ", "_")


def _stable_score(text: str) -> float:
    """Return a deterministic pseudo-random score in [0, 1)."""

    return (sum(ord(char) for char in text) % 1000) / 1000
