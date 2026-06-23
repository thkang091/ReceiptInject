"""Tests for YAML config support in scripts/run_eval.py."""

import argparse

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


def test_load_config_rejects_non_mapping(tmp_path) -> None:
    """Config files should be YAML mappings."""

    path = tmp_path / "config.yaml"
    path.write_text("- not\n- mapping\n", encoding="utf-8")
    with pytest.raises(ValueError, match="YAML mapping"):
        _load_config(path)
