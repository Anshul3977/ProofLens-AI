"""Self-created deterministic geometric fixtures, not real customer evidence."""
import cv2
import numpy as np
from prooflens.vision.quality import Image


def reference_image() -> Image:
    rng = np.random.default_rng(2026)
    image = np.full((480, 640, 3), 130, np.uint8)
    for _ in range(160):
        x, y = rng.integers([20, 20], [610, 450])
        color = tuple(int(v) for v in rng.integers(35, 220, 3))
        cv2.circle(image, (int(x), int(y)), int(rng.integers(3, 12)), color, -1)
    cv2.rectangle(image, (50, 50), (590, 430), (55, 90, 180), 3)
    cv2.putText(image, "PROOFLENS SYNTHETIC", (70, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (210, 210, 210), 2)
    return image


def perspective_image(image: Image) -> Image:
    h, w = image.shape[:2]
    source = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
    target = source + np.float32([[15, 10], [-15, 15], [-5, -10], [10, -15]])
    return cv2.warpPerspective(image, cv2.getPerspectiveTransform(source, target), (w, h), borderValue=(130, 130, 130))
