"""Render synthetic ReceiptInject examples to PDF and PNG files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receiptinject.dataset_generator import load_jsonl  # noqa: E402
from receiptinject.render_documents import (  # noqa: E402
    MANIFEST_NAME,
    render_example,
    save_manifest,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/examples_500.jsonl", help="Input dataset JSONL.")
    parser.add_argument("--out", default="data/rendered_docs", help="Rendered output directory.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum examples to render.")
    return parser.parse_args()


def main() -> None:
    """Render examples and write a manifest."""

    args = parse_args()
    out_dir = Path(args.out)
    try:
        examples = load_jsonl(Path(args.data))
        if args.limit is not None:
            if args.limit < 0:
                raise ValueError("--limit must be non-negative")
            examples = examples[: args.limit]

        rendered = []
        for example in tqdm(examples, desc="Rendering", unit="document"):
            rendered.append(render_example(example, out_dir))
        manifest_path = save_manifest(rendered, out_dir / MANIFEST_NAME)
    except Exception as exc:
        print(f"Rendering failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"Rendered {len(rendered)} documents")
    print(f"PDF directory: {out_dir / 'pdf'}")
    print(f"Image directory: {out_dir / 'images'}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
