import argparse
import json
from pathlib import Path

from prooflens.video_benchmark import benchmark_video

parser = argparse.ArgumentParser(description="Compare keyframe selectors on an identical synthetic candidate set")
parser.add_argument("video", type=Path)
parser.add_argument("metadata", type=Path)
parser.add_argument("--output", type=Path, default=Path("artifacts/evaluation/keyframes.json"))
args = parser.parse_args()
report = benchmark_video(args.video, args.metadata)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
print(json.dumps(report, indent=2))
