"""Create a deterministic 6-second 1080p geometric MP4; not real warehouse evidence."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from prooflens.pipeline import require_opencv5
from prooflens.synthetic import reference_image


def generate(output: Path) -> dict:
    require_opencv5()
    if output.exists():
        raise ValueError("Sample output already exists; choose a fresh path")
    output.parent.mkdir(parents=True, exist_ok=True)
    source = np.tile(reference_image(), (3, 3, 1))[:1080, :1920].copy()
    # Distinct synthetic appearances are deliberately labeled; they are not verified physical views.
    views = [source, cv2.rotate(source, cv2.ROTATE_180), cv2.flip(source, 1)]
    classes = ["blurred"] * 10 + ["appearance_A"] * 15 + ["appearance_B"] * 15 + ["appearance_C"] * 15 + ["overexposed"] * 5
    blurred = cv2.GaussianBlur(source, (31, 31), 10)
    frames = {"blurred": blurred, "appearance_A": views[0], "appearance_B": views[1],
              "appearance_C": views[2], "overexposed": np.full_like(source, 255)}
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    if not writer.isOpened():
        raise RuntimeError("OpenCV MP4 encoder unavailable")
    try:
        for label in classes:
            writer.write(frames[label])
    finally:
        writer.release()
    metadata = {"synthetic": True, "source_id": "geometric-video-v1", "seed": 2026,
                "fps": 10, "width": 1920, "height": 1080, "frame_count": 60,
                "transformations": {"appearance_A": "identity tiled source",
                                    "appearance_B": "180-degree rotation", "appearance_C": "horizontal reflection",
                                    "blurred": "Gaussian kernel 31x31, sigma 10", "overexposed": "all channels 255"},
                "frame_labels": [{"index": index, "timestamp_seconds": index / 10, "label": label}
                                 for index, label in enumerate(classes)]}
    output.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("sample_data/generated/video-inspection.mp4"))
    args = parser.parse_args()
    generate(args.output)
    print(f"Created {args.output}: 60 frames, 1920x1080, 10 FPS, 6 seconds; synthetic only")
