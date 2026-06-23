"""Estimated token/cost tracking for EvalGrid."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from evalgrid.schemas import ModelRequest, ModelResponse

DEFAULT_PRICES_PER_1M = {
    ("mistral", "mistral-large-latest"): {"input": 2.0, "output": 6.0},
    ("openai", "gpt-4o-mini"): {"input": 0.15, "output": 0.60},
    ("mock", "mock"): {"input": 0.0, "output": 0.0},
}


def estimate_tokens(text: str) -> int:
    """Rough token estimate when providers do not return usage."""

    if not text:
        return 0
    return max(1, len(text.split()) + len(text) // 20)


@dataclass
class CostTracker:
    """Track estimated tokens, latency, and cost."""

    prices_per_1m: dict[tuple[str, str], dict[str, float]] | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_seconds: float = 0.0
    estimated_cost: float = 0.0
    responses: int = 0

    def price_table(self) -> dict[tuple[str, str], dict[str, float]]:
        """Return configured or default price table."""

        return self.prices_per_1m or DEFAULT_PRICES_PER_1M

    def estimate_request_cost(self, request: ModelRequest, response: ModelResponse) -> float:
        """Estimate cost for one response, labeling it approximate."""

        input_tokens = response.input_tokens or estimate_tokens(
            f"{request.system_prompt}\n{request.user_prompt}"
        )
        output_tokens = response.output_tokens or estimate_tokens(str(response.raw_output or ""))
        prices = self.price_table().get(
            (request.model_provider, request.model_name),
            {"input": 0.0, "output": 0.0},
        )
        return (input_tokens / 1_000_000) * prices["input"] + (
            output_tokens / 1_000_000
        ) * prices["output"]

    def record(self, request: ModelRequest, response: ModelResponse) -> ModelResponse:
        """Record one response and return response with estimated usage/cost populated."""

        input_tokens = response.input_tokens or estimate_tokens(
            f"{request.system_prompt}\n{request.user_prompt}"
        )
        output_tokens = response.output_tokens or estimate_tokens(str(response.raw_output or ""))
        cost = response.cost_estimate or self.estimate_request_cost(request, response)
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.latency_seconds += response.latency_seconds
        self.estimated_cost += cost
        self.responses += 1
        return response.model_copy(
            update={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_estimate": cost,
            }
        )

    @property
    def average_latency(self) -> float:
        """Return average latency over recorded responses."""

        if self.responses == 0:
            return 0.0
        return self.latency_seconds / self.responses

    def save_summary(self, path: str | Path) -> Path:
        """Save an estimated cost summary Markdown file."""

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "\n".join(
                [
                    "# EvalGrid Estimated Cost Summary",
                    "",
                    "Costs are approximate estimates, not billing records.",
                    "",
                    f"Responses: {self.responses}",
                    f"Input tokens: {self.input_tokens}",
                    f"Output tokens: {self.output_tokens}",
                    f"Estimated cost: ${self.estimated_cost:.6f}",
                    f"Average latency seconds: {self.average_latency:.3f}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output_path
