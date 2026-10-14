"""Fixed-pipeline metrics, saved failures and recorded-outcome regression gates."""
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
from .dataset import MANIFEST, load_manifest, render_case


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def next_action(status: str, regions: bool) -> str:
    return {"QUALITY_INSUFFICIENT": "request_retake", "ALIGNMENT_FAILED": "request_alternative_viewpoint",
            "INVALID_INPUT": "human_review"}.get(status, "targeted_inspection" if regions else "continue_inspection")


def evaluate_suite(split: str = "development", evidence_dir: Path | None = None) -> dict:
    if split not in {"development", "holdout"}:
        raise ValueError("Unknown split")
    manifest = load_manifest()
    cases = [c for c in manifest["cases"] if c["split"] == split]
    records = []
    with tempfile.TemporaryDirectory(prefix="prooflens-suite-") as temp:
        for case in cases:
            reference, image = render_case(case)
            cv2.setRNGSeed(case["seed"])
            start = perf_counter()
            result = inspect_pair(reference, image, Path(temp) / case["id"])
            latency = (perf_counter() - start) * 1000
            regions = bool(result.differences and result.differences.regions)
            action = next_action(result.status, regions)
            passed = result.status == case["expected_status"] and action == case["expected_next_action"]
            record = {"id": case["id"], "category": case["category"], "status": result.status,
                      "next_action": action, "action_correct": action == case["expected_next_action"],
                      "passed": passed, "regions_present": regions,
                      "expected_mismatch": case["ground_truth"]["mismatch"],
                      "missed_mismatch_candidate": case["ground_truth"]["mismatch"] and not regions,
                      "quality_acceptable": not result.inspection_quality.recommended_actions,
                      "expected_quality_acceptable": case["ground_truth"]["quality_acceptable"],
                      "alignment_eligible": case["ground_truth"]["alignment_eligible"],
                      "alignment_success": bool(result.alignment and result.alignment.success),
                      "quality_metrics": result.inspection_quality.metrics,
                      "alignment_reason": result.alignment.reason if result.alignment else None,
                      "region_boxes": result.differences.regions if result.differences else [],
                      "latency_ms": latency}
            if not passed:
                record["expected_status"] = case["expected_status"]
                record["expected_next_action"] = case["expected_next_action"]
            if evidence_dir and (not passed or record["missed_mismatch_candidate"]):
                folder = evidence_dir / case["id"]
                folder.mkdir(parents=True, exist_ok=True)
                for name, pixels in [("reference", reference), ("inspection", image)]:
                    ok, encoded = cv2.imencode(".png", pixels)
                    if not ok:
                        raise OSError("Image encoding failed")
                    (folder / f"{name}.png").write_bytes(encoded.tobytes())
                for name in ("overlay", "evidence_mask"):
                    if name in result.artifacts:
                        (folder / f"{name}.png").write_bytes(Path(result.artifacts[name]).read_bytes())
            records.append(record)
    positives = sum(r["expected_mismatch"] for r in records)
    predicted = sum(r["regions_present"] for r in records)
    tp = sum(r["expected_mismatch"] and r["regions_present"] for r in records)
    eligible = [r for r in records if r["alignment_eligible"]]
    latencies = [r["latency_ms"] for r in records]
    source = Path(__file__).parent
    return {"dataset_id": manifest["dataset_id"], "split": split, "dataset_sha256": digest(MANIFEST.read_bytes()),
            "generator_sha256": digest((source / "dataset.py").read_bytes() + Path(__file__).read_bytes()),
            "settings_sha256": digest(json.dumps(asdict(Settings()), sort_keys=True).encode()),
            "opencv": cv2.__version__, "python": platform.python_version(), "cases": records,
            "metrics": {"total_cases": len(records), "passed_cases": sum(r["passed"] for r in records),
                        "quality_correct": sum(r["quality_acceptable"] == r["expected_quality_acceptable"] for r in records),
                        "alignment_success": sum(r["alignment_success"] for r in eligible), "alignment_eligible": len(eligible),
                        "next_action_correct": sum(r["action_correct"] for r in records),
                        "candidate_mismatch_precision": tp / predicted if predicted else None,
                        "candidate_mismatch_recall": tp / positives if positives else None,
                        "mismatch_positive_cases": positives, "mismatch_predicted_cases": predicted,
                        "missed_mismatch_candidates": positives - tp,
                        "abstention_cases": sum(r["status"] != "DIFFERENCES_AVAILABLE" for r in records),
                        "latency_ms": {"median": float(np.median(latencies)), "p95": float(np.percentile(latencies, 95))}},
            "unavailable_metrics": ["real_world", "holdout" if split == "development" else "real_holdout",
                                    "agent_actions", "tool_calls", "human_review_rate", "frame_selection", "region_pixel_precision_recall"]}


def check_gate(report: dict, baseline: dict) -> list[str]:
    failures = []
    for key in ("dataset_id", "split", "dataset_sha256", "generator_sha256", "settings_sha256", "opencv"):
        if report.get(key) != baseline.get(key):
            failures.append(f"Contract mismatch: {key}")
    old = {r["id"]: r for r in baseline["cases"]}
    new = {r["id"]: r for r in report["cases"]}
    if old.keys() != new.keys() or len(new) != len(report["cases"]):
        failures.append("Case identity mismatch")
    for key, previous in old.items():
        current = new.get(key)
        if current is None:
            continue
        if previous["passed"] and not current["passed"]:
            failures.append(f"Previously passing case failed: {key}")
        for metric in ("quality_acceptable", "alignment_success", "regions_present", "status", "next_action"):
            if current[metric] != previous[metric] and not (current["passed"] and not previous["passed"]):
                failures.append(f"Outcome changed without labeled improvement: {key}/{metric}")
    return failures
