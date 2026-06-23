"""Tests for OCR clients and manifest OCR runner."""

import json
from pathlib import Path

from receiptinject.ocr_client import (
    BaseOCRClient,
    OCRClientError,
    OCRManifestItem,
    load_manifest,
    ocr_manifest_item,
    run_ocr_manifest,
)


class FailingOCRClient(BaseOCRClient):
    """OCR client that always fails for error-row tests."""

    def ocr_file(self, item: OCRManifestItem) -> str:
        """Raise a deterministic OCR failure."""

        raise OCRClientError(f"boom for {item.id}")


def test_load_manifest_prefers_pdf_path(tmp_path: Path) -> None:
    """Manifest loading should use PDFs before images."""

    pdf = tmp_path / "doc.pdf"
    png = tmp_path / "doc.png"
    pdf.write_bytes(b"%PDF fake")
    png.write_bytes(b"PNG fake")
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "id": "ex-1",
                "pdf_path": str(pdf),
                "image_path": str(png),
                "document_text": "original text",
                "example": {"id": "ex-1"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    items = load_manifest(manifest)
    assert items[0].source_file == pdf
    assert items[0].document_text == "original text"
    assert items[0].example == {"id": "ex-1"}


def test_mock_ocr_run_copies_manifest_document_text(tmp_path: Path) -> None:
    """Mock OCR should copy original document text when available."""

    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF fake")
    manifest = tmp_path / "manifest.jsonl"
    output = tmp_path / "ocr.jsonl"
    manifest.write_text(
        json.dumps({"id": "ex-1", "pdf_path": str(pdf), "document_text": "SOURCE TEXT"})
        + "\n",
        encoding="utf-8",
    )

    results = run_ocr_manifest(manifest, output, mock=True)
    assert len(results) == 1
    assert results[0].ocr_markdown == "SOURCE TEXT"
    assert results[0].ocr_error is None

    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert records[0]["id"] == "ex-1"
    assert records[0]["ocr_markdown"] == "SOURCE TEXT"


def test_ocr_manifest_item_captures_per_document_errors(tmp_path: Path) -> None:
    """One OCR failure should become an output row, not an exception."""

    item = OCRManifestItem(id="ex-2", source_file=tmp_path / "missing.pdf")
    result = ocr_manifest_item(FailingOCRClient(), item)
    assert result.id == "ex-2"
    assert result.ocr_markdown == ""
    assert "boom for ex-2" in (result.ocr_error or "")
