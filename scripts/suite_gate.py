"""Fresh development evaluation against frozen recorded outcomes (not all-label success)."""
import argparse
import json
from pathlib import Path
from prooflens.evaluation.runner import check_gate, evaluate_suite

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=ROOT / "eval_data/suite_baseline.json")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/evaluation/suite-gate.json")
    args = parser.parse_args()
    report = evaluate_suite()
    failures = check_gate(report, json.loads(args.baseline.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"failures": failures, "evaluation": report}, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"gate_passed": not failures, "failures": failures, "metrics": report["metrics"]}, indent=2))
    raise SystemExit(bool(failures))
