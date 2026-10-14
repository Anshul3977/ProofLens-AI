import json
from pathlib import Path

from prooflens.agent_benchmark import check_agent_gate, evaluate_agents

root = Path(__file__).resolve().parents[1]
baseline = json.loads((root / "eval_data/agent_baseline.json").read_text(encoding="utf-8"))
report = evaluate_agents()
failures = check_agent_gate(report, baseline)
print(json.dumps({"passed": not failures, "failures": failures, "metrics": report["metrics"]}, indent=2))
raise SystemExit(bool(failures))
