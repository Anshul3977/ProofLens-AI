import argparse
import json
from pathlib import Path

from prooflens.agent_benchmark import evaluate_agents

parser = argparse.ArgumentParser(description="Measured fixed-pipeline/adaptive-agent comparison; development only")
parser.add_argument("--output", type=Path, default=Path("artifacts/evaluation/agent-comparison.json"))
parser.add_argument("--evidence", type=Path, help="Retain actual images, overlays and traces")
args = parser.parse_args()
report = evaluate_agents(args.evidence)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
print(json.dumps({"metrics": report["metrics"], "holdout_evaluated": report["holdout_evaluated"]}, indent=2))
