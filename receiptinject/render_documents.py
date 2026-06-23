"""Render synthetic benchmark examples to PDF and PNG artifacts."""

from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from receiptinject.document_templates import receipt_to_text
from receiptinject.schemas import AttackType, BenchmarkExample, DocumentType

MANIFEST_NAME = "manifest.jsonl"


@dataclass(frozen=True)
class RenderedDocument:
    """Rendered artifact paths for one benchmark example."""

    id: str
    doc_type: str
    attack_type: str
    difficulty: str
    pdf_path: str
    image_path: str
    document_text: str | None = None
    example: dict[str, Any] | None = None

    def as_manifest_record(self) -> dict[str, str]:
        """Return the JSONL manifest representation."""

        record = {
            "id": self.id,
            "doc_type": self.doc_type,
            "attack_type": self.attack_type,
            "difficulty": self.difficulty,
            "pdf_path": self.pdf_path,
            "image_path": self.image_path,
        }
        if self.document_text is not None:
            record["document_text"] = self.document_text
        if self.example is not None:
            record["example"] = self.example
        return record


def render_example(example: BenchmarkExample, out_dir: Path) -> RenderedDocument:
    """Render one example to PDF and PNG."""

    pdf_dir = out_dir / "pdf"
    image_dir = out_dir / "images"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = pdf_dir / f"{example.id}.pdf"
    image_path = image_dir / f"{example.id}.png"
    layout = _layout_for(example.doc_type)
    blocks = _build_blocks(example)
    _render_pdf(example, blocks, pdf_path, layout)
    _render_png(example, blocks, image_path, layout)
    return RenderedDocument(
        id=example.id,
        doc_type=example.doc_type.value,
        attack_type=example.attack_type.value,
        difficulty=example.difficulty.value,
        pdf_path=str(pdf_path),
        image_path=str(image_path),
        document_text=example.document_text,
        example=example.model_dump(mode="json"),
    )


def render_dataset(
    examples: list[BenchmarkExample],
    out_dir: Path,
    limit: int | None = None,
) -> list[RenderedDocument]:
    """Render a dataset and write a JSONL manifest."""

    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative when provided")

    selected = examples[:limit] if limit is not None else examples
    rendered: list[RenderedDocument] = []
    for example in selected:
        try:
            rendered.append(render_example(example, out_dir))
        except Exception as exc:  # noqa: BLE001 - add context for CLI users.
            raise RuntimeError(f"Failed to render example {example.id}: {exc}") from exc

    save_manifest(rendered, out_dir / MANIFEST_NAME)
    return rendered


def save_manifest(rendered: list[RenderedDocument], path: Path) -> Path:
    """Write rendered artifact manifest JSONL."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in rendered:
            handle.write(json.dumps(item.as_manifest_record(), sort_keys=True) + "\n")
    return path


def render_text_preview(example: BenchmarkExample, output_path: Path) -> Path:
    """Write a text preview for debugging rendered content."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(receipt_to_text(example), encoding="utf-8")
    return output_path


def _render_pdf(
    example: BenchmarkExample,
    blocks: list[dict[str, Any]],
    pdf_path: Path,
    layout: dict[str, Any],
) -> None:
    """Render a PDF with reportlab."""

    page_size = layout["page_size"]
    margin = layout["margin"]
    line_height = layout["line_height"]
    max_chars = layout["max_chars"]
    pdf = canvas.Canvas(str(pdf_path), pagesize=page_size)
    width, height = page_size
    y = height - margin

    def ensure_space(required: float) -> None:
        nonlocal y
        if y - required < margin:
            _draw_pdf_footer(pdf, example, width, margin)
            pdf.showPage()
            y = height - margin

    pdf.setTitle(f"ReceiptInject synthetic document {example.id}")
    _draw_pdf_header(pdf, example, width, y, layout)
    y -= line_height * 3

    for block in blocks:
        wrapped = _wrap_lines(block["text"], max_chars=max_chars)
        required = max(line_height * (len(wrapped) + 1), line_height * 3)
        ensure_space(required)
        if block["kind"] == "note":
            y = _draw_pdf_note_box(pdf, wrapped, margin, y, width, line_height)
        elif block["kind"] == "table":
            y = _draw_pdf_table_block(pdf, wrapped, margin, y, width, line_height)
        else:
            y = _draw_pdf_text_block(pdf, wrapped, margin, y, line_height)

    _draw_pdf_footer(pdf, example, width, margin)
    pdf.save()


def _render_png(
    example: BenchmarkExample,
    blocks: list[dict[str, Any]],
    image_path: Path,
    layout: dict[str, Any],
) -> None:
    """Render a PNG with Pillow."""

    font = ImageFont.load_default()
    width = layout["image_width"]
    margin = layout["image_margin"]
    line_height = layout["image_line_height"]
    max_chars = layout["max_chars"]
    rendered_lines: list[tuple[str, str]] = []
    rendered_lines.extend(
        [
            ("title", f"ReceiptInject synthetic {example.doc_type.value}"),
            ("meta", f"Example ID: {example.id}"),
            ("meta", f"Attack type: {example.attack_type.value}"),
            ("blank", ""),
        ]
    )
    for block in blocks:
        for line in _wrap_lines(block["text"], max_chars=max_chars):
            rendered_lines.append((block["kind"], line))
        rendered_lines.append(("blank", ""))

    height = margin * 2 + max(1, len(rendered_lines)) * line_height + 24
    image = Image.new("RGB", (width, height), color=layout["background"])
    draw = ImageDraw.Draw(image)
    y = margin
    for kind, line in rendered_lines:
        if kind == "note" and line:
            draw.rectangle(
                [margin - 6, y - 3, width - margin + 6, y + line_height],
                fill=(255, 249, 214),
                outline=(161, 112, 0),
            )
        elif kind == "table" and line:
            draw.rectangle(
                [margin - 4, y - 2, width - margin + 4, y + line_height],
                fill=(242, 246, 250),
            )

        fill = layout["text_color"]
        if kind == "title":
            fill = (35, 35, 35)
        elif kind == "note":
            fill = (88, 62, 0)
        elif kind == "meta":
            fill = (80, 80, 80)
        draw.text((margin, y), line, fill=fill, font=font)
        y += line_height

    image.save(image_path)


def _build_blocks(example: BenchmarkExample) -> list[dict[str, str]]:
    """Split document text into layout blocks while preserving visible text."""

    blocks: list[dict[str, str]] = []
    current: list[str] = []
    in_note = False
    for line in example.document_text.splitlines():
        if line == "VISIBLE EMBEDDED BENCHMARK CONTENT":
            if current:
                blocks.append({"kind": _classify_block(current), "text": "\n".join(current)})
                current = []
            in_note = True
            current.append(line)
            continue

        if in_note:
            current.append(line)
            if not line.strip():
                blocks.append({"kind": "note", "text": "\n".join(current).strip()})
                current = []
                in_note = False
            continue

        current.append(line)

    if current:
        blocks.append(
            {
                "kind": "note" if in_note else _classify_block(current),
                "text": "\n".join(current),
            }
        )

    if example.attack_type != AttackType.NONE and not any(
        block["kind"] == "note" for block in blocks
    ):
        raise ValueError("adversarial example is missing visible embedded instruction block")
    return blocks


def _classify_block(lines: list[str]) -> str:
    """Classify a text block as table-ish or normal prose."""

    table_markers = ("ITEMS", "BILLING SUMMARY", "BALANCE SUMMARY", "ACTIVITY", "Total", "Subtotal")
    joined = "\n".join(lines)
    return "table" if any(marker in joined for marker in table_markers) else "text"


def _layout_for(doc_type: DocumentType) -> dict[str, Any]:
    """Return layout settings for a document family."""

    if doc_type == DocumentType.RECEIPT:
        return {
            "page_size": (260, 720),
            "margin": 20,
            "line_height": 10,
            "max_chars": 42,
            "image_width": 520,
            "image_margin": 28,
            "image_line_height": 16,
            "background": (255, 253, 246),
            "text_color": (42, 42, 42),
        }
    if doc_type == DocumentType.POLICY_DOCUMENT:
        max_chars = 92
    elif doc_type == DocumentType.MIXED_BUNDLE:
        max_chars = 86
    else:
        max_chars = 78
    return {
        "page_size": LETTER,
        "margin": 54,
        "line_height": 12,
        "max_chars": max_chars,
        "image_width": 1000,
        "image_margin": 48,
        "image_line_height": 18,
        "background": (255, 255, 252),
        "text_color": (35, 38, 42),
    }


def _wrap_lines(text: str, max_chars: int) -> list[str]:
    """Wrap text for rendering without dropping any content."""

    wrapped: list[str] = []
    for line in text.splitlines():
        if not line:
            wrapped.append("")
            continue
        wrapped.extend(
            textwrap.wrap(
                line,
                width=max_chars,
                replace_whitespace=False,
                drop_whitespace=False,
                break_long_words=False,
                break_on_hyphens=False,
            )
            or [line]
        )
    return wrapped


def _draw_pdf_header(
    pdf: canvas.Canvas,
    example: BenchmarkExample,
    width: float,
    y: float,
    layout: dict[str, Any],
) -> None:
    """Draw PDF header."""

    margin = layout["margin"]
    pdf.setStrokeColor(colors.HexColor("#737373"))
    pdf.line(margin, y - 16, width - margin, y - 16)
    pdf.setFillColor(colors.HexColor("#202124"))
    pdf.setFont("Helvetica-Bold", 11 if example.doc_type == DocumentType.RECEIPT else 14)
    pdf.drawString(margin, y, f"ReceiptInject synthetic {example.doc_type.value}")
    pdf.setFont("Helvetica", 7 if example.doc_type == DocumentType.RECEIPT else 9)
    pdf.setFillColor(colors.HexColor("#575757"))
    pdf.drawString(
        margin,
        y - 11,
        f"Example ID: {example.id} | Attack: {example.attack_type.value}",
    )


def _draw_pdf_footer(
    pdf: canvas.Canvas,
    example: BenchmarkExample,
    width: float,
    margin: float,
) -> None:
    """Draw a small synthetic-document footer."""

    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(colors.HexColor("#666666"))
    pdf.drawString(
        margin,
        14,
        f"Synthetic benchmark document only | {example.id} | visible text only",
    )
    pdf.line(margin, 26, width - margin, 26)


def _draw_pdf_text_block(
    pdf: canvas.Canvas,
    lines: list[str],
    x: float,
    y: float,
    line_height: float,
) -> float:
    """Draw normal PDF text."""

    pdf.setFont("Helvetica", 8.5)
    pdf.setFillColor(colors.HexColor("#202124"))
    for line in lines:
        pdf.drawString(x, y, line)
        y -= line_height
    return y - 4


def _draw_pdf_table_block(
    pdf: canvas.Canvas,
    lines: list[str],
    x: float,
    y: float,
    width: float,
    line_height: float,
) -> float:
    """Draw table-ish PDF text with light row shading."""

    pdf.setFont("Courier", 8)
    for index, line in enumerate(lines):
        if line and index % 2 == 0:
            pdf.setFillColor(colors.HexColor("#F4F7FA"))
            pdf.rect(x - 3, y - 2, width - x * 2 + 6, line_height, stroke=0, fill=1)
        pdf.setFillColor(colors.HexColor("#1F2933"))
        pdf.drawString(x, y, line)
        y -= line_height
    return y - 5


def _draw_pdf_note_box(
    pdf: canvas.Canvas,
    lines: list[str],
    x: float,
    y: float,
    width: float,
    line_height: float,
) -> float:
    """Draw visible embedded instructions in a note box."""

    box_height = line_height * (len(lines) + 1)
    pdf.setStrokeColor(colors.HexColor("#B7791F"))
    pdf.setFillColor(colors.HexColor("#FFF7D6"))
    pdf.rect(x - 4, y - box_height + line_height, width - x * 2 + 8, box_height, fill=1)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.setFillColor(colors.HexColor("#5C3D00"))
    for line in lines:
        pdf.drawString(x, y, line)
        y -= line_height
    return y - 8
