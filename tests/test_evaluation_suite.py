from copy import deepcopy
import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from prooflens.evaluation.dataset import load_manifest, render_case
from prooflens.evaluation.runner import check_gate, evaluate_suite


def test_manifest_has_100_cases_and_source_disjoint_splits():
    manifest = load_manifest()
    assert len(manifest["cases"]) == 100
    sources = {split: {c["source_id"] for c in manifest["cases"] if c["split"] == split}
               for split in ("development", "holdout")}
    assert not sources["development"] & sources["holdout"]
    assert {c["category"] for c in manifest["cases"]} == {
        "matching", "blur", "exposure", "glare", "perspective", "visible_difference", "mismatched_pair"}


def test_source_leakage_rejected(tmp_path):
    manifest = load_manifest()
    manifest["cases"][0]["split"] = "holdout"
    path = tmp_path / "leaked.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="leakage"):
        load_manifest(path)


def test_paired_source_leakage_rejected(tmp_path):
    manifest = load_manifest()
    manifest["cases"][6]["inspection_source_id"] = "source-09"
    path = tmp_path / "leaked.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="leakage"):
        load_manifest(path)


def test_development_rendering_determinism_and_ground_truth():
    for case in load_manifest()["cases"]:
        if case["split"] != "development":
            continue
        ref, seen = render_case(case)
        ref2, seen2 = render_case(case)
        assert ref.dtype == seen.dtype == np.uint8
        assert ref.shape == seen.shape == (360, 480, 3)
        assert np.array_equal(ref, ref2) and np.array_equal(seen, seen2)
        if case["category"] == "matching":
            assert np.array_equal(ref, seen)
        if case["category"] == "visible_difference":
            x, y, w, h = case["ground_truth"]["region_rectangles"][0]
            assert np.all(seen[y:y+h, x:x+w] == 20)
            changed = np.any(ref != seen, axis=2)
            assert not changed[:y].any() and not changed[y+h:].any()


def test_unknown_transformation_rejected():
    case = deepcopy(load_manifest()["cases"][0])
    case["transformations"] = [{"type": "unsupported"}]
    with pytest.raises(ValueError, match="Unknown"):
        render_case(case)


@pytest.fixture(scope="module")
def report():
    return evaluate_suite()


def test_default_evaluation_never_runs_holdout(report):
    assert report["split"] == "development"
    assert report["metrics"]["total_cases"] == 80
    assert not any(r["id"].startswith(("source-08", "source-09")) for r in report["cases"])
    assert report["opencv"].startswith("5.")
    assert report["metrics"]["latency_ms"]["median"] > 0
    assert "agent_actions" in report["unavailable_metrics"]


def test_recorded_baseline_gate(report):
    path = Path(__file__).resolve().parents[1] / "eval_data/suite_baseline.json"
    baseline = json.loads(path.read_text(encoding="utf-8"))
    assert check_gate(report, baseline) == []


def test_gate_rejects_contract_and_outcome_regressions(report):
    modified = deepcopy(report)
    modified["dataset_sha256"] = "changed"
    assert any("dataset_sha256" in f for f in check_gate(modified, report))
    modified = deepcopy(report)
    case = next(r for r in modified["cases"] if r["passed"])
    case["passed"] = False
    case["regions_present"] = not case["regions_present"]
    assert any("Previously passing" in f for f in check_gate(modified, report))
    modified = deepcopy(report)
    modified["cases"].pop()
    assert "Case identity mismatch" in check_gate(modified, report)
