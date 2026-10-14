"""Measured fixed-vision vs adaptive-agent comparisons on development cases only."""
from contextlib import ExitStack
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import tempfile
from time import perf_counter
from unittest.mock import patch

import cv2
import numpy as np

from prooflens.agent import controller
from prooflens.config import Settings
from prooflens.evaluation.dataset import MANIFEST, load_manifest, render_case
from prooflens.evaluation.runner import next_action
from prooflens import pipeline


def measured_tools(module, operation):
    calls = []

    def tracked(name, function):
        def invoke(*args, **kwargs):
            calls.append(name)
            return function(*args, **kwargs)
        return invoke

    with ExitStack() as stack:
        for name in ("inspect_image_quality", "align_images", "inspect_differences"):
            stack.enter_context(patch.object(module, name, tracked(name, getattr(module, name))))
        start = perf_counter()
        result = operation()
        seconds = perf_counter() - start
    return result, calls, seconds * 1000


def agent_next_action(investigation) -> str:
    tools = [entry["tool"] for entry in investigation.trace]
    if "targeted_inspection" in tools:
        return "targeted_inspection"
    if str(investigation.state) == "manual_resolution":
        return "manual_resolution"
    if str(investigation.state) == "awaiting_evidence":
        return "request_retake" if "retake" in investigation.request.lower() else "request_alternative_viewpoint"
    if investigation.human_review_required:
        return "human_review"
    return "continue_inspection"


def summarize(records: list[dict], system: str) -> dict:
    rows = [record[system] for record in records]
    predicted = sum(row["candidate_mismatch"] for row in rows)
    positives = sum(record["expected_mismatch"] for record in records)
    true_positive = sum(record["expected_mismatch"] and record[system]["candidate_mismatch"] for record in records)
    eligible = [record[system] for record in records if record["alignment_eligible"]]
    return {"total_cases": len(rows), "next_action_correct": sum(row["action_correct"] for row in rows),
            "candidate_mismatch_precision": true_positive / predicted if predicted else None,
            "candidate_mismatch_recall": true_positive / positives if positives else None,
            "alignment_success": sum(row["alignment_success"] for row in eligible),
            "alignment_eligible": len(eligible), "abstention_cases": sum(row["abstained"] for row in rows),
            "human_review_cases": sum(row["human_review_required"] for row in rows) if system == "agent" else None,
            "latency_ms": {"median": float(np.median([row["latency_ms"] for row in rows])),
                           "p95": float(np.percentile([row["latency_ms"] for row in rows], 95))},
            "actual_vision_tool_calls": {"median": float(np.median([len(row["tool_calls"]) for row in rows])),
                                        "total": sum(len(row["tool_calls"]) for row in rows)}}


def evaluate_agents(evidence_dir: Path | None = None) -> dict:
    manifest = load_manifest()
    cases = [case for case in manifest["cases"] if case["split"] == "development"]
    records = []
    with tempfile.TemporaryDirectory(prefix="prooflens-agent-eval-") as temporary:
        root = evidence_dir or Path(temporary)
        for case in cases:
            reference, image = render_case(case)
            folder = root / case["id"]
            fixed, fixed_calls, fixed_ms = measured_tools(pipeline, lambda: pipeline.inspect_pair(
                reference, image, folder / "fixed"))
            candidate = bool(fixed.differences and fixed.differences.regions)
            action = next_action(fixed.status, candidate)
            fixed_row = {"action": action, "action_correct": action == case["expected_next_action"],
                         "status": fixed.status, "candidate_mismatch": candidate,
                         "alignment_success": bool(fixed.alignment and fixed.alignment.success),
                         "abstained": fixed.status != "DIFFERENCES_AVAILABLE",
                         "human_review_required": None, "tool_calls": fixed_calls, "latency_ms": fixed_ms}
            agent = controller.InspectionAgent(folder / "agent")
            investigation, calls, agent_ms = measured_tools(controller, lambda: agent.start(
                reference, image, identifier=case["source_id"]))
            action = agent_next_action(investigation)
            trace = investigation.trace
            candidate = any(entry["tool"] == "differences" and entry["observations"].get("regions") for entry in trace)
            aligned = any(entry["tool"] == "alignment" and entry["observations"].get("success") for entry in trace)
            agent_row = {"action": action, "action_correct": action == case["expected_next_action"],
                         "state": str(investigation.state), "verdict": str(investigation.verdict),
                         "candidate_mismatch": bool(candidate), "alignment_success": aligned,
                         "abstained": str(investigation.verdict) == "insufficient_evidence",
                         "human_review_required": investigation.human_review_required,
                         "tool_calls": calls, "logical_trace_steps": len(trace), "latency_ms": agent_ms}
            records.append({"id": case["id"], "source_id": case["source_id"], "category": case["category"],
                            "expected_action": case["expected_next_action"],
                            "expected_mismatch": case["ground_truth"]["mismatch"],
                            "alignment_eligible": case["ground_truth"]["alignment_eligible"],
                            "fixed": fixed_row, "agent": agent_row})
    sha = lambda value: hashlib.sha256(value).hexdigest()
    return {"scope": "synthetic_development_fixed_vs_agent", "split": "development",
            "holdout_evaluated": False, "dataset_sha256": sha(MANIFEST.read_bytes()),
            "settings_sha256": sha(json.dumps(asdict(Settings()), sort_keys=True).encode()),
            "measurement_sha256": sha(Path(__file__).read_bytes()), "opencv": cv2.__version__,
            "cases": records, "metrics": {system: summarize(records, system) for system in ("fixed", "agent")},
            "limitations": ["Synthetic candidates are not real fraud incidents; real-world performance unavailable.",
                            "Both systems use identical images and unchanged vision thresholds.",
                            "Fixed vision pipeline performs quality/alignment/differences with safety aborts; no targeted tool or human-review policy.",
                            "API-call counts are instrumented invocations; logical agent trace length is reported separately.",
                            "One pass per case, no warmup; timings include artifact persistence, exclude fixture rendering.",
                            "No overall accuracy or speed improvement is presumed; agent adds targeted work and review handling."]}


def check_agent_gate(report: dict, baseline: dict) -> list[str]:
    failures = []
    for key in ("scope", "split", "dataset_sha256", "settings_sha256", "measurement_sha256", "opencv"):
        if report.get(key) != baseline.get(key):
            failures.append(f"Contract mismatch: {key}")
    if report.get("holdout_evaluated") is not False:
        failures.append("Holdout must remain untouched during development")
    old = {row["id"]: row for row in baseline["cases"]}
    current = {row["id"]: row for row in report["cases"]}
    if len(current) != len(report["cases"]) or set(old) != set(current):
        failures.append("Case identity mismatch")
    for case_id, row in current.items():
        if case_id not in old:
            continue
        for system in ("fixed", "agent"):
            previous = old[case_id][system]
            result = row[system]
            if previous["action_correct"] and not result["action_correct"]:
                failures.append(f"Next-action regression: {case_id}/{system}")
            for key in ("candidate_mismatch", "alignment_success", "human_review_required", "abstained"):
                if result[key] != previous[key]:
                    failures.append(f"Outcome changed: {case_id}/{system}/{key}")
        if row["agent"]["candidate_mismatch"] and not row["agent"]["human_review_required"]:
            failures.append(f"Suspicious evidence bypassed human review: {case_id}")
    return failures
