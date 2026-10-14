import cv2
import numpy as np

from prooflens.config import Settings
from prooflens.schemas import DifferenceResult
from prooflens.vision.quality import Image


def inspect_differences(reference: Image, aligned: Image, valid_mask: np.ndarray,
                        settings: Settings = Settings()) -> tuple[DifferenceResult, Image, np.ndarray]:
    if reference.shape != aligned.shape or valid_mask.shape != reference.shape[:2]:
        raise ValueError("Aligned images and validity mask must share dimensions.")
    valid = valid_mask > 0
    if not np.any(valid):
        raise ValueError("No valid overlap to inspect.")
    ref = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY).astype(np.float32)
    seen = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY).astype(np.float32)
    offset = float(np.median(ref[valid] - seen[valid]))
    delta = np.abs(ref - np.clip(seen + offset, 0, 255))
    evidence = ((delta > settings.difference_threshold) & valid).astype(np.uint8) * 255
    kernel = np.ones((3, 3), np.uint8)
    evidence = cv2.morphologyEx(evidence, cv2.MORPH_OPEN, kernel)
    evidence = cv2.morphologyEx(evidence, cv2.MORPH_CLOSE, kernel)
    evidence[~valid] = 0
    contours, _ = cv2.findContours(evidence, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) >= settings.min_region_area]
    filtered = np.zeros_like(evidence)
    cv2.drawContours(filtered, contours, -1, 255, cv2.FILLED)
    # Contour filling selects retained regions, but must not invent evidence
    # inside holes or other pixels absent from the post-morphology mask.
    filtered = cv2.bitwise_and(filtered, evidence)
    filtered[~valid] = 0
    regions = sorted([cv2.boundingRect(c) for c in contours])
    overlay = aligned.copy()
    overlay[filtered > 0] = (0.5 * overlay[filtered > 0] + np.array([0, 0, 127])).astype(np.uint8)
    for x, y, w, h in regions:
        cv2.rectangle(overlay, (x, y), (x + w - 1, y + h - 1), (0, 0, 255), 2)
    result = DifferenceResult(float(np.count_nonzero(filtered) / np.count_nonzero(valid)),
                              int(np.count_nonzero(valid)), regions, offset)
    return result, overlay, filtered
