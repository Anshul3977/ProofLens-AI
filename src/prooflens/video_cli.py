import argparse
from dataclasses import asdict
import json
from pathlib import Path
from uuid import uuid4

from prooflens.video import VideoSettings, inspect_video


def main() -> int:
    parser = argparse.ArgumentParser(description="ProofLens local MP4 quality/keyframe inspection")
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/video") / uuid4().hex)
    parser.add_argument("--samples", type=int, default=None)
    parser.add_argument("--config", type=Path, help="JSON VideoSettings overrides; --samples overrides sample_count")
    args = parser.parse_args()
    try:
        overrides = json.loads(args.config.read_text(encoding="utf-8")) if args.config else {}
        # Only override a file's sample_count when --samples was explicitly supplied.
        if args.samples is not None:
            overrides["sample_count"] = args.samples
        report = inspect_video(args.video, args.output, VideoSettings(**overrides))
    except (ValueError, TypeError, OSError, RuntimeError) as error:
        parser.error(str(error))
    print(json.dumps(asdict(report), indent=2, allow_nan=False))
    return 0 if report.status == "KEYFRAMES_SELECTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
