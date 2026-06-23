"""Tests for EvalGrid cost tracking."""

from pathlib import Path

from evalgrid.cost_tracker import CostTracker, estimate_tokens
from evalgrid.schemas import ModelRequest, ModelResponse


def test_estimate_tokens_is_positive_for_text() -> None:
    """Token estimates should be positive for non-empty text."""

    assert estimate_tokens("hello world") > 0
    assert estimate_tokens("") == 0


def test_cost_tracker_records_estimated_cost(tmp_path: Path) -> None:
    """Cost tracker should aggregate approximate tokens, cost, and latency."""

    request = ModelRequest(
        model_provider="mock",
        model_name="mock",
        system_prompt="system",
        user_prompt="user",
    )
    response = ModelResponse(
        task_id="t1",
        model_provider="mock",
        model_name="mock",
        raw_output={"ok": True},
        parsed_output={"ok": True},
        latency_seconds=0.25,
    )
    tracker = CostTracker()
    updated = tracker.record(request, response)

    assert updated.input_tokens > 0
    assert tracker.responses == 1
    assert tracker.average_latency == 0.25
    path = tracker.save_summary(tmp_path / "cost.md")
    assert "Estimated Cost Summary" in path.read_text(encoding="utf-8")
