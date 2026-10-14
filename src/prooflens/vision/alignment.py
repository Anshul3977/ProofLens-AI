from typing import Protocol

import cv2
import numpy as np

from prooflens.config import Settings
from prooflens.schemas import AlignmentResult
from prooflens.vision.quality import Image


class Matcher(Protocol):
    def correspondences(self, reference: Image, inspection: Image) -> tuple[np.ndarray, np.ndarray]: ...


class ORBMatcher:
    def __init__(self, settings: Settings):
        self.settings = settings

    def correspondences(self, reference: Image, inspection: Image) -> tuple[np.ndarray, np.ndarray]:
        orb = cv2.ORB_create(nfeatures=self.settings.orb_features)
        kr, dr = orb.detectAndCompute(cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY), None)
        ki, di = orb.detectAndCompute(cv2.cvtColor(inspection, cv2.COLOR_BGR2GRAY), None)
        if dr is None or di is None:
            return np.empty((0, 2), np.float32), np.empty((0, 2), np.float32)
        pairs = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(di, dr, k=2)
        candidates = sorted([a for pair in pairs if len(pair) == 2
                             for a, b in [pair] if a.distance < self.settings.match_ratio * b.distance],
                            key=lambda m: m.distance)
        # One-to-one destinations avoid multiple features voting for one reference point.
        good, used = [], set()
        for match in candidates:
            if match.trainIdx not in used:
                good.append(match)
                used.add(match.trainIdx)
        return (np.float32([ki[m.queryIdx].pt for m in good]).reshape(-1, 2),
                np.float32([kr[m.trainIdx].pt for m in good]).reshape(-1, 2))


def align_images(reference: Image, inspection: Image, settings: Settings = Settings(),
                 matcher: Matcher | None = None) -> tuple[AlignmentResult, Image | None, np.ndarray | None]:
    source, target = (matcher or ORBMatcher(settings)).correspondences(reference, inspection)
    result = AlignmentResult(False, "Too few reliable correspondences.", matches=len(source))
    if len(source) < settings.min_matches:
        return result, None, None
    # Robust-estimation seed for reproducible fixtures, not a claim of universal determinism.
    cv2.setRNGSeed(42)
    matrix, mask = cv2.findHomography(source, target, cv2.RANSAC, settings.reprojection_threshold)
    if matrix is None or mask is None or not np.isfinite(matrix).all():
        result.reason = "Homography estimation failed."
        return result, None, None
    result.inliers = int(mask.sum())
    result.inlier_ratio = result.inliers / result.matches
    if result.inliers < settings.min_inliers or result.inlier_ratio < settings.min_inlier_ratio:
        result.reason = "Insufficient homography inlier support."
        return result, None, None
    ih, iw = inspection.shape[:2]
    rh, rw = reference.shape[:2]
    corners = np.float32([[0, 0], [iw - 1, 0], [iw - 1, ih - 1], [0, ih - 1]])
    denominator = np.c_[corners, np.ones(4)] @ matrix[2]
    if np.any(np.abs(denominator) < 1e-8) or not (np.all(denominator > 0) or np.all(denominator < 0)):
        result.reason = "Projective horizon crosses the image."
        return result, None, None
    projected = cv2.perspectiveTransform(corners.reshape(-1, 1, 2), matrix)
    area_ratio = cv2.contourArea(projected) / (rh * rw)
    if (not np.isfinite(projected).all() or not cv2.isContourConvex(projected)
            or not 0.25 <= area_ratio <= 4.0 or cv2.contourArea(projected, oriented=True) <= 0):
        result.reason = "Implausible or reflected image geometry."
        return result, None, None
    # Also reject spatially concentrated inlier support.
    inlier_target = target[mask.ravel().astype(bool)]
    if cv2.contourArea(cv2.convexHull(inlier_target)) / (rh * rw) < 0.05:
        result.reason = "Inliers cover too little of the reference."
        return result, None, None
    valid = cv2.warpPerspective(np.full((ih, iw), 255, np.uint8), matrix, (rw, rh), flags=cv2.INTER_NEAREST)
    valid = cv2.erode(valid, np.ones((5, 5), np.uint8), borderType=cv2.BORDER_CONSTANT, borderValue=0)
    result.overlap = float(np.mean(valid > 0))
    if result.overlap < settings.min_overlap:
        result.reason = "Insufficient overlapping visible area."
        return result, None, None
    warped = cv2.warpPerspective(inspection, matrix, (rw, rh))
    result.success, result.reason = True, "ORB/RANSAC alignment passed heuristic checks."
    result.homography = matrix.tolist()
    return result, warped, valid
