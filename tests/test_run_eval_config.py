"""Tests for YAML config support in scripts/run_eval.py."""

import argparse
from pathlib import Path

import pytest

from scripts.run_eval import _load_config, _merge_config_and_args


def test_load_config_reads_yaml_mapping(tmp_path) -> None:
    """YAML experiment configs should load as dictionaries."""

    path = tmp_path / "config.yaml"
    path.write_text("dataset_path: data/examples.jsonl\nmodel: mock\n", encoding="utf-8")
    assert _load_config(path)["model"] == "mock"


def test_merge_config_and_args_uses_config_defaults() -> None:
    """Config values should populate the run config when CLI args are omitted."""

    args = argparse.Namespace(
        data=None,
        model=None,
        mitigation=None,
        input_mode=None,
        limit=None,
        sleep=None,
        output=None,
        raw_output=None,
        resume=None,
        seed=None,
        run_id=None,
        fresh=None,
    )
    merged = _merge_config_and_args(
        {
            "dataset_path": "data/config.jsonl",
            "model": "mock",
            "mitigation": "combined_safety",
            "input_mode": "text",
            "limit": 7,
            "sleep": 0.25,
            "output_path": "results/config.csv",
            "raw_output_path": "results/config.jsonl",
            "resume": True,
            "seed": 5,
        },
        args,
    )
    assert merged["dataset_path"] == "data/config.jsonl"
    assert merged["limit"] == 7
    assert merged["resume"] is True


def test_merge_config_and_args_cli_overrides_config() -> None:
    """Explicit CLI args should override YAML values."""

    args = argparse.Namespace(
        data="data/cli.jsonl",
        model="mock",
        mitigation="baseline",
        input_mode="ocr",
        limit=3,
        sleep=0.0,
        output="results/cli.csv",
        raw_output="results/cli_raw.jsonl",
        resume=False,
        seed=99,
        run_id=None,
        fresh=None,
    )
    merged = _merge_config_and_args(
        {
            "dataset_path": "data/config.jsonl",
            "model": "mistral",
            "mitigation": "combined_safety",
            "input_mode": "text",
            "limit": 10,
            "sleep": 1.0,
            "output_path": "results/config.csv",
            "raw_output_path": "results/config_raw.jsonl",
            "resume": True,
            "seed": 1,
        },
        args,
    )
    assert merged["dataset_path"] == "data/cli.jsonl"
    assert merged["model"] == "mock"
    assert merged["input_mode"] == "ocr"
    assert merged["resume"] is False
    assert merged["seed"] == 99


def test_merge_config_accepts_evalgrid_style_real_provider_config() -> None:
    """EvalGrid-style Gemini configs should not silently resolve to mock."""

    args = argparse.Namespace(
        data=None,
        model=None,
        mitigation=None,
        input_mode=None,
        limit=None,
        sleep=None,
        output=None,
        raw_output=None,
        resume=None,
        seed=None,
        run_id=None,
        fresh=None,
    )
    merged = _merge_config_and_args(
        {
            "benchmark_name": "receiptinject",
            "dataset_path": "data/examples_300.jsonl",
            "provider": "gemini",
            "model_name": "gemini-3.1-flash-lite",
            "mitigation": "baseline_minimal",
            "limit": 300,
            "sleep_between_requests": 8.0,
            "output_results_path": "results/evalgrid_gemini_300_baseline_results.csv",
            "raw_outputs_path": "results/evalgrid_gemini_300_baseline_raw_outputs.jsonl",
            "metadata_path": "results/evalgrid_gemini_300_baseline_metadata.json",
            "resume": True,
        },
        args,
    )

    assert merged["model"] == "gemini"
    assert merged["provider_model_name"] == "gemini-3.1-flash-lite"
    assert merged["output_path"] == "results/evalgrid_gemini_300_baseline_results.csv"
    assert merged["raw_output_path"] == (
        "results/evalgrid_gemini_300_baseline_raw_outputs.jsonl"
    )
    assert merged["sleep"] == 8.0
    assert merged["model"] != "mock"


@pytest.mark.parametrize(
    ("config_path", "provider", "provider_model_name", "path_marker"),
    [
        (
            "configs/evalgrid_mistral_300_baseline.yaml",
            "mistral",
            "mistral-large-latest",
            "mistral_300_baseline",
        ),
        (
            "configs/evalgrid_mistral_300_safety_schema.yaml",
            "mistral",
            "mistral-large-latest",
            "mistral_300_safety_schema",
        ),
        (
            "configs/evalgrid_openai_300_baseline.yaml",
            "openai",
            "gpt-4o-mini",
            "openai_300_baseline",
        ),
        (
            "configs/evalgrid_openai_300_safety_schema.yaml",
            "openai",
            "gpt-4o-mini",
            "openai_300_safety_schema",
        ),
    ],
)
def test_run_eval_resolves_openai_mistral_300_configs_to_real_provider(
    config_path: str,
    provider: str,
    provider_model_name: str,
    path_marker: str,
) -> None:
    """run_eval should honor OpenAI/Mistral 300 config provider and paths."""

    args = argparse.Namespace(
        data=None,
        model=None,
        mitigation=None,
        input_mode=None,
        limit=None,
        sleep=None,
        output=None,
        raw_output=None,
        resume=None,
        seed=None,
        run_id=None,
        fresh=None,
    )
    merged = _merge_config_and_args(_load_config(Path(config_path)), args)

    assert merged["model"] == provider
    assert merged["provider_model_name"] == provider_model_name
    assert merged["model"] != "mock"
    assert path_marker in merged["output_path"]
    assert path_marker in merged["raw_output_path"]
    assert path_marker in merged["metadata_path"]


def test_merge_config_rejects_conflicting_model_and_provider() -> None:
    """A real-provider config should fail instead of falling back to mock."""

    args = argparse.Namespace(
        data=None,
        model=None,
        mitigation=None,
        input_mode=None,
        limit=None,
        sleep=None,
        output=None,
        raw_output=None,
        resume=None,
        seed=None,
        run_id=None,
        fresh=None,
    )
    with pytest.raises(ValueError, match="conflicting `model` and `provider`"):
        _merge_config_and_args(
            {
                "dataset_path": "data/examples_300.jsonl",
                "model": "mock",
                "provider": "gemini",
                "model_name": "gemini-3.1-flash-lite",
                "mitigation": "baseline_minimal",
            },
            args,
        )


def test_load_config_rejects_non_mapping(tmp_path) -> None:
    """Config files should be YAML mappings."""

    path = tmp_path / "config.yaml"
    path.write_text("- not\n- mapping\n", encoding="utf-8")
    with pytest.raises(ValueError, match="YAML mapping"):
        _load_config(path)
