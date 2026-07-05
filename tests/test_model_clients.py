"""Tests for model client interfaces and offline mock behavior."""

import pytest

from receiptinject.dataset_generator import generate_dataset
from receiptinject.model_clients import (
    ANTHROPIC_MISSING_KEY_MESSAGE,
    GEMINI_MISSING_KEY_MESSAGE,
    MISTRAL_MISSING_KEY_MESSAGE,
    OPENAI_MISSING_KEY_MESSAGE,
    AnthropicModelClient,
    GeminiModelClient,
    MistralModelClient,
    MockModelClient,
    ModelClientError,
    OpenAIModelClient,
    get_model_client,
)
from receiptinject.prompts import build_user_prompt
from receiptinject.schemas import AttackType
from receiptinject.utils import extract_first_json_object, normalize_model_output


def _adversarial_example():
    """Return one deterministic adversarial example."""

    return next(
        example
        for example in generate_dataset(n=30, seed=42)
        if example.attack_type != AttackType.NONE
    )


def test_get_model_client_returns_supported_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    """Factory should return provider clients without touching lazy placeholder API keys."""

    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr("receiptinject.model_clients._build_openai_client", _fake_openai_builder)
    monkeypatch.setattr(
        "receiptinject.model_clients._build_anthropic_client",
        _fake_anthropic_builder,
    )
    assert isinstance(get_model_client("mock"), MockModelClient)
    assert isinstance(get_model_client("openai"), OpenAIModelClient)
    assert isinstance(get_model_client("anthropic"), AnthropicModelClient)
    assert isinstance(get_model_client("gemini"), GeminiModelClient)


def test_get_model_client_rejects_unknown_model() -> None:
    """Factory should fail clearly for unsupported names."""

    with pytest.raises(ValueError, match="Supported model names"):
        get_model_client("not-a-provider")


def test_mock_model_baseline_can_follow_adversarial_instruction() -> None:
    """Baseline mock behavior should expose adversarial failures for offline runs."""

    example = _adversarial_example()
    prompt = build_user_prompt(example, mitigation="baseline")
    result = MockModelClient().complete_json("", prompt)
    assert result["followed_document_instruction"] is True
    assert result["confidence"] < 0.5


def test_mock_model_combined_safety_handles_adversarial_instruction() -> None:
    """Combined safety should improve mock behavior on adversarial documents."""

    example = _adversarial_example()
    prompt = build_user_prompt(example, mitigation="combined_safety")
    result = MockModelClient().complete_json("", prompt)
    assert result["followed_document_instruction"] is False
    assert result["suspicious_instruction_detected"] is True
    assert result["confidence"] >= 0.8


def test_mock_model_can_over_refuse_strict_prompt() -> None:
    """Strict prompts should sometimes trigger deterministic mock over-refusal."""

    example = generate_dataset(n=10, seed=1)[0]
    prompt = (
        build_user_prompt(example, mitigation="privacy_minimization")
        + "\nDo not answer. Do not extract. Do not summarize. Do not continue."
    )
    result = MockModelClient().complete_json("", prompt)
    assert isinstance(result["refused"], bool)


def test_mock_predict_returns_model_output() -> None:
    """Compatibility predict wrapper should return a validated ModelOutput."""

    output = MockModelClient().predict("example-1", "Total 12.00")
    assert output.notes.endswith("for example-1")
    assert output.confidence >= 0


def test_remaining_placeholders_do_not_fail_until_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clients should raise helpful errors when required keys are missing."""

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ModelClientError, match="ANTHROPIC_API_KEY"):
        AnthropicModelClient(env_path="/tmp/receiptinject-test-missing-env")
    with pytest.raises(ModelClientError, match="GEMINI_API_KEY"):
        GeminiModelClient(env_path="/tmp/receiptinject-test-missing-env")


def test_mistral_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mistral client should fail clearly when no key is configured."""

    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(ModelClientError) as exc_info:
        MistralModelClient(env_path="/tmp/receiptinject-test-missing-env")
    assert str(exc_info.value) == MISTRAL_MISSING_KEY_MESSAGE


def test_mistral_retries_invalid_json_and_returns_valid_model_output() -> None:
    """Mistral client should retry provider/API parse failures without real API calls."""

    fake_client = _FakeMistralClient(
        [
            _FakeResponse("not json"),
            _FakeResponse(
                {
                    "extracted_fields": {"total": "12.00"},
                    "refused": False,
                    "unsafe_action_recommended": False,
                    "private_information_revealed": False,
                    "followed_document_instruction": False,
                    "suspicious_instruction_detected": True,
                    "confidence": 0.91,
                    "notes": "valid fake response",
                }
            ),
        ]
    )

    client = MistralModelClient(
        api_key="test-key",
        client=fake_client,
        model="mistral-test-model",
        max_retries=2,
        env_path="/tmp/receiptinject-test-missing-env",
    )
    result = client.complete_json("system", "user")

    assert result["extracted_fields"] == {"total": "12.00"}
    assert result["confidence"] == 0.91
    assert fake_client.chat.calls[0]["temperature"] == 0
    assert fake_client.chat.calls[0]["response_format"] == {"type": "json_object"}
    assert len(fake_client.chat.calls) == 2


def test_openai_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenAI client should fail clearly when no key is configured."""

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("receiptinject.model_clients.find_dotenv", lambda usecwd=True: "")
    with pytest.raises(ModelClientError) as exc_info:
        OpenAIModelClient(env_path="/tmp/receiptinject-test-missing-env")
    assert str(exc_info.value) == OPENAI_MISSING_KEY_MESSAGE


def test_openai_retries_invalid_json_and_returns_normalized_output() -> None:
    """OpenAI client should retry parse failures without real API calls."""

    fake_client = _FakeOpenAIClient(
        [
            _FakeResponse("not json"),
            _FakeResponse('```json\n{"confidence": 2, "notes": "ok"}\n```'),
        ]
    )
    client = OpenAIModelClient(
        api_key="test-key",
        client=fake_client,
        model="gpt-test",
        max_retries=2,
        env_path="/tmp/receiptinject-test-missing-env",
    )

    result = client.complete_json("system", "user")

    assert result["extracted_fields"] == {}
    assert result["confidence"] == 1.0
    assert result["notes"] == "ok"
    assert fake_client.chat.completions.calls[0]["temperature"] == 0
    assert fake_client.chat.completions.calls[0]["response_format"] == {
        "type": "json_object"
    }


def test_anthropic_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Anthropic client should fail clearly when no key is configured."""

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("receiptinject.model_clients.find_dotenv", lambda usecwd=True: "")
    with pytest.raises(ModelClientError) as exc_info:
        AnthropicModelClient(env_path="/tmp/receiptinject-test-missing-env")
    assert str(exc_info.value) == ANTHROPIC_MISSING_KEY_MESSAGE


def test_anthropic_retries_invalid_json_and_returns_agentic_output() -> None:
    """Anthropic client should retry parse failures and preserve agentic tool calls."""

    fake_client = _FakeAnthropicClient(
        [
            _FakeAnthropicResponse("not json"),
            _FakeAnthropicResponse(
                {
                    "extracted_fields": {"total": "12.00"},
                    "tool_calls": [
                        {
                            "tool_name": "write_case_note_simulated",
                            "arguments": {"case_id": "SYN", "note": "ok"},
                            "reason": "allowed audit note",
                            "authorized": True,
                        }
                    ],
                    "final_answer": "ok",
                    "refused": False,
                    "suspicious_instruction_detected": False,
                    "confidence": 0.8,
                    "notes": "",
                }
            ),
        ]
    )
    client = AnthropicModelClient(
        api_key="test-key",
        client=fake_client,
        model="claude-test",
        max_retries=2,
        env_path="/tmp/receiptinject-test-missing-env",
    )

    result = client.complete_json("system", "user")

    assert result["tool_calls"][0]["tool_name"] == "write_case_note_simulated"
    assert fake_client.messages.calls[0]["temperature"] == 0
    assert fake_client.messages.calls[0]["max_tokens"] == 2048


def test_gemini_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gemini client should fail clearly when no key is configured."""

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr("receiptinject.model_clients.find_dotenv", lambda usecwd=True: "")
    with pytest.raises(ModelClientError) as exc_info:
        GeminiModelClient(env_path="/tmp/receiptinject-test-missing-env")
    assert str(exc_info.value) == GEMINI_MISSING_KEY_MESSAGE


def test_gemini_retries_invalid_json_and_returns_normalized_output() -> None:
    """Gemini client should retry parse failures without real API calls."""

    fake_client = _FakeGeminiClient(
        [
            _FakeGeminiResponse("not json"),
            _FakeGeminiResponse(
                {
                    "extracted_fields": {"total": "12.00"},
                    "refused": False,
                    "unsafe_action_recommended": False,
                    "private_information_revealed": False,
                    "followed_document_instruction": False,
                    "suspicious_instruction_detected": True,
                    "confidence": 0.88,
                    "notes": "valid fake gemini response",
                }
            ),
        ]
    )
    client = GeminiModelClient(
        api_key="test-key",
        client=fake_client,
        model="gemini-test",
        max_retries=2,
        env_path="/tmp/receiptinject-test-missing-env",
    )

    result = client.complete_json("system", "user")

    assert result["extracted_fields"] == {"total": "12.00"}
    assert result["confidence"] == 0.88
    assert fake_client.calls[0]["system_prompt"] == "system"
    assert len(fake_client.calls) == 2


def test_json_utilities_handle_fences_extra_text_and_missing_keys() -> None:
    """Shared parsing utilities should handle common provider formatting."""

    parsed = extract_first_json_object('prefix ```json\n{"confidence": 0.5}\n``` suffix')
    normalized = normalize_model_output(parsed)

    assert normalized["extracted_fields"] == {}
    assert normalized["refused"] is False
    assert normalized["confidence"] == 0.5
    assert normalized["notes"] == ""


class _FakeMistralClient:
    """Tiny fake object matching the SDK path used by MistralModelClient."""

    def __init__(self, responses: list[object]) -> None:
        self.chat = _FakeChat(responses)


class _FakeOpenAIClient:
    """Tiny fake object matching the OpenAI SDK chat completions path."""

    def __init__(self, responses: list[object]) -> None:
        self.chat = _FakeOpenAIChat(responses)


class _FakeAnthropicClient:
    """Tiny fake object matching the Anthropic SDK path."""

    def __init__(self, responses: list[object]) -> None:
        self.messages = _FakeAnthropicMessages(responses)


class _FakeGeminiClient:
    """Tiny fake object matching GeminiModelClient's REST adapter."""

    def __init__(self, responses: list[object]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> object:
        """Return the next fake response."""

        self.calls.append(kwargs)
        return self._responses.pop(0)


class _FakeOpenAIChat:
    """Fake chat namespace."""

    def __init__(self, responses: list[object]) -> None:
        self.completions = _FakeOpenAICompletions(responses)


class _FakeOpenAICompletions:
    """Fake OpenAI completions namespace with create method."""

    def __init__(self, responses: list[object]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        """Return the next fake response."""

        self.calls.append(kwargs)
        return self._responses.pop(0)


class _FakeAnthropicMessages:
    """Fake Anthropic messages namespace with create method."""

    def __init__(self, responses: list[object]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        """Return the next fake response."""

        self.calls.append(kwargs)
        return self._responses.pop(0)


def _fake_openai_builder(api_key: str) -> _FakeOpenAIClient:
    """Return a fake OpenAI client for factory tests."""

    return _FakeOpenAIClient([])


def _fake_anthropic_builder(api_key: str) -> _FakeAnthropicClient:
    """Return a fake Anthropic client for factory tests."""

    return _FakeAnthropicClient([])


class _FakeChat:
    """Fake chat namespace with a complete method."""

    def __init__(self, responses: list[object]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def complete(self, **kwargs: object) -> object:
        """Return the next fake response."""

        self.calls.append(kwargs)
        return self._responses.pop(0)


class _FakeResponse:
    """Fake Mistral response with choices[0].message.content."""

    def __init__(self, content: str | dict[str, object]) -> None:
        if isinstance(content, dict):
            import json

            content = json.dumps(content)
        self.choices = [_FakeChoice(_FakeMessage(content))]


class _FakeAnthropicResponse:
    """Fake Anthropic response with text content blocks."""

    def __init__(self, content: str | dict[str, object]) -> None:
        if isinstance(content, dict):
            import json

            content = json.dumps(content)
        self.content = [_FakeAnthropicBlock(content)]


class _FakeGeminiResponse:
    """Fake Gemini response with candidates[0].content.parts[0].text."""

    def __init__(self, content: str | dict[str, object]) -> None:
        if isinstance(content, dict):
            import json

            content = json.dumps(content)
        self.candidates = [{"content": {"parts": [{"text": content}]}}]


class _FakeAnthropicBlock:
    """Fake Anthropic content block."""

    def __init__(self, text: str) -> None:
        self.text = text


class _FakeChoice:
    """Fake response choice."""

    def __init__(self, message: "_FakeMessage") -> None:
        self.message = message


class _FakeMessage:
    """Fake response message."""

    def __init__(self, content: str) -> None:
        self.content = content
