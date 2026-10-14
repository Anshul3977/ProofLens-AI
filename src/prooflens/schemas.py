from dataclasses import dataclass, field
from typing import Literal


@dataclass
class QualityResult:
    valid: bool
    width: int = 0
    height: int = 0
    metrics: dict[str, float] = field(default_factory=dict)
    observations: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)


@dataclass
class AlignmentResult:
    success: bool
    reason: str
    matches: int = 0
    inliers: int = 0
    inlier_ratio: float = 0.0
    overlap: float = 0.0
    homography: list[list[float]] | None = None


@dataclass
class DifferenceResult:
    changed_fraction: float
    valid_pixels: int
    regions: list[tuple[int, int, int, int]]
    lighting_offset: float
    limitations: list[str] = field(default_factory=lambda: [
        "Pixel changes may reflect lighting, viewpoint, texture, or registration error.",
        "Candidate regions do not prove damage, mismatch, fraud, or authenticity.",
    ])


@dataclass
class InspectionResult:
    status: Literal["DIFFERENCES_AVAILABLE", "QUALITY_INSUFFICIENT", "ALIGNMENT_FAILED", "INVALID_INPUT"]
    opencv_version: str
    reference_quality: QualityResult
    inspection_quality: QualityResult
    alignment: AlignmentResult | None = None
    differences: DifferenceResult | None = None
    artifacts: dict[str, str] = field(default_factory=dict)
