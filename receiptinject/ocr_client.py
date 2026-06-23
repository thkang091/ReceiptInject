"""OCR clients and manifest-driven OCR helpers for ReceiptInject."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class OCRClientError(RuntimeError):
    """Raised when an OCR client cannot process a document."""


class OCRResult(BaseModel):
    """OCR output row persisted to JSONL."""

    id: str
    source_file: str
    ocr_markdown: str
    ocr_error: str | None
    timestamp: str
    example: dict[str, Any] | None = None


@dataclass(frozen=True)
class OCRManifestItem:
    """Rendered-document manifest row."""

    id: str
    source_file: Path
    document_text: str | None = None
    example: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None


class BaseOCRClient:
    """Common OCR client interface."""

    def ocr_file(self, item: OCRManifestItem) -> str:
        """Return OCR markdown for one manifest item."""

        raise NotImplementedError


class MockOCRClient(BaseOCRClient):
    """Offline OCR client that returns original document text when available."""

    def ocr_file(self, item: OCRManifestItem) -> str:
        """Return manifest-provided original text or a clear fallback string."""

        if item.document_text:
            return item.document_text
        return (
            f"MOCK OCR FALLBACK for {item.id}\n"
            f"Source file: {item.source_file}\n"
            "Original document_text was not available in the manifest."
        )


class MistralOCRClient(BaseOCRClient):
    """Mistral OCR client using the `mistral-ocr-latest` model."""

    def __init__(
        self,
        model: str = "mistral-ocr-latest",
        max_retries: int = 3,
    ) -> None:
        load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise OCRClientError(
                "MISTRAL_API_KEY is required for Mistral OCR. "
                "Add it to .env or use --mock."
            )
        self.model = model
        self.max_retries = max_retries
        self.client = _build_mistral_client(self.api_key)

    def ocr_file(self, item: OCRManifestItem) -> str:
        """Upload a PDF/image to Mistral OCR and return page markdown."""

        last_error: Exception | None = None
        for _attempt in range(1, self.max_retries + 1):
            try:
                file_id = self._upload_for_ocr(item.source_file)
                signed_url = self._signed_url(file_id)
                response = self.client.ocr.process(
                    model=self.model,
                    document={
                        "type": "document_url",
                        "document_url": signed_url,
                        "document_name": item.source_file.name,
                    },
                    include_image_base64=False,
                    table_format="markdown",
                    extract_header=True,
                    extract_footer=True,
                )
                return _ocr_response_to_markdown(response)
            except Exception as exc:  # noqa: BLE001 - SDK/network errors vary.
                last_error = exc
                time.sleep(0.5)

        raise OCRClientError(
            f"Mistral OCR failed for {item.id} after {self.max_retries} attempts: {last_error}"
        )

    def _upload_for_ocr(self, path: Path) -> str:
        """Upload a document for OCR and return its file ID."""

        file_model = _mistral_file_model()
        with path.open("rb") as handle:
            uploaded = self.client.files.upload(
                file=file_model(
                    fileName=path.name,
                    content=handle,
                    content_type=_content_type(path),
                ),
                purpose="ocr",
            )
        file_id = getattr(uploaded, "id", None)
        if file_id is None and isinstance(uploaded, dict):
            file_id = uploaded.get("id")
        if not file_id:
            raise OCRClientError("Mistral file upload did not return a file ID.")
        return str(file_id)

    def _signed_url(self, file_id: str) -> str:
        """Return a signed URL for an uploaded OCR file."""

        signed = self.client.files.get_signed_url(file_id=file_id)
        url = getattr(signed, "url", None)
        if url is None and isinstance(signed, dict):
            url = signed.get("url")
        if not url:
            raise OCRClientError("Mistral signed URL response did not include a URL.")
        return str(url)


def load_manifest(path: str | Path, limit: int | None = None) -> list[OCRManifestItem]:
    """Load rendered-document manifest rows, preferring PDFs over images."""

    manifest_path = Path(path)
    items: list[OCRManifestItem] = []
    with manifest_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            source_file = _source_file_from_manifest(record)
            items.append(
                OCRManifestItem(
                    id=record["id"],
                    source_file=source_file,
                    document_text=record.get("document_text"),
                    example=record.get("example"),
                    raw=record,
                )
            )
            if limit is not None and len(items) >= limit:
                break
    return items


def run_ocr_manifest(
    manifest_path: str | Path,
    output_path: str | Path,
    *,
    mock: bool = False,
    limit: int | None = None,
    sleep_seconds: float = 0.0,
) -> list[OCRResult]:
    """Run OCR over a rendered-document manifest and save JSONL results."""

    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative when provided")
    items = load_manifest(manifest_path, limit=limit)
    client: BaseOCRClient = MockOCRClient() if mock else MistralOCRClient()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    results: list[OCRResult] = []
    with output.open("w", encoding="utf-8") as handle:
        for item in items:
            result = ocr_manifest_item(client, item)
            results.append(result)
            handle.write(json.dumps(result.model_dump(mode="json"), sort_keys=True) + "\n")
            handle.flush()
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
    return results


def ocr_manifest_item(client: BaseOCRClient, item: OCRManifestItem) -> OCRResult:
    """OCR one manifest item without raising per-document errors."""

    try:
        markdown = client.ocr_file(item)
        error = None
    except Exception as exc:  # noqa: BLE001 - failures should become output rows.
        markdown = ""
        error = str(exc)
    return OCRResult(
        id=item.id,
        source_file=str(item.source_file),
        ocr_markdown=markdown,
        ocr_error=error,
        timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        example=item.example,
    )


def _source_file_from_manifest(record: dict[str, Any]) -> Path:
    """Pick a source file from manifest, preferring PDFs."""

    for key in ("pdf_path", "image_path"):
        value = record.get(key)
        if value:
            path = Path(value)
            if path.exists():
                return path
            raise OCRClientError(f"Manifest source file does not exist: {path}")
    raise OCRClientError("Manifest row must include pdf_path or image_path.")


def _build_mistral_client(api_key: str) -> Any:
    """Build a Mistral SDK client across supported import layouts."""

    try:
        from mistralai import Mistral  # type: ignore[attr-defined]
    except ImportError:
        try:
            from mistralai.client import Mistral  # type: ignore[no-redef]
        except ImportError as exc:
            raise OCRClientError("The mistralai SDK is required for Mistral OCR.") from exc
    return Mistral(api_key=api_key)


def _mistral_file_model() -> Any:
    """Return the Mistral File model class."""

    try:
        from mistralai.client.models import File
    except ImportError as exc:
        raise OCRClientError("Could not import mistralai File model for upload.") from exc
    return File


def _ocr_response_to_markdown(response: Any) -> str:
    """Extract markdown from Mistral OCR response pages."""

    pages = getattr(response, "pages", None)
    if pages is None and isinstance(response, dict):
        pages = response.get("pages")
    if not pages:
        raise OCRClientError("Mistral OCR response did not include pages.")

    markdown_pages: list[str] = []
    for page in pages:
        markdown = getattr(page, "markdown", None)
        if markdown is None and isinstance(page, dict):
            markdown = page.get("markdown")
        if markdown:
            markdown_pages.append(str(markdown))
    if not markdown_pages:
        raise OCRClientError("Mistral OCR response pages did not include markdown.")
    return "\n\n".join(markdown_pages)


def _content_type(path: Path) -> str:
    """Return a content type for supported rendered artifacts."""

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    return "application/octet-stream"
