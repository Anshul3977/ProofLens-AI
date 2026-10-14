import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from prooflens.synthetic import reference_image
from prooflens.video import VideoSettings, inspect_video, sampling_indices, score_frame, select_keyframes


def write_mp4(path: Path, frames: list[np.ndarray], fps: float = 10):
    h, w = frames[0].shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    assert writer.isOpened(), "Required MP4 encoder unavailable"
    try:
        for frame in frames:
            writer.write(frame)
    finally:
        writer.release()


def views():
    image = reference_image()
    return [image, cv2.rotate(image, cv2.ROTATE_180), cv2.flip(image, 1)]


def test_sampling_bounds_and_spacing():
    assert sampling_indices(10, 4) == [0, 3, 6, 9]
    assert sampling_indices(2, 24) == [0, 1]
    assert sampling_indices(1, 1) == [0]
    with pytest.raises(ValueError):
        sampling_indices(0, 3)


def test_quality_scoring_and_rejection():
    image = reference_image()
    sharp = score_frame(image, 10, 10)
    blurred = score_frame(cv2.GaussianBlur(image, (31, 31), 10), 0, 10)
    bright = score_frame(np.full_like(image, 255), 0, 10)
    assert sharp.eligible and 0 <= blurred.score < sharp.score <= 1
    assert not blurred.eligible and not bright.eligible
    assert sharp.timestamp_seconds == 1


def test_selection_quality_and_diversity():
    images = views()
    candidates = [score_frame(image, index, 10) for index, image in enumerate(images)]
    candidates += [score_frame(images[0].copy(), 3, 10),
                   score_frame(cv2.GaussianBlur(images[1], (31, 31), 10), 4, 10)]
    selected = select_keyframes(candidates)
    assert len(selected) == 3
    assert {frame.index for frame in selected} == {0, 1, 2}
    assert all(frame.eligible for frame in selected)
    assert [frame.index for frame in select_keyframes(candidates)] == [frame.index for frame in selected]


def test_static_and_all_bad_selection():
    image = reference_image()
    assert len(select_keyframes([score_frame(image.copy(), i, 10) for i in range(5)])) == 1
    assert select_keyframes([score_frame(np.full_like(image, 0), 0, 10)]) == []


def test_mp4_sampling_and_native_saved_images(tmp_path):
    path = tmp_path / "views.mp4"
    images = views()
    write_mp4(path, [images[i // 10] for i in range(30)])
    report = inspect_video(path, tmp_path / "out", VideoSettings(sample_count=9))
    assert report.status == "KEYFRAMES_SELECTED", report.reason
    assert report.metadata["sampled_indices"] == sampling_indices(30, 9)
    assert len(report.samples) == 9 and len(report.selected) == 3
    assert report.processing_seconds > 0
    for frame in report.selected:
        saved = cv2.imread(frame["path"])
        assert saved.shape == (480, 640, 3)
    persisted = json.loads((tmp_path / "out/report.json").read_text())
    assert persisted["opencv_version"] == "5.0.0"


def test_1080p_detail_survives_diversity_descriptor(tmp_path):
    source = np.tile(reference_image(), (3, 3, 1))[:1080, :1920].copy()
    images = [source, cv2.rotate(source, cv2.ROTATE_180), cv2.flip(source, 1)]
    path = tmp_path / "1080p.mp4"
    write_mp4(path, [images[index // 2] for index in range(6)], fps=1)
    report = inspect_video(path, tmp_path / "out", VideoSettings(sample_count=6))
    assert report.status == "KEYFRAMES_SELECTED"
    assert report.metadata["target_duration_met"]
    assert {frame["index"] // 2 for frame in report.selected} == {0, 1, 2}
    capture = cv2.VideoCapture(str(path))
    try:
        decoded = []
        for _ in range(6):
            ok, frame = capture.read()
            assert ok
            decoded.append(frame)
        for selected in report.selected:
            saved = cv2.imread(selected["path"])
            assert saved.shape == (1080, 1920, 3)
            np.testing.assert_array_equal(saved, decoded[selected["index"]])
    finally:
        capture.release()


def test_truncated_decode_is_structured_and_capture_released(tmp_path, monkeypatch):
    path = tmp_path / "truncated.mp4"
    path.write_bytes(b"\x00\x00\x00\x18ftypisom")

    class Capture:
        released = False

        def isOpened(self):
            return True

        def get(self, prop):
            return {cv2.CAP_PROP_FPS: 10, cv2.CAP_PROP_FRAME_COUNT: 3,
                    cv2.CAP_PROP_FRAME_WIDTH: 640, cv2.CAP_PROP_FRAME_HEIGHT: 480}[prop]

        def grab(self):
            return False

        def release(self):
            self.released = True

    capture = Capture()
    monkeypatch.setattr(cv2, "VideoCapture", lambda *args: capture)
    report = inspect_video(path, tmp_path / "out")
    assert report.status == "INVALID_VIDEO" and "ended early" in report.reason
    assert capture.released


@pytest.mark.parametrize("kind", ["missing", "empty", "garbage", "fake_header", "wrong_suffix"])
def test_invalid_videos_are_structured(tmp_path, kind):
    path = tmp_path / ("bad.avi" if kind == "wrong_suffix" else "bad.mp4")
    if kind != "missing":
        path.write_bytes(b"\x00\x00\x00\x18ftypisomgarbage" if kind == "fake_header" else
                         b"garbage" if kind in ("garbage", "wrong_suffix") else b"")
    report = inspect_video(path, tmp_path / "out")
    assert report.status == "INVALID_VIDEO" and report.reason and not report.selected
    assert (tmp_path / "out/report.json").exists()


@pytest.mark.parametrize("limits", [{"max_file_bytes": 1}, {"max_pixels": 100},
                                  {"max_decoded_frames": 2}, {"max_duration_seconds": 0.1},
                                  {"max_sample_bytes": 100}])
def test_video_resource_limits(tmp_path, limits):
    path = tmp_path / "input.mp4"
    write_mp4(path, [reference_image()] * 5)
    report = inspect_video(path, tmp_path / "out", VideoSettings(**limits))
    assert report.status == "INVALID_VIDEO" and not report.selected


def test_short_static_video_and_output_reuse(tmp_path):
    path = tmp_path / "single.mp4"
    write_mp4(path, [reference_image()])
    report = inspect_video(path, tmp_path / "out")
    assert report.status == "INSUFFICIENT_KEYFRAMES" and len(report.selected) == 1
    assert not report.metadata["target_duration_met"]
    with pytest.raises(ValueError, match="empty"):
        inspect_video(path, tmp_path / "out")


@pytest.mark.parametrize("kwargs", [{"sample_count": 0}, {"sample_count": 61},
                                  {"sample_count": 1.5}, {"max_duration_seconds": float("nan")},
                                  {"diversity_weight": -0.1}, {"diversity_threshold": 2}])
def test_bad_settings(kwargs):
    with pytest.raises(ValueError):
        VideoSettings(**kwargs)
