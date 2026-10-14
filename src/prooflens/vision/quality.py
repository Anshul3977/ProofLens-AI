import cv2
import numpy as np
from numpy.typing import NDArray

from prooflens.config import Settings
from prooflens.schemas import QualityResult

Image = NDArray[np.uint8]


def inspect_image_quality(image: Image | None, settings: Settings = Settings()) -> QualityResult:
    if (image is None or not isinstance(image, np.ndarray) or image.dtype != np.uint8
            or image.ndim != 3 or image.shape[2] != 3 or image.size == 0):
        return QualityResult(False, observations=["Expected a nonempty uint8 BGR image."],
                             recommended_actions=["Provide a readable color image."])
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    metrics = {
        "laplacian_variance": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        "dark_fraction": float(np.mean(gray <= settings.dark_pixel)),
        "bright_fraction": float(np.mean(gray >= settings.bright_pixel)),
        "potential_glare_fraction": float(np.mean(
            (hsv[:, :, 2] >= settings.bright_pixel) & (hsv[:, :, 1] <= settings.glare_saturation))),
    }
    observations, actions = [], []
    checks = [
        (min(height, width) < settings.min_dimension, "Image dimensions are too small.", "Provide a higher-resolution image."),
        (metrics["laplacian_variance"] < settings.blur_variance, "Low edge detail: possible blur or textureless surface.", "Retake in focus with visible product detail."),
        (metrics["dark_fraction"] > settings.exposure_fraction, "Potential underexposure.", "Retake with more even lighting."),
        (metrics["bright_fraction"] > settings.exposure_fraction, "Potential overexposure.", "Reduce exposure and preserve surface detail."),
        (metrics["potential_glare_fraction"] > settings.glare_fraction, "Bright low-saturation pixels: potential glare or white surface.", "Reduce reflections or confirm that the bright area is the product surface."),
    ]
    for triggered, observation, action in checks:
        if triggered:
            observations.append(observation)
            actions.append(action)
    return QualityResult(True, width, height, metrics, observations, actions)
