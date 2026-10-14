from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Initial synthetic-fixture heuristics; require real-photo calibration."""

    min_dimension: int = 128
    blur_variance: float = 50.0
    dark_pixel: int = 20
    bright_pixel: int = 245
    exposure_fraction: float = 0.45
    glare_fraction: float = 0.08
    glare_saturation: int = 35
    orb_features: int = 2500
    match_ratio: float = 0.75
    min_matches: int = 12
    min_inliers: int = 10
    min_inlier_ratio: float = 0.45
    reprojection_threshold: float = 3.0
    min_overlap: float = 0.65
    difference_threshold: int = 35
    min_region_area: float = 80.0
