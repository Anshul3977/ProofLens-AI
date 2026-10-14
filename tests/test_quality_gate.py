from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("quality_gate", SCRIPTS / "quality_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def report():
    return {"scope": "smoke", "dataset_id": "v1", "dataset_sha256": "data",
            "generator_sha256": "generator", "settings_sha256": "settings", "opencv": "5.0.0",
            "cases": [{"id": "matching", "status": "DIFFERENCES_AVAILABLE",
                       "regions_present": False, "passed": True}]}


def test_gate_accepts_unchanged_behavior():
    assert gate.compare(report(), report()) == []


def test_gate_rejects_regression_even_if_pass_flag_is_true():
    current = deepcopy(report())
    current["cases"][0]["regions_present"] = True
    assert "Behavior changed: matching" in gate.compare(current, report())


def test_gate_rejects_modified_contract_and_missing_case():
    current = report()
    current["settings_sha256"] = "weakened"
    current["cases"] = []
    failures = gate.compare(current, report())
    assert "Contract differs: settings_sha256" in failures
    assert "Case set differs from baseline" in failures


def test_gate_rejects_failed_expectation():
    current = report()
    current["cases"][0]["passed"] = False
    assert "Smoke expectation failed: matching" in gate.compare(current, report())
