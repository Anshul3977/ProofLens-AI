import argparse
from dataclasses import asdict
import json
from pathlib import Path
from uuid import uuid4

from prooflens.config import Settings
from prooflens.pipeline import inspect_pair, read_image


def main() -> int:
    parser = argparse.ArgumentParser(description="ProofLens local Phase 1 image comparison")
    parser.add_argument("reference", type=Path)
    parser.add_argument("inspection", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts") / uuid4().hex)
    parser.add_argument("--config", type=Path, help="JSON object containing Settings overrides")
    args = parser.parse_args()
    try:
        settings = Settings(**json.loads(args.config.read_text(encoding="utf-8"))) if args.config else Settings()
        if args.output.exists() and any(args.output.iterdir()):
            parser.error("Output directory must be empty; use a fresh path to avoid stale evidence.")
        result = inspect_pair(read_image(args.reference), read_image(args.inspection), args.output, settings)
    except (ValueError, TypeError, OSError, RuntimeError) as error:
        parser.error(str(error))
    print(json.dumps(asdict(result), indent=2, allow_nan=False))
    return 0 if result.status == "DIFFERENCES_AVAILABLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
