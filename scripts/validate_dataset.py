"""Audit a ReceiptInject synthetic dataset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receiptinject.dataset_generator import (  # noqa: E402
    audit_dataset_file,
    save_audit_report,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/examples_500.jsonl", help="Dataset JSONL path.")
    parser.add_argument(
        "--report",
        default="results/dataset_audit.md",
        help="Markdown audit report output path.",
    )
    return parser.parse_args()


def main() -> None:
    """Run dataset audit and exit nonzero on failure."""

    args = parse_args()
    report = audit_dataset_file(Path(args.data))
    output_path = save_audit_report(report, Path(args.report))

    status = "PASS" if report.passed else "FAIL"
    print("Dataset audit summary")
    print(f"status: {status}")
    print(f"total examples: {report.total_examples}")
    print(f"document type counts: {dict(sorted(report.doc_type_counts.items()))}")
    print(f"attack type counts: {dict(sorted(report.attack_type_counts.items()))}")
    print(f"difficulty counts: {dict(sorted(report.difficulty_counts.items()))}")
    print(f"errors: {report.error_count}")
    print(f"warnings: {report.warning_count}")
    print(f"audit report: {output_path}")

    if not report.passed:
        print("\nAudit failed. Fix the following issues:")
        for finding in report.findings:
            if finding.severity == "error":
                example = f" [{finding.example_id}]" if finding.example_id else ""
                print(f"- {finding.check}{example}: {finding.message}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
