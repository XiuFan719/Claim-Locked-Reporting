#!/usr/bin/env python3
"""Run the synthetic public demonstration."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from claim_locked import run_pipeline  # noqa: E402


def main() -> None:
    outputs = run_pipeline(
        ROOT / "examples" / "evidence.json",
        ROOT / "examples" / "connective_prose.json",
        ROOT / "examples" / "output",
    )
    print("Claim-locked demo complete:")
    for path in outputs.values():
        print(f"  {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
