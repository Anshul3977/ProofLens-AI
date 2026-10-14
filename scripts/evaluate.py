"""Phase 1 synthetic smoke evaluation; full vision/agent benchmarks are deferred."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import tempfile
from time import perf_counter

import cv2
import numpy as np
from prooflens.config import Settings
from prooflens.pipeline import inspect_pair
from prooflens.synthetic import reference_image, perspective_image

ROOT = Path(__file__).resolve().parents[1]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def evaluate() -> dict:
    manifest_bytes = (ROOT / "eval_data/smoke.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    reference = reference_image()
    modified = reference.copy()
    cv2.rectangle(modified, (390, 280), (465, 340), (30, 30, 30), -1)
    images = {"matching": reference.copy(), "perspective": perspective_image(reference),
              "modified": modified, "blurry": cv2.GaussianBlur(reference, (31, 31), 10)}
    records = []
    with tempfile.TemporaryDirectory(prefix="prooflens-smoke-") as directory:
        for case in manifest["cases"]:
            start = perf_counter()
            result = inspect_pair(reference, images[case["id"]], Path(directory) / case["id"])
            elapsed = (perf_counter() - start) * 1000
            regions = bool(result.differences and result.differences.regions)
            records.append({"id": case["id"], "status": result.status, "regions_present": regions,
                            "passed": result.status == case["expected_status"] and regions == case["expected_regions"],
                            "latency_ms": elapsed})
    latencies = [case["latency_ms"] for case in records]
    return {"scope": "phase1_synthetic_smoke", "dataset_id": manifest["dataset_id"],
            "dataset_sha256": digest(manifest_bytes),
            "generator_sha256": digest((ROOT / "src/prooflens/synthetic.py").read_bytes()
                                       + Path(__file__).read_bytes()),
            "settings_sha256": digest(json.dumps(asdict(Settings()), sort_keys=True).encode()),
            "opencv": cv2.__version__, "python": platform.python_version(), "cases": records,
            "passed_cases": sum(case["passed"] for case in records), "total_cases": len(records),
            "latency_ms": {"median": float(np.median(latencies)), "p95": float(np.percentile(latencies, 95))},
            "unavailable_metrics": ["agent_actions", "agent_vs_fixed_baseline", "real_photo_accuracy",
                                    "region_IoU", "holdout_performance"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/evaluation/latest.json")
    args = parser.parse_args()
    report = evaluate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed_cases"] == report["total_cases"] else 1)
