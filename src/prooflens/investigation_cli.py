import argparse
import json
from pathlib import Path

from prooflens.investigation import investigate_video, resume_investigation
from prooflens.video import VideoSettings


def main() -> int:
    parser = argparse.ArgumentParser(description="ProofLens local bounded video investigation")
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("video", type=Path)
    start.add_argument("--catalog", type=Path, required=True)
    start.add_argument("--identifier")
    start.add_argument("--samples", type=int, default=24)
    start.add_argument("--workspace", type=Path, default=Path("artifacts/investigations"))
    resume = commands.add_parser("resume")
    resume.add_argument("investigation_id")
    resume.add_argument("image", type=Path)
    resume.add_argument("--workspace", type=Path, default=Path("artifacts/investigations"))
    resume.add_argument("--catalog", type=Path)
    resume.add_argument("--identifier")
    args = parser.parse_args()
    try:
        if args.command == "start":
            result = investigate_video(args.video, args.catalog, args.workspace, args.identifier,
                                       VideoSettings(sample_count=args.samples))
        else:
            result = resume_investigation(args.workspace, args.investigation_id, args.image,
                                          args.catalog, args.identifier)
    except (OSError, ValueError, TypeError, RuntimeError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
