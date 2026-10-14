"""Deterministic, source-grouped geometric fixtures (not fraud incidents)."""
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "eval_data/synthetic_manifest.json"


def load_manifest(path: Path | None = None) -> dict:
    manifest = json.loads((path or MANIFEST).read_text(encoding="utf-8"))
    ids, splits = set(), {}
    for case in manifest["cases"]:
        if case["id"] in ids:
            raise ValueError("Duplicate case identifier")
        ids.add(case["id"])
        if case["split"] not in {"development", "holdout"}:
            raise ValueError("Unknown split")
        # Both original sources in a mismatched pair must remain in one split.
        for source in {case["source_id"], case.get("inspection_source_id", case["source_id"])}:
            if source in splits and splits[source] != case["split"]:
                raise ValueError("Source leakage across splits")
            splits[source] = case["split"]
    return manifest


def source_image(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    image = np.full((360, 480, 3), 130, np.uint8)
    for _ in range(200):
        x, y = rng.integers([15, 15], [465, 345])
        color = tuple(int(v) for v in rng.integers(35, 220, 3))
        cv2.circle(image, (int(x), int(y)), int(rng.integers(3, 10)), color, -1)
    cv2.rectangle(image, (30, 30), (450, 330), (55, 90, 180), 3)
    cv2.putText(image, f"SOURCE {seed}", (55, 180), cv2.FONT_HERSHEY_SIMPLEX, .65, (210, 210, 210), 2)
    return image


def render_case(case: dict) -> tuple[np.ndarray, np.ndarray]:
    reference = source_image(case["source_seed"])
    image = source_image(case.get("inspection_source_seed", case["source_seed"]))
    # Case seed is fixed even though parameters are explicitly recorded.
    rng = np.random.default_rng(case["seed"])
    for transformation in case["transformations"]:
        kind = transformation["type"]
        if kind == "blur":
            image = cv2.GaussianBlur(image, (transformation["kernel"],) * 2, transformation["sigma"])
        elif kind == "exposure":
            image = np.clip(image.astype(np.float32) * transformation["gain"], 0, 255).astype(np.uint8)
        elif kind in {"glare", "visible_difference"}:
            x, y, w, h = transformation["rect"]
            image[y:y+h, x:x+w] = transformation["bgr"]
        elif kind == "perspective":
            h, w = image.shape[:2]
            corners = np.float32([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]])
            target = corners + np.float32(transformation["corner_offsets"])
            image = cv2.warpPerspective(image, cv2.getPerspectiveTransform(corners, target), (w, h), borderValue=(130, 130, 130))
        elif kind == "sensor_noise":
            noise = rng.normal(0, transformation["sigma"], image.shape)
            image = np.clip(image.astype(np.float64) + noise, 0, 255).astype(np.uint8)
        else:
            raise ValueError(f"Unknown transformation: {kind}")
    return reference, image
