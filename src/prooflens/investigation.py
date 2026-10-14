"""Local video/catalog/agent integration; all source lineage remains in the report."""
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from prooflens.agent.controller import InspectionAgent
from prooflens.catalog.repository import ReferenceCatalog
from prooflens.pipeline import read_image
from prooflens.video import VideoSettings, inspect_video
from prooflens.vision.qr import ReferenceResolution, identify_reference


def resolve_keyframes(images: list[tuple[dict, object]], catalog: ReferenceCatalog,
                      manual_identifier: str | None) -> tuple[ReferenceResolution, list[dict]]:
    attempts = []
    candidates = images if images and manual_identifier is None else [(images[0][0] if images else {},
                                                                      images[0][1] if images else None)]
    resolutions = []
    for frame, image in candidates:
        resolution = identify_reference(image, catalog, manual_identifier)
        resolutions.append(resolution)
        attempts.append({"frame_index": frame.get("index"), "result": resolution.summary()})
    decoded = {result.identifier for result in resolutions if result.identifier is not None}
    if len(decoded) > 1 or any(result.status == "CONFLICTING_IDENTIFIERS" for result in resolutions):
        return ReferenceResolution("CONFLICTING_IDENTIFIERS", None, "qr",
                                   ["Selected keyframes decoded different product identifiers."],
                                   "Resolve the product manually; conflicting QR evidence requires review."), attempts
    return next((result for result in resolutions if result.status == "RESOLVED"),
                next((result for result in resolutions if result.identifier is not None), resolutions[0])), attempts


def investigate_video(video_path: Path, catalog_path: Path, workspace: Path,
                      manual_identifier: str | None = None,
                      video_settings: VideoSettings = VideoSettings()) -> dict:
    start = perf_counter()
    run_id = uuid4().hex
    video_report = inspect_video(video_path, workspace / "videos" / run_id, video_settings)
    images = [(frame, read_image(Path(frame["path"]))) for frame in video_report.selected]
    first_image = images[0][1] if images else None
    catalog = ReferenceCatalog(catalog_path)
    resolution, attempts = resolve_keyframes(images, catalog, manual_identifier)
    reference = catalog.read(resolution.record) if resolution.status == "RESOLVED" else None
    agent = InspectionAgent(workspace / "investigations")
    investigation = agent.start(reference, first_image, identifier=resolution.identifier)
    lineage = [{"tool": "video_keyframe_selection", "observations": asdict(video_report)},
               {"tool": "identify_reference", "observations": resolution.summary(), "attempts": attempts}]
    if images:
        lineage.append({"tool": "agent_start", "investigation_id": investigation.id,
                        "source_video": str(video_path.resolve()), "frame_index": images[0][0]["index"],
                        "source_image": images[0][0]["path"]})
    # Inspect complementary selected evidence after a consistent view, or answer a grounded request.
    for frame, image in images[1:]:
        if str(investigation.state) == "complete":
            investigation = agent.inspect_additional(investigation.id, image)
            lineage.append({"tool": "inspect_complementary_keyframe",
                            "reason": "Prior view was consistent; additional selected evidence remains.",
                            "investigation_id": investigation.id, "frame_index": frame["index"],
                            "source_image": frame["path"]})
            continue
        if str(investigation.state) != "awaiting_evidence":
            break
        request = investigation.request
        investigation = agent.resume(investigation.id, image)
        lineage.append({"tool": "provide_complementary_keyframe", "grounded_request": request,
                        "investigation_id": investigation.id, "frame_index": frame["index"],
                        "source_image": frame["path"]})
    report = {"schema_version": 1, "scope": "local_video_investigation", "run_id": run_id,
              "video": asdict(video_report), "reference_resolution": resolution.summary(),
              "reference_resolution_attempts": attempts,
              "investigation": asdict(investigation), "integration_trace": lineage,
              "processing_seconds": perf_counter() - start,
              "limitations": ["No authenticity finding or fraud accusation is made.",
                              "Native video decoding and this local workspace are not a public upload service.",
                              "Complementary frames come from the same clip, not new physical evidence."]}
    inspected = [entry["frame_index"] for entry in lineage if entry["tool"] in
                 {"agent_start", "provide_complementary_keyframe", "inspect_complementary_keyframe"}]
    report["evidence_coverage"] = {"inspected_selected_indices": inspected,
                                   "uninspected_selected_indices": [frame["index"] for frame, _ in images
                                                                    if frame["index"] not in inspected],
                                   "verdict_scope": "Inspected selected reference-visible evidence only; not the entire video."}
    output = workspace / "reports" / f"{run_id}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    report["report_path"] = str(output.resolve())
    output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return report


def resume_investigation(workspace: Path, investigation_id: str, image_path: Path,
                         catalog_path: Path | None = None, manual_identifier: str | None = None) -> dict:
    image = read_image(image_path)
    if image is None:
        raise ValueError("Follow-up image could not be decoded")
    agent = InspectionAgent(workspace / "investigations")
    current = agent.load(investigation_id)
    reference = None
    identifier = None
    resolution = None
    if catalog_path is not None:
        catalog = ReferenceCatalog(catalog_path)
        resolution = identify_reference(image, catalog, manual_identifier)
        if resolution.status != "RESOLVED":
            raise ValueError(f"Reference still unresolved: {resolution.status}")
        identifier = resolution.identifier
        if str(current.state) != "manual_resolution" and current.identifier != identifier:
            raise ValueError("Cannot change product identity on a recapture; start a new investigation")
        reference = catalog.read(resolution.record)
    elif manual_identifier is not None:
        raise ValueError("Manual reference selection requires a catalog path")
    updated = agent.resume(investigation_id, image, reference=reference, identifier=identifier)
    return {"investigation": asdict(updated), "follow_up_image": str(image_path.resolve()),
            "reference_resolution": resolution.summary() if resolution else None}
