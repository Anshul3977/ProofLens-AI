from dataclasses import asdict
import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from prooflens.agent import InspectionAgent, State, Verdict
from prooflens.pipeline import read_image
from prooflens.synthetic import reference_image


def tools(result):
    return [entry["tool"] for entry in result.trace]


def test_clear_evidence_runs_real_tools_and_persists_native_images(tmp_path):
    image = reference_image()
    agent = InspectionAgent(tmp_path)
    result = agent.start(image, image)
    assert result.state == State.COMPLETE
    assert result.verdict == Verdict.CONSISTENT
    assert tools(result) == ["quality", "alignment", "differences"]
    assert result.trace[1]["observations"]["inliers"] >= 10
    assert result.trace[2]["observations"]["changed_fraction"] == 0
    assert not result.human_review_required
    assert asdict(agent.load(result.id)) == asdict(result)
    assert np.array_equal(read_image(tmp_path / result.id / "reference.png"), image)
    assert all(read_image(path).shape[:2] == image.shape[:2]
               for path in map(Path, result.artifacts.values()))
    assert not list(tmp_path.rglob("*.tmp"))


def test_blur_requests_retake_and_counterfactual_changes_next_tool(tmp_path):
    image = reference_image()
    agent = InspectionAgent(tmp_path)
    blurred = cv2.GaussianBlur(image, (31, 31), 10)
    bad = agent.start(image, blurred, "same-context")
    good = agent.start(image, image, "same-context")
    assert bad.state == State.AWAITING_EVIDENCE
    assert "retake" in bad.request.lower()
    assert tools(bad) == ["quality"]
    assert bad.trace[0]["observations"]["inspection"]["metrics"]["laplacian_variance"] < 50
    assert tools(good)[1] == "alignment"


def test_quality_glare_requests_lighting_change(tmp_path):
    image = reference_image()
    glare = image.copy()
    glare[80:250, 100:400] = 255
    result = InspectionAgent(tmp_path).start(image, glare)
    assert result.state == State.AWAITING_EVIDENCE
    assert "reflections" in result.request
    assert result.trace[0]["observations"]["inspection"]["metrics"]["potential_glare_fraction"] > .08


def test_alignment_failure_requests_alternative_viewpoint(tmp_path):
    image = reference_image()
    rng = np.random.default_rng(12)
    unrelated = rng.integers(35, 220, image.shape, dtype=np.uint8)
    result = InspectionAgent(tmp_path).start(image, unrelated)
    assert tools(result) == ["quality", "alignment"]
    assert result.state == State.AWAITING_EVIDENCE
    assert "alternative viewpoint" in result.request
    assert not result.trace[-1]["observations"]["success"]


def test_suspicious_region_executes_crop_reinspection_and_requires_human(tmp_path):
    image = reference_image()
    modified = image.copy()
    modified[280:350, 300:390] = (35, 35, 35)
    result = InspectionAgent(tmp_path).start(image, modified)
    assert "targeted_inspection" in tools(result)
    assert result.state == State.HUMAN_REVIEW
    assert result.verdict == Verdict.SUSPECTED_MISMATCH
    assert result.human_review_required
    target = next(item for item in result.trace if item["tool"] == "targeted_inspection")
    x, y, w, h = target["observations"]["region"]
    assert read_image(Path(target["observations"]["artifact"])).shape[:2] == (h, w)
    assert target["observations"]["local"]["valid_pixels"] > 0


def test_unknown_reference_manual_resolution_then_resume(tmp_path):
    image = reference_image()
    agent = InspectionAgent(tmp_path)
    initial = agent.start(None, image, "unknown")
    assert initial.state == State.MANUAL_RESOLUTION
    assert "manually" in initial.request
    resumed = agent.resume(initial.id, image, reference=image, identifier="resolved")
    assert resumed.id == initial.id
    assert resumed.identifier == "resolved"
    assert resumed.state == State.COMPLETE
    assert resumed.trace[:1] == initial.trace
    assert resumed.recaptures == 0


def test_insufficient_evidence_and_bad_reference_require_human(tmp_path):
    agent = InspectionAgent(tmp_path)
    absent = agent.start(reference_image(), None)
    assert absent.verdict == Verdict.INSUFFICIENT
    assert absent.human_review_required
    invalid = agent.start(np.zeros((32, 32, 3), np.uint8), reference_image())
    assert invalid.human_review_required
    assert "reference" in invalid.request


def test_followup_resumes_across_controller_restart(tmp_path):
    image = reference_image()
    blurred = cv2.GaussianBlur(image, (31, 31), 10)
    initial = InspectionAgent(tmp_path).start(image, blurred)
    resumed = InspectionAgent(tmp_path).resume(initial.id, image)
    assert resumed.id == initial.id
    assert resumed.state == State.COMPLETE
    assert resumed.recaptures == 1
    assert resumed.trace[:len(initial.trace)] == initial.trace
    assert len(resumed.trace) == 4
    with pytest.raises(ValueError, match="Only investigations"):
        InspectionAgent(tmp_path).resume(resumed.id, image)


def test_recapture_limit_survives_restart_with_looser_constructor(tmp_path):
    image = reference_image()
    blurred = cv2.GaussianBlur(image, (31, 31), 10)
    initial = InspectionAgent(tmp_path, max_recaptures=1).start(image, blurred)
    final = InspectionAgent(tmp_path, max_recaptures=100).resume(initial.id, blurred)
    assert final.state == State.HUMAN_REVIEW
    assert final.human_review_required
    assert final.recaptures == 1
    assert "Recapture limit" in final.request


@pytest.mark.parametrize("budget", [1, 2])
def test_step_limit_prevents_unexecuted_tool_claims(tmp_path, budget):
    result = InspectionAgent(tmp_path, max_steps=budget).start(reference_image(), reference_image())
    assert len(result.trace) == budget
    assert result.state == State.HUMAN_REVIEW
    assert result.verdict == Verdict.INSUFFICIENT
    assert "Tool-call limit" in result.request


@pytest.mark.parametrize("identifier", ["../escape", "not-a-uuid", "", "00000000-0000-0000-0000-000000000000/../../"])
def test_unsafe_ids_rejected(tmp_path, identifier):
    with pytest.raises(ValueError, match="UUID"):
        InspectionAgent(tmp_path).load(identifier)


def test_persisted_policy_records_exact_settings(tmp_path):
    agent = InspectionAgent(tmp_path)
    result = agent.start(reference_image(), reference_image())
    raw = json.loads((tmp_path / result.id / "state.json").read_text())
    assert raw["policy"]["settings"] == asdict(agent.settings)
    assert raw["policy"]["max_steps"] == 40


def test_tool_exception_escalates_without_fake_observation(tmp_path, monkeypatch):
    def fail(*args):
        raise cv2.error("reproducible injected tool failure")
    monkeypatch.setattr("prooflens.agent.controller.align_images", fail)
    result = InspectionAgent(tmp_path).start(reference_image(), reference_image())
    assert result.human_review_required
    assert tools(result) == ["quality", "alignment"]
    assert "error" in result.trace[-1]["observations"]
    assert "inliers" not in result.trace[-1]["observations"]
    assert "Vision tool failed" in result.request


def test_followup_cannot_reset_cumulative_step_limit(tmp_path):
    image = reference_image()
    blurred = cv2.GaussianBlur(image, (31, 31), 10)
    initial = InspectionAgent(tmp_path, max_steps=2).start(image, blurred)
    result = InspectionAgent(tmp_path, max_steps=100).resume(initial.id, image)
    assert len(result.trace) == 2
    assert tools(result) == ["quality", "quality"]
    assert result.state == State.HUMAN_REVIEW


def test_suspicious_evidence_cannot_bypass_targeted_tool_budget(tmp_path):
    image = reference_image()
    modified = image.copy()
    modified[280:350, 300:390] = 35
    result = InspectionAgent(tmp_path, max_steps=3).start(image, modified)
    assert tools(result) == ["quality", "alignment", "differences"]
    assert result.state == State.HUMAN_REVIEW
    assert result.verdict == Verdict.INSUFFICIENT
    assert "Tool-call limit" in result.request


@pytest.mark.parametrize("steps,recaptures", [(0, 2), (40, -1)])
def test_invalid_bounds_rejected(tmp_path, steps, recaptures):
    with pytest.raises(ValueError):
        InspectionAgent(tmp_path, max_steps=steps, max_recaptures=recaptures)


@pytest.mark.parametrize("change", ["identifier", "reference"])
def test_recapture_cannot_change_identity_or_reference(tmp_path, change):
    image = reference_image()
    agent = InspectionAgent(tmp_path)
    initial = agent.start(image, cv2.GaussianBlur(image, (31, 31), 10), "product-A")
    kwargs = {"identifier": "product-B"} if change == "identifier" else {"reference": cv2.flip(image, 1)}
    with pytest.raises(ValueError, match="Cannot"):
        agent.resume(initial.id, image, **kwargs)
    persisted = agent.load(initial.id)
    assert persisted.identifier == "product-A" and persisted.recaptures == 0
    assert persisted.trace == initial.trace


def test_additional_selected_view_retains_trace_and_detects_later_difference(tmp_path):
    image = reference_image()
    agent = InspectionAgent(tmp_path)
    initial = agent.start(image, image, "product-A")
    modified = image.copy()
    modified[280:350, 300:390] = 35
    result = agent.inspect_additional(initial.id, modified)
    assert result.id == initial.id and result.trace[:len(initial.trace)] == initial.trace
    assert result.identifier == "product-A" and result.recaptures == 0
    assert result.human_review_required and result.verdict == Verdict.SUSPECTED_MISMATCH
    with pytest.raises(ValueError, match="Additional"):
        agent.inspect_additional(result.id, image)
