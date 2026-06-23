"""Model provider abstraction for EvalGrid."""

from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from typing import Any

from dotenv import find_dotenv, load_dotenv

from evalgrid.cost_tracker import estimate_tokens
from evalgrid.schemas import ModelRequest, ModelResponse
from receiptinject.model_clients import (
    MistralModelClient,
    MockModelClient,
    ModelClientError,
    OpenAIModelClient,
)


class ProviderError(RuntimeError):
    """Raised when a provider cannot complete a request."""


class BaseProvider(ABC):
    """Common provider interface."""

    @abstractmethod
    def complete(self, request: ModelRequest, task_id: str) -> ModelResponse:
        """Complete one model request."""


class MockProvider(BaseProvider):
    """Offline deterministic provider."""

    def __init__(self) -> None:
        self.client = MockModelClient()

    def complete(self, request: ModelRequest, task_id: str) -> ModelResponse:
        """Return a deterministic mock response."""

        start = time.perf_counter()
        try:
            parsed = self.client.complete_json(request.system_prompt, request.user_prompt)
            raw_output: Any = parsed
            error = None
        except Exception as exc:  # noqa: BLE001 - normalize provider failures.
            parsed = None
            raw_output = None
            error = str(exc)
        latency = time.perf_counter() - start
        return ModelResponse(
            task_id=task_id,
            model_provider=request.model_provider,
            model_name=request.model_name,
            raw_output=raw_output,
            parsed_output=parsed,
            input_tokens=estimate_tokens(f"{request.system_prompt}\n{request.user_prompt}"),
            output_tokens=estimate_tokens(json.dumps(raw_output, sort_keys=True)),
            latency_seconds=latency,
            error=error,
        )


class MistralProvider(BaseProvider):
    """Mistral provider using ReceiptInject's MistralModelClient."""

    def __init__(self) -> None:
        dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path:
            load_dotenv(dotenv_path=dotenv_path, override=False)
        print(f"MISTRAL_API_KEY loaded: {'yes' if os.getenv('MISTRAL_API_KEY') else 'no'}")

    def complete(self, request: ModelRequest, task_id: str) -> ModelResponse:
        """Call Mistral and normalize output."""

        start = time.perf_counter()
        try:
            client = MistralModelClient(model=request.model_name)
            parsed = client.complete_json(request.system_prompt, request.user_prompt)
            raw_output: Any = parsed
            error = None
        except ModelClientError as exc:
            raise ProviderError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001 - SDK errors vary.
            raise ProviderError(str(exc)) from exc
        latency = time.perf_counter() - start
        return ModelResponse(
            task_id=task_id,
            model_provider=request.model_provider,
            model_name=request.model_name,
            raw_output=raw_output,
            parsed_output=parsed,
            input_tokens=estimate_tokens(f"{request.system_prompt}\n{request.user_prompt}"),
            output_tokens=estimate_tokens(json.dumps(raw_output, sort_keys=True)),
            latency_seconds=latency,
            error=error,
        )


class OpenAIProvider(BaseProvider):
    """OpenAI provider using ReceiptInject's OpenAIModelClient."""

    def __init__(self) -> None:
        dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path:
            load_dotenv(dotenv_path=dotenv_path, override=False)
        print(f"OPENAI_API_KEY loaded: {'yes' if os.getenv('OPENAI_API_KEY') else 'no'}")

    def complete(self, request: ModelRequest, task_id: str) -> ModelResponse:
        """Call OpenAI and normalize output."""

        start = time.perf_counter()
        try:
            client = OpenAIModelClient(model=request.model_name)
            parsed = client.complete_json(request.system_prompt, request.user_prompt)
            raw_output: Any = parsed
            error = None
        except ModelClientError as exc:
            raise ProviderError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001 - SDK errors vary.
            raise ProviderError(str(exc)) from exc
        latency = time.perf_counter() - start
        return ModelResponse(
            task_id=task_id,
            model_provider=request.model_provider,
            model_name=request.model_name,
            raw_output=raw_output,
            parsed_output=parsed,
            input_tokens=estimate_tokens(f"{request.system_prompt}\n{request.user_prompt}"),
            output_tokens=estimate_tokens(json.dumps(raw_output, sort_keys=True)),
            latency_seconds=latency,
            error=error,
        )


class PlaceholderProvider(BaseProvider):
    """Provider placeholder that fails only when selected."""

    def __init__(self, provider_name: str, env_key: str) -> None:
        self.provider_name = provider_name
        self.env_key = env_key

    def complete(self, request: ModelRequest, task_id: str) -> ModelResponse:
        """Raise a helpful placeholder error."""

        raise ProviderError(
            f"{self.provider_name} provider is not implemented yet. "
            f"Set {self.env_key} only after implementing this provider, or use mock/mistral."
        )


def get_provider(provider: str) -> BaseProvider:
    """Return provider implementation."""

    normalized = provider.strip().lower()
    if normalized == "mock":
        return MockProvider()
    if normalized == "mistral":
        return MistralProvider()
    if normalized == "openai":
        return OpenAIProvider()
    if normalized == "anthropic":
        return PlaceholderProvider("Anthropic", "ANTHROPIC_API_KEY")
    if normalized == "gemini":
        return PlaceholderProvider("Gemini", "GEMINI_API_KEY")
    raise ValueError(
        f"Unknown provider `{provider}`. Supported: mock, mistral, openai, anthropic, gemini"
    )
