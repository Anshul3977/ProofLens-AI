import json
from pathlib import Path

import cv2

from prooflens.agent.controller import InspectionAgent
from prooflens.investigation import investigate_video, resolve_keyframes, resume_investigation
from prooflens.catalog.repository import ReferenceCatalog
from prooflens.synthetic import reference_image
from prooflens.video import VideoReport


def setup_catalog(tmp_path):
    image = reference_image()
    cv2.imwrite(str(tmp_path / "reference.png"), image)
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({"references": [{"identifier": "product-001", "image": "reference.png"}]}))
    return image, path


def write_video(path, image):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (640, 480))
    assert writer.isOpened()
    try:
        for _ in range(10):
            writer.write(image)
    finally:
        writer.release()


def test_actual_mp4_to_catalog_to_agent(tmp_path):
    reference, catalog = setup_catalog(tmp_path)
    video = tmp_path / "matching.mp4"
    write_video(video, reference)
    report = investigate_video(video, catalog, tmp_path / "workspace", "product-001")
    assert report["video"]["status"] == "INSUFFICIENT_KEYFRAMES"  # static scene has one view
    assert report["reference_resolution"]["status"] == "RESOLVED"
    assert report["investigation"]["verdict"] == "consistent_with_reference"
    assert not report["investigation"]["human_review_required"]
    assert Path(report["report_path"]).exists()
    tools = [step["tool"] for step in report["investigation"]["trace"]]
    assert "alignment" in tools and "differences" in tools


def test_unknown_reference_manual_resume_same_investigation(tmp_path):
    reference, catalog = setup_catalog(tmp_path)
    video = tmp_path / "input.mp4"
    write_video(video, reference)
    workspace = tmp_path / "workspace"
    report = investigate_video(video, catalog, workspace, "unknown")
    assert report["reference_resolution"]["status"] == "UNKNOWN_IDENTIFIER"
    current = report["investigation"]
    assert current["state"] == "manual_resolution"
    followup = resume_investigation(workspace, current["id"], tmp_path / "reference.png", catalog, "product-001")
    assert followup["investigation"]["id"] == current["id"]
    assert followup["investigation"]["verdict"] == "consistent_with_reference"
    assert len(followup["investigation"]["trace"]) > len(current["trace"])
    restored = InspectionAgent(workspace / "investigations").load(current["id"])
    assert restored.identifier == "product-001"


def test_complementary_frame_consumed_only_after_grounded_request(tmp_path, monkeypatch):
    reference, catalog = setup_catalog(tmp_path)
    native = [cv2.flip(reference, 1), reference.copy(), cv2.rotate(reference, cv2.ROTATE_180)]
    selected = []
    for index, image in enumerate(native):
        path = tmp_path / f"keyframe-{index}.png"
        cv2.imwrite(str(path), image)
        selected.append({"index": index, "path": str(path)})
    report = VideoReport("KEYFRAMES_SELECTED", cv2.__version__, "Controlled synthetic selections", selected=selected)
    monkeypatch.setattr("prooflens.investigation.inspect_video", lambda *args: report)
    result = investigate_video(tmp_path / "controlled.mp4", catalog, tmp_path / "workspace", "product-001")
    followups = [step for step in result["integration_trace"] if step["tool"] == "provide_complementary_keyframe"]
    assert len(followups) == 1
    assert followups[0]["frame_index"] == 1 and followups[0]["grounded_request"]
    assert result["investigation"]["verdict"] == "consistent_with_reference"
    assert result["evidence_coverage"]["inspected_selected_indices"] == [0, 1, 2]


def test_later_selected_difference_prevents_early_consistent_video_result(tmp_path, monkeypatch):
    reference, catalog = setup_catalog(tmp_path)
    changed = reference.copy()
    changed[280:350, 300:390] = 35
    selected = []
    for index, image in enumerate([reference, changed, reference.copy()]):
        path = tmp_path / f"selected-{index}.png"
        cv2.imwrite(str(path), image)
        selected.append({"index": index, "path": str(path)})
    report = VideoReport("KEYFRAMES_SELECTED", cv2.__version__, "Controlled selections", selected=selected)
    monkeypatch.setattr("prooflens.investigation.inspect_video", lambda *args: report)
    result = investigate_video(tmp_path / "controlled.mp4", catalog, tmp_path / "workspace", "product-001")
    assert result["investigation"]["human_review_required"]
    assert result["investigation"]["verdict"] == "suspected_mismatch"
    assert result["evidence_coverage"]["inspected_selected_indices"] == [0, 1]
    assert result["evidence_coverage"]["uninspected_selected_indices"] == [2]


def test_qr_resolves_from_later_keyframe_and_conflicting_codes_require_manual(tmp_path):
    reference, path = setup_catalog(tmp_path)
    catalog = ReferenceCatalog(path)

    def qr(identifier):
        pixels = cv2.QRCodeEncoder_create().encode(identifier)
        pixels = cv2.copyMakeBorder(pixels, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=255)
        pixels = cv2.resize(pixels, None, fx=8, fy=8, interpolation=cv2.INTER_NEAREST)
        return cv2.cvtColor(pixels, cv2.COLOR_GRAY2BGR)

    images = [({"index": 0}, reference), ({"index": 1}, qr("product-001"))]
    resolved, attempts = resolve_keyframes(images, catalog, None)
    assert resolved.status == "RESOLVED" and len(attempts) == 2
    assert attempts[0]["result"]["status"] == "MISSING_CODE"
    conflict, attempts = resolve_keyframes(images + [({"index": 2}, qr("unknown"))], catalog, None)
    assert conflict.status == "CONFLICTING_IDENTIFIERS" and conflict.record is None
    manual, _ = resolve_keyframes(images, catalog, "product-001")
    assert manual.status == "RESOLVED" and manual.source == "manual"
