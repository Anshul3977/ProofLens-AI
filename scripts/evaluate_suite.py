"""Evaluate development synthetic cases; holdout requires explicit selection."""
import argparse
import json
from pathlib import Path
from prooflens.evaluation.runner import evaluate_suite

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["development", "holdout"], default="development")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/evaluation/suite-latest.json")
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "artifacts/evaluation/failures")
    args = parser.parse_args()
    report = evaluate_suite(args.split, args.evidence_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"split": report["split"], "metrics": report["metrics"],
                      "report": str(args.output)}, indent=2))
    # An evaluation measures actual weaknesses; the separate gate decides acceptance.
