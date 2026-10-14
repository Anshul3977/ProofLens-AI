from copy import deepcopy

from prooflens.agent_benchmark import check_agent_gate, measured_tools
from prooflens import pipeline
from prooflens.synthetic import reference_image


def baseline_record():
    result = {"action_correct": True, "candidate_mismatch": True, "alignment_success": True,
              "human_review_required": True, "abstained": False}
    return {"scope": "test", "split": "development", "dataset_sha256": "data", "settings_sha256": "settings",
            "measurement_sha256": "measurement", "opencv": "5.0.0", "holdout_evaluated": False,
            "cases": [{"id": "case", "fixed": deepcopy(result), "agent": deepcopy(result)}]}


def test_agent_gate_rejects_changed_review_contract_and_cases():
    report = baseline_record()
    baseline = deepcopy(report)
    assert check_agent_gate(report, baseline) == []
    report["cases"][0]["agent"]["human_review_required"] = False
    assert any("human review" in error for error in check_agent_gate(report, baseline))
    report = baseline_record()
    report["holdout_evaluated"] = True
    assert any("Holdout" in error for error in check_agent_gate(report, baseline))
    report = baseline_record()
    report["cases"] = []
    assert "Case identity mismatch" in check_agent_gate(report, baseline)


def test_api_counts_are_executed_not_inferred(tmp_path):
    image = reference_image()
    result, calls, latency = measured_tools(pipeline, lambda: pipeline.inspect_pair(image, image, tmp_path))
    assert result.status == "DIFFERENCES_AVAILABLE"
    assert calls == ["inspect_image_quality", "inspect_image_quality", "align_images", "inspect_differences"]
    assert latency > 0
