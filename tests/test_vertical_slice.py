import json
import cv2
import numpy as np
import pytest

from prooflens.pipeline import inspect_pair, read_image, require_opencv5
from prooflens.synthetic import reference_image, perspective_image
from prooflens.vision.quality import inspect_image_quality
from prooflens.vision.alignment import align_images
from prooflens.vision.differences import inspect_differences


def test_opencv5_runtime():
    require_opencv5()
    cv2.QRCodeDetector()


def test_quality_rejects_invalid_and_detects_blur():
    assert not inspect_image_quality(None).valid
    sharp = reference_image()
    assert not inspect_image_quality(sharp).recommended_actions
    blurry = inspect_image_quality(cv2.GaussianBlur(sharp, (31, 31), 10))
    assert blurry.metrics["laplacian_variance"] < inspect_image_quality(sharp).metrics["laplacian_variance"]
    assert any("focus" in a for a in blurry.recommended_actions)


@pytest.mark.parametrize("value, metric", [(0, "dark_fraction"), (255, "bright_fraction")])
def test_exposure(value, metric):
    result = inspect_image_quality(np.full((200, 200, 3), value, np.uint8))
    assert result.metrics[metric] == 1.0
    assert result.recommended_actions


def test_perspective_alignment():
    reference = reference_image()
    result, warped, mask = align_images(reference, perspective_image(reference))
    assert result.success, result
    assert result.inliers >= 10 and result.overlap >= 0.65
    assert warped.shape == reference.shape
    assert mask.shape == reference.shape[:2]


def test_alignment_failure_is_structured():
    result, warped, mask = align_images(reference_image(), np.full((480, 640, 3), 130, np.uint8))
    assert not result.success and result.reason
    assert warped is None and mask is None


def test_known_change_and_invalid_border():
    reference = reference_image()
    modified = reference.copy()
    modified[280:340, 390:465] = 30
    modified[:15] = 0
    mask = np.full(reference.shape[:2], 255, np.uint8)
    mask[:20] = 0
    result, overlay, evidence = inspect_differences(reference, modified, mask)
    assert 0.01 < result.changed_fraction < 0.03
    assert len(result.regions) == 1
    assert np.any(evidence[280:340, 390:465]) and not np.any(evidence[:20])
    assert overlay.shape == reference.shape


def test_lighting_offset():
    reference = reference_image()
    brighter = (reference.astype(np.int16) + 15).astype(np.uint8)
    result, _, _ = inspect_differences(reference, brighter, np.full(reference.shape[:2], 255, np.uint8))
    assert result.changed_fraction == 0 and result.lighting_offset == -15


def test_saved_matching_artifacts(tmp_path):
    reference = reference_image()
    result = inspect_pair(reference, reference.copy(), tmp_path)
    assert result.status == "DIFFERENCES_AVAILABLE"
    assert result.differences.changed_fraction == 0
    saved = json.loads((tmp_path / "result.json").read_text())
    assert saved["opencv_version"].startswith("5.")
    assert read_image(tmp_path / "overlay.png") is not None


def test_perspective_through_quality_gate(tmp_path):
    reference = reference_image()
    result = inspect_pair(reference, perspective_image(reference), tmp_path)
    assert result.status == "DIFFERENCES_AVAILABLE"
    assert result.alignment.success


def test_quality_stops_slice(tmp_path):
    reference = reference_image()
    result = inspect_pair(reference, cv2.GaussianBlur(reference, (31, 31), 10), tmp_path)
    assert result.status == "QUALITY_INSUFFICIENT" and result.alignment is None


def test_invalid_file(tmp_path):
    path = tmp_path / "bad.png"
    path.write_text("not an image")
    assert read_image(path) is None
    assert inspect_pair(None, reference_image(), tmp_path / "result").status == "INVALID_INPUT"


def test_empty_overlap():
    reference = reference_image()
    with pytest.raises(ValueError, match="No valid overlap"):
        inspect_differences(reference, reference, np.zeros(reference.shape[:2], np.uint8))


def test_ring_change_preserves_unchanged_interior():
    reference = np.full((240, 240, 3), 130, np.uint8)
    inspection = reference.copy()
    cv2.rectangle(inspection, (50, 50), (190, 190), (30, 30, 30), 15)
    valid = np.full(reference.shape[:2], 255, np.uint8)
    result, overlay, evidence = inspect_differences(reference, inspection, valid)
    actual_change = np.any(reference != inspection, axis=2)
    assert len(result.regions) == 1
    assert evidence[50, 120] == 255
    assert evidence[120, 120] == 0
    assert not np.any((evidence > 0) & ~actual_change)
    np.testing.assert_array_equal(overlay[100:140, 100:140], inspection[100:140, 100:140])
    assert result.changed_fraction == np.count_nonzero(evidence) / evidence.size
