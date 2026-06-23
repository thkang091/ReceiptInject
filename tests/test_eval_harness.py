"""Starter tests for the mock evaluation harness and repository scaffold."""

import csv
import importlib
import json
from pathlib import Path

from receiptinject.dataset_generator import generate_dataset, save_jsonl
from receiptinject.eval_harness import (
    EvalHarnessConfig,
    load_eval_inputs,
    run_experiment,
    run_mock_eval,
)


def test_run_mock_eval_returns_predictions() -> None:
    """The placeholder harness should produce one prediction per receipt."""

    receipts = generate_dataset(count=2, seed=0)
    predictions = run_mock_eval(receipts)
    assert len(predictions) == 2


def test_run_experiment_mock_mode_writes_results_and_raw_outputs(tmp_path: Path) -> None:
    """Mock evaluation should write scored CSV rows and raw JSONL records."""

    data_path = tmp_path / "examples.jsonl"
    output_path = tmp_path / "results.csv"
    raw_path = tmp_path / "raw_outputs.jsonl"
    save_jsonl(generate_dataset(n=6, seed=4), data_path)

    results = run_experiment(
        EvalHarnessConfig(
            data_path=data_path,
            model_name="mock",
            mitigation="baseline",
            output_path=output_path,
            raw_output_path=raw_path,
            metadata_path=tmp_path / "run_metadata.json",
            limit=3,
            seed=123,
        )
    )

    assert len(results) == 3
    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    assert rows[0]["model_name"] == "mock"
    assert rows[0]["mitigation"] == "baseline"
    assert "extraction_accuracy" in rows[0]

    raw_records = [
        json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(raw_records) == 3
    assert raw_records[0]["raw_output"] is not None

    metadata = json.loads((tmp_path / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["dataset_file"] == str(data_path)
    assert metadata["number_of_examples_attempted"] == 3
    assert metadata["model"] == "mock"


def test_run_experiment_resume_skips_completed_rows(tmp_path: Path) -> None:
    """Resume mode should avoid re-running already completed examples."""

    data_path = tmp_path / "examples.jsonl"
    output_path = tmp_path / "results.csv"
    raw_path = tmp_path / "raw_outputs.jsonl"
    save_jsonl(generate_dataset(n=5, seed=5), data_path)
    config = EvalHarnessConfig(
        data_path=data_path,
        model_name="mock",
        mitigation="combined_safety",
        output_path=output_path,
        raw_output_path=raw_path,
        metadata_path=tmp_path / "run_metadata.json",
        limit=2,
    )

    first = run_experiment(config)
    second = run_experiment(
        EvalHarnessConfig(
            data_path=data_path,
            model_name="mock",
            mitigation="combined_safety",
            output_path=output_path,
            raw_output_path=raw_path,
            metadata_path=tmp_path / "run_metadata.json",
            limit=2,
            resume=True,
        )
    )

    assert len(first) == 2
    assert second == []
    with output_path.open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 2


def test_load_eval_inputs_supports_ocr_records_with_example_metadata(tmp_path: Path) -> None:
    """OCR mode should accept rows with full example metadata and OCR text."""

    example = generate_dataset(n=1, seed=6)[0]
    ocr_path = tmp_path / "ocr.jsonl"
    record = {
        "example": example.model_dump(mode="json"),
        "ocr_markdown": "OCR text replacement",
    }
    ocr_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    inputs = load_eval_inputs(ocr_path, input_mode="ocr")
    assert len(inputs) == 1
    assert inputs[0].example.id == example.id
    assert inputs[0].input_text == "OCR text replacement"


def test_expected_scaffold_files_exist() -> None:
    """Core documentation and configuration files should exist."""

    root = Path(__file__).resolve().parents[1]
    expected = [
        "README.md",
        "benchmark_spec.md",
        "dataset_card.md",
        "responsible_use.md",
        "research_memo.md",
        "paper/ReceiptInject_Report.md",
        "configs/default.yaml",
        "configs/cheap_mistral_test.yaml",
        "configs/mock_full_run.yaml",
    ]
    for relative_path in expected:
        assert (root / relative_path).exists()


def test_cli_scripts_import_without_api_keys() -> None:
    """CLI modules should import cleanly without requiring real provider API keys."""

    modules = [
        "scripts.generate_dataset",
        "scripts.validate_dataset",
        "scripts.render_documents",
        "scripts.run_ocr",
        "scripts.run_eval",
        "scripts.summarize_results",
        "scripts.make_figures",
        "scripts.export_failure_cases",
    ]
    for module_name in modules:
        module = importlib.import_module(module_name)
        assert module is not None
