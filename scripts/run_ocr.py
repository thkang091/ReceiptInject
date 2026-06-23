"""Run OCR over rendered ReceiptInject documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receiptinject.ocr_client import (  # noqa: E402
    MistralOCRClient,
    MockOCRClient,
    load_manifest,
    ocr_manifest_item,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default="data/rendered_docs/manifest.jsonl",
        help="Rendered-document manifest JSONL.",
    )
    parser.add_argument(
        "--output",
        default="data/ocr_outputs/ocr_results.jsonl",
        help="OCR results JSONL output.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Maximum documents to OCR.")
    parser.add_argument("--sleep", type=float, default=0.0, help="Seconds to sleep per OCR call.")
    parser.add_argument("--mock", action="store_true", help="Use offline mock OCR.")
    return parser.parse_args()


def main() -> None:
    """Run OCR and write JSONL rows."""

    args = parse_args()
    try:
        if args.limit is not None and args.limit < 0:
            raise ValueError("--limit must be non-negative")
        items = load_manifest(Path(args.manifest), limit=args.limit)
        client = MockOCRClient() if args.mock else MistralOCRClient()
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        results = []
        with output_path.open("w", encoding="utf-8") as handle:
            for item in tqdm(items, desc="OCR", unit="document"):
                result = ocr_manifest_item(client, item)
                results.append(result)
                handle.write(result.model_dump_json() + "\n")
                handle.flush()
                if args.sleep > 0:
                    import time

                    time.sleep(args.sleep)
    except Exception as exc:
        print(f"OCR setup failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    failures = sum(result.ocr_error is not None for result in results)
    print(f"OCR completed: {len(results)} documents")
    print(f"Failures: {failures}")
    print(f"Output: {output_path}")
    if not args.mock:
        print("Note: Mistral OCR API usage may incur cost.")


if __name__ == "__main__":
    main()
