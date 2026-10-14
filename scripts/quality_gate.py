"""Execute tests and fresh Phase 1 smoke checks against the recorded contract."""
import json
from pathlib import Path
import subprocess
import sys
from evaluate import evaluate

ROOT = Path(__file__).resolve().parents[1]


def compare(current: dict, baseline: dict) -> list[str]:
    failures = []
    for key in ["scope", "dataset_id", "dataset_sha256", "generator_sha256", "settings_sha256", "opencv"]:
        if current.get(key) != baseline.get(key):
            failures.append(f"Contract differs: {key}")
    previous = {case["id"]: case for case in baseline["cases"]}
    if set(previous) != {case["id"] for case in current["cases"]}:
        failures.append("Case set differs from baseline")
    for case in current["cases"]:
        if not case["passed"]:
            failures.append(f"Smoke expectation failed: {case['id']}")
        old = previous.get(case["id"])
        if old and (case["status"], case["regions_present"]) != (old["status"], old["regions_present"]):
            failures.append(f"Behavior changed: {case['id']}")
    return failures


if __name__ == "__main__":
    tests = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, check=False)
    if tests.returncode:
        raise SystemExit(tests.returncode)
    baseline = json.loads((ROOT / "eval_data/phase1-baseline.json").read_text(encoding="utf-8"))
    current = evaluate()
    failures = compare(current, baseline)
    print(json.dumps({"scope": current["scope"], "passed": not failures, "failures": failures,
                      "cases": current["total_cases"], "latency_ms": current["latency_ms"],
                      "baseline_latency_ms": baseline["latency_ms"],
                      "latency_gate": "informational only; no threshold established"}, indent=2))
    raise SystemExit(bool(failures))
