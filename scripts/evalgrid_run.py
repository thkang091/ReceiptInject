"""Run an EvalGrid experiment from YAML config."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evalgrid.cli import parse_run_args, run_from_args  # noqa: E402


def main() -> None:
    """CLI entry point."""

    run_from_args(parse_run_args())


if __name__ == "__main__":
    main()
