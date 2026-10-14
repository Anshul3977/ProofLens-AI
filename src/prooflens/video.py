"""Bounded local MP4 sampling; appearance diversity is not physical viewpoint proof."""
from dataclasses import asdict, dataclass, field
from itertools import combinations
import json
from pathlib import Path
from time import perf_counter
from typing import Literal

import cv2
import numpy as np

from prooflens.config import Settings
from prooflens.pipeline import require_opencv5
from prooflens.schemas import QualityResult
from prooflens.vision.quality import Image, inspect_image_quality


@dataclass(frozen=True)
class VideoSettings:
    sample_count: int = 24
    max_file_bytes: int = 100 * 1024 * 1024
    max_pixels: int = 3840 * 2160
    max_duration_seconds: float = 15.0
    max_decoded_frames: int = 900
    max_sample_bytes: int = 256 * 1024 * 1024
    diversity_threshold: float = 0.04
    diversity_weight: float = 0.6

    def __post_init__(self) -> None:
        for name in ("sample_count", "max_file_bytes", "max_pixels", "max_decoded_frames", "max_sample_bytes"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.sample_count > 60:
            raise ValueError("sample_count cannot exceed 60")
        if not np.isfinite(self.max_duration_seconds) or self.max_duration_seconds <= 0:
            raise ValueError("max_duration_seconds must be positive and finite")
        for name in ("diversity_threshold", "diversity_weight"):
            value = getattr(self, name)
            if not np.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be finite in [0,1]")


@dataclass
class FrameCandidate:
    index: int
    timestamp_seconds: float
    quality: QualityResult
    score: float
    eligible: bool
    image: Image = field(repr=False)
    descriptor: np.ndarray = field(repr=False)

    def summary(self) -> dict:
        return {"index": self.index, "timestamp_seconds": self.timestamp_seconds,
                "quality": asdict(self.quality), "quality_score": self.score,
                "eligible": self.eligible}


@dataclass
class VideoReport:
    status: Literal["KEYFRAMES_SELECTED", "INSUFFICIENT_KEYFRAMES", "INVALID_VIDEO"]
    opencv_version: str
    reason: str
    metadata: dict = field(default_factory=dict)
    settings: dict = field(default_factory=dict)
    samples: list[dict] = field(default_factory=list)
    selected: list[dict] = field(default_factory=list)
    processing_seconds: float = 0.0
    limitations: list[str] = field(default_factory=lambda: [
        "Appearance diversity is a thumbnail heuristic, not verified physical viewpoint diversity.",
        "Quality thresholds need real-video calibration; white surfaces may resemble glare.",
        "Timestamps use frame index / reported FPS; variable-frame-rate timing may be approximate.",
        "Local native decoder is not sandboxed; limits do not harden this for public uploads.",
    ])


def sampling_indices(frame_count: int, sample_count: int) -> list[int]:
    if frame_count <= 0 or sample_count <= 0:
        raise ValueError("Frame and sample counts must be positive")
    return np.linspace(0, frame_count - 1, min(frame_count, sample_count), dtype=int).tolist()


def score_frame(image: Image, index: int, fps: float, settings: Settings = Settings()) -> FrameCandidate:
    quality = inspect_image_quality(image, settings)
    if not quality.valid or not np.isfinite(fps) or fps <= 0:
        raise ValueError("Scoring requires a valid image and positive finite FPS")
    metrics = quality.metrics
    sharp = metrics["laplacian_variance"]
    score = sharp / (sharp + max(settings.blur_variance, 1.0))
    score *= 1 - max(metrics["dark_fraction"], metrics["bright_fraction"])
    score *= 1 - metrics["potential_glare_fraction"]
    # Small normalized luminance descriptor; native frame remains untouched for saving.
    thumbnail = cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (160, 90), interpolation=cv2.INTER_AREA)
    descriptor = thumbnail.astype(np.float32) / 255.0
    return FrameCandidate(index, index / fps, quality, float(score), not quality.recommended_actions,
                          image, descriptor)


def appearance_distance(first: FrameCandidate, second: FrameCandidate) -> float:
    # RMS gives localized product detail more weight than uniform background.
    return float(np.sqrt(np.mean((first.descriptor - second.descriptor) ** 2)))


def select_keyframes(candidates: list[FrameCandidate], settings: VideoSettings = VideoSettings()) -> list[FrameCandidate]:
    eligible = sorted([candidate for candidate in candidates if candidate.eligible],
                      key=lambda frame: (-frame.score, frame.index))
    remaining = eligible.copy()
    selected: list[FrameCandidate] = []
    if remaining:
        selected.append(remaining.pop(0))
    while remaining and len(selected) < 3:
        ranked = []
        for candidate in remaining:
            if any(candidate.index == chosen.index for chosen in selected):
                continue
            distance = min(appearance_distance(candidate, chosen) for chosen in selected)
            if distance <= settings.diversity_threshold:
                continue
            utility = (1 - settings.diversity_weight) * candidate.score + settings.diversity_weight * distance
            ranked.append((utility, -candidate.index, candidate))
        if not ranked:
            break
        winner = max(ranked, key=lambda entry: entry[:2])[2]
        selected.append(winner)
        remaining = [candidate for candidate in remaining if candidate is not winner]
    if len(selected) < 3:
        # The best-quality seed can block an otherwise feasible complementary set.
        # Only repair insufficient greedy results; normal successful selection stays unchanged.
        # Sampling is bounded to 60 candidates, hence at most 34,220 possible triples.
        distances = {(i, j): appearance_distance(first, second)
                     for i, first in enumerate(eligible)
                     for j, second in enumerate(eligible) if i < j}
        for size in range(3, len(selected), -1):
            best_group = None
            best_utility = -float("inf")
            for group in combinations(range(len(eligible)), size):
                frames = [eligible[index] for index in group]
                if len({frame.index for frame in frames}) != size:
                    continue
                minimum = min(distances[pair] for pair in combinations(group, 2))
                if minimum <= settings.diversity_threshold:
                    continue
                utility = ((1 - settings.diversity_weight) * sum(frame.score for frame in frames) / size
                           + settings.diversity_weight * minimum)
                if utility > best_utility:
                    best_group, best_utility = frames, utility
            if best_group is not None:
                selected = best_group
                break
    return selected


def sample_video(path: Path, settings: VideoSettings, quality_settings: Settings) -> tuple[dict, list[FrameCandidate]]:
    path = path.resolve(strict=True)
    if not path.is_file() or path.suffix.lower() != ".mp4":
        raise ValueError("Provide a local MP4 file")
    if not 0 < path.stat().st_size <= settings.max_file_bytes:
        raise ValueError("Video is empty or exceeds the file-size limit")
    with path.open("rb") as stream:
        if stream.read(12)[4:8] != b"ftyp":
            raise ValueError("Missing MP4 ftyp signature")
    capture = cv2.VideoCapture(str(path), cv2.CAP_FFMPEG)
    try:
        if not capture.isOpened():
            raise ValueError("OpenCV could not open the MP4")
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        count = float(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        width = float(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = float(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if not all(np.isfinite(value) and value > 0 for value in (fps, count, width, height)):
            raise ValueError("Invalid video metadata")
        frame_count, w, h = int(count), int(width), int(height)
        if frame_count > settings.max_decoded_frames or count / fps > settings.max_duration_seconds:
            raise ValueError("Video exceeds duration or frame-count limits")
        if w * h > settings.max_pixels:
            raise ValueError("Video dimensions exceed the pixel limit")
        indices = sampling_indices(frame_count, settings.sample_count)
        if len(indices) * w * h * 3 > settings.max_sample_bytes:
            raise ValueError("Retained samples exceed the memory budget; reduce sample_count")
        chosen = set(indices)
        candidates = []
        actual_bytes = 0
        for index in range(frame_count):
            if not capture.grab():
                raise ValueError(f"Video decode ended early at frame {index}")
            if index in chosen:
                ok, frame = capture.retrieve()
                if not ok or frame is None:
                    raise ValueError(f"Could not decode sampled frame {index}")
                if frame.shape[:2] != (h, w) or frame.nbytes > settings.max_pixels * 3:
                    raise ValueError("Decoded dimensions disagree with validated metadata")
                actual_bytes += frame.nbytes
                if actual_bytes > settings.max_sample_bytes:
                    raise ValueError("Decoded samples exceed memory budget")
                candidates.append(score_frame(frame, index, fps, quality_settings))
        if capture.grab():
            raise ValueError("Video contains more frames than declared; refusing unbounded decode")
        return {"width": w, "height": h, "fps": fps, "frame_count": frame_count,
                "duration_seconds": frame_count / fps, "sampled_indices": indices,
                "target_duration_met": 5 <= frame_count / fps <= 10}, candidates
    finally:
        capture.release()


def inspect_video(path: Path, output: Path, settings: VideoSettings = VideoSettings(),
                  quality_settings: Settings = Settings()) -> VideoReport:
    require_opencv5()
    start = perf_counter()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("Output directory must be empty to avoid stale evidence")
    output.mkdir(parents=True, exist_ok=True)
    report = VideoReport("INVALID_VIDEO", cv2.__version__, "", settings={
        "video": asdict(settings), "quality": asdict(quality_settings)})
    try:
        metadata, candidates = sample_video(path, settings, quality_settings)
    except (ValueError, OSError, cv2.error) as error:
        report.reason = str(error)
    else:
        report.metadata = metadata
        report.samples = [frame.summary() for frame in candidates]
        selected = select_keyframes(candidates, settings)
        report.status = "KEYFRAMES_SELECTED" if len(selected) == 3 else "INSUFFICIENT_KEYFRAMES"
        report.reason = ("Three quality-eligible frames with complementary appearance selected."
                         if len(selected) == 3 else "Not enough quality-eligible, visually distinct frames; capture additional viewpoints.")
        for rank, frame in enumerate(selected, 1):
            target = output / f"keyframe_{rank:02d}_frame_{frame.index:06d}.png"
            ok, encoded = cv2.imencode(".png", frame.image)
            if not ok:
                raise OSError("Could not encode selected keyframe")
            target.write_bytes(encoded.tobytes())
            summary = frame.summary()
            summary.update({"rank": rank, "path": str(target.resolve()),
                            "selection_reason": "Highest quality eligible frame in selected complementary set" if rank == 1 else
                            "Quality/diversity selection with minimum distance to all previous selections",
                            "minimum_appearance_distance": None if rank == 1 else
                            min(appearance_distance(frame, other) for other in selected[:rank - 1])})
            report.selected.append(summary)
    # Includes decode/scoring/PNG writes; excludes final JSON serialization/write.
    report.processing_seconds = perf_counter() - start
    (output / "report.json").write_text(json.dumps(asdict(report), indent=2, allow_nan=False), encoding="utf-8")
    return report
