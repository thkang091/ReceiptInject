"""Tests for PDF/PNG document rendering."""

import json
from pathlib import Path

from receiptinject.dataset_generator import generate_dataset
from receiptinject.render_documents import MANIFEST_NAME, render_dataset, render_example


def test_render_example_writes_pdf_and_png(tmp_path: Path) -> None:
    """Rendering one example should create non-empty PDF and PNG files."""

    example = generate_dataset(n=10, seed=21)[0]
    rendered = render_example(example, tmp_path)
    pdf_path = Path(rendered.pdf_path)
    image_path = Path(rendered.image_path)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 100
    assert image_path.exists()
    assert image_path.stat().st_size > 100
    assert rendered.id == example.id
    assert rendered.doc_type == example.doc_type.value


def test_render_dataset_writes_manifest(tmp_path: Path) -> None:
    """Rendering a dataset should write a JSONL manifest with artifact paths."""

    examples = generate_dataset(n=8, seed=22)
    rendered = render_dataset(examples, tmp_path, limit=3)
    manifest_path = tmp_path / MANIFEST_NAME

    assert len(rendered) == 3
    assert manifest_path.exists()
    records = [
        json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(records) == 3
    assert set(records[0]) == {
        "id",
        "doc_type",
        "attack_type",
        "difficulty",
        "pdf_path",
        "image_path",
        "document_text",
        "example",
    }
    assert Path(records[0]["pdf_path"]).exists()
    assert Path(records[0]["image_path"]).exists()
