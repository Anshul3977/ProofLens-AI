"""Identical-candidate keyframe baselines with explicitly labeled synthetic appearances."""
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from prooflens.video import FrameCandidate, VideoSettings, sample_video, select_keyframes
from prooflens.config import Settings


def compare_selections(candidates: list[FrameCandidate], frame_labels: dict[int, str],
                       settings: VideoSettings = VideoSettings()) -> dict:
    if not candidates:
        raise ValueError("No candidates for baseline comparison")
    uniform_indices = np.linspace(0, len(candidates) - 1, min(3, len(candidates)), dtype=int)
    methods = {
        "uniform": [candidates[int(index)] for index in uniform_indices],
        "top_quality": sorted(candidates, key=lambda frame: (-frame.score, frame.index))[:3],
        "quality_and_diversity": select_keyframes(candidates, settings),
    }
    results = {}
    available = {frame_labels[frame.index] for frame in candidates
                 if frame_labels[frame.index].startswith("appearance_")}
    full_video_available = {label for label in frame_labels.values() if label.startswith("appearance_")}
    for name, frames in methods.items():
        classes = [frame_labels[frame.index] for frame in frames]
        covered = {label for label in classes if label.startswith("appearance_")}
        results[name] = {"selected_indices": [frame.index for frame in frames],
                         "labels": classes, "selected_count": len(frames),
                         "eligible_count": sum(frame.eligible for frame in frames),
                         "quality_eligibility_precision": sum(frame.eligible for frame in frames) / len(frames) if frames else None,
                         "appearance_classes_covered": len(covered),
                         "available_appearance_classes": len(available),
                         "full_video_appearance_classes": len(full_video_available),
                         "duplicate_appearance_count": len(classes) - len(set(classes))}
    return {"scope": "labeled_synthetic_appearance_selection", "candidate_count": len(candidates),
            "methods": results, "limitations": [
                "Labeled synthetic transformations are not verified physical product viewpoints.",
                "One fixture comparison does not establish real-world selection improvement."]}


def benchmark_video(path: Path, metadata_path: Path, settings: VideoSettings = VideoSettings()) -> dict:
    labels = json.loads(metadata_path.read_text(encoding="utf-8"))
    if labels.get("synthetic") is not True:
        raise ValueError("This benchmark requires explicitly synthetic ground-truth metadata")
    start = perf_counter()
    metadata, candidates = sample_video(path, settings, Settings())
    if (metadata["width"], metadata["height"], metadata["frame_count"]) != (
            labels["width"], labels["height"], labels["frame_count"]):
        raise ValueError("Video disagrees with ground-truth metadata")
    entries = labels["frame_labels"]
    indices = [entry["index"] for entry in entries]
    if (len(entries) != metadata["frame_count"] or any(type(index) is not int for index in indices)
            or len(set(indices)) != len(indices)):
        raise ValueError("Ground truth must label every source frame exactly once")
    frame_labels = {entry["index"]: entry["label"] for entry in entries}
    if set(frame_labels) != set(range(metadata["frame_count"])):
        raise ValueError("Ground truth must label every source frame exactly once")
    report = compare_selections(candidates, frame_labels, settings)
    report.update({"source_id": labels["source_id"], "seed": labels["seed"], "metadata": metadata,
                   "settings": asdict(settings), "processing_seconds": perf_counter() - start})
    return report
