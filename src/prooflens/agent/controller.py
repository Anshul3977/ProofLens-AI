"""Evidence-driven, single-writer inspection state machine using independent vision tools."""
from dataclasses import asdict, dataclass, field
from enum import StrEnum
import json
import os
from pathlib import Path
from uuid import UUID, uuid4

import cv2
import numpy as np

from prooflens.config import Settings
from prooflens.pipeline import read_image, require_opencv5
from prooflens.vision.alignment import align_images
from prooflens.vision.differences import inspect_differences
from prooflens.vision.quality import Image, inspect_image_quality


class State(StrEnum):
    INSPECTING = "inspecting"
    MANUAL_RESOLUTION = "manual_resolution"
    AWAITING_EVIDENCE = "awaiting_evidence"
    COMPLETE = "complete"
    HUMAN_REVIEW = "human_review"


class Verdict(StrEnum):
    CONSISTENT = "consistent_with_reference"
    SUSPECTED_MISMATCH = "suspected_mismatch"
    INSUFFICIENT = "insufficient_evidence"


@dataclass
class Investigation:
    id: str
    state: State = State.INSPECTING
    verdict: Verdict | None = None
    trace: list[dict] = field(default_factory=list)
    request: str | None = None
    human_review_required: bool = False
    identifier: str | None = None
    recaptures: int = 0
    artifacts: dict[str, str] = field(default_factory=dict)
    policy: dict = field(default_factory=dict)


class InspectionAgent:
    def __init__(self, workspace: Path, settings: Settings = Settings(),
                 max_steps: int = 40, max_recaptures: int = 2):
        require_opencv5()
        if max_steps < 1 or max_recaptures < 0:
            raise ValueError("max_steps must be positive and max_recaptures nonnegative")
        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.settings, self.max_steps, self.max_recaptures = settings, max_steps, max_recaptures

    def _directory(self, identifier: str) -> Path:
        try:
            if str(UUID(identifier)) != identifier:
                raise ValueError
        except (ValueError, TypeError, AttributeError):
            raise ValueError("Expected a canonical UUID investigation ID") from None
        directory = self.workspace / identifier
        if directory.is_symlink() or directory.resolve().parent != self.workspace:
            raise ValueError("Investigation directory escapes workspace")
        return directory

    @staticmethod
    def _atomic(path: Path, data: bytes) -> None:
        temporary = path.with_name(path.name + "." + str(uuid4()) + ".tmp")
        try:
            temporary.write_bytes(data)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def _save(self, investigation: Investigation) -> Investigation:
        directory = self._directory(investigation.id)
        directory.mkdir(exist_ok=True)
        self._atomic(directory / "state.json", json.dumps(asdict(investigation), indent=2,
                                                        allow_nan=False).encode("utf-8"))
        return investigation

    def _image(self, investigation: Investigation, name: str, image: Image) -> None:
        ok, encoded = cv2.imencode(".png", image)
        if not ok:
            raise OSError("PNG encoding failed")
        path = self._directory(investigation.id) / (name + ".png")
        self._atomic(path, encoded.tobytes())
        investigation.artifacts[name] = str(path)

    def load(self, investigation_id: str) -> Investigation:
        raw = json.loads((self._directory(investigation_id) / "state.json").read_text("utf-8"))
        if raw["id"] != investigation_id:
            raise ValueError("Persisted investigation ID mismatch")
        raw["state"] = State(raw["state"])
        raw["verdict"] = Verdict(raw["verdict"]) if raw["verdict"] else None
        return Investigation(**raw)

    def start(self, reference: Image | None, inspection: Image | None,
              identifier: str | None = None) -> Investigation:
        investigation = Investigation(str(uuid4()), identifier=identifier,
                                      policy={"settings": asdict(self.settings),
                                              "max_steps": self.max_steps,
                                              "max_recaptures": self.max_recaptures})
        self._save(investigation)
        return self._run(investigation, reference, inspection)

    def resume(self, investigation_id: str, inspection: Image,
               reference: Image | None = None, identifier: str | None = None) -> Investigation:
        investigation = self.load(investigation_id)
        if investigation.state not in (State.AWAITING_EVIDENCE, State.MANUAL_RESOLUTION):
            raise ValueError("Only investigations requesting evidence or catalog resolution can resume")
        if investigation.state == State.AWAITING_EVIDENCE:
            if identifier is not None and identifier != investigation.identifier:
                raise ValueError("Cannot change product identity during recapture")
            stored = read_image(self._directory(investigation.id) / "reference.png")
            if stored is None:
                raise ValueError("Persisted trusted reference is unavailable")
            if reference is not None and not np.array_equal(reference, stored):
                raise ValueError("Cannot replace trusted reference during recapture")
            reference = stored
            if investigation.recaptures >= investigation.policy["max_recaptures"]:
                return self._save(self._review(investigation, "Recapture limit reached."))
            investigation.recaptures += 1
        if reference is None and "reference" in investigation.artifacts:
            reference = read_image(self._directory(investigation.id) / "reference.png")
        if identifier is not None:
            investigation.identifier = identifier
        investigation.state, investigation.verdict = State.INSPECTING, None
        investigation.request, investigation.human_review_required = None, False
        return self._run(investigation, reference, inspection)

    def inspect_additional(self, investigation_id: str, inspection: Image) -> Investigation:
        """Inspect another selected view only after a consistent per-view result.

        Keeps lifetime budget/trace/reference/identity; human-review decisions stay terminal.
        This is new selected evidence, not a recapture retry or a verdict override.
        """
        investigation = self.load(investigation_id)
        if investigation.state != State.COMPLETE or investigation.verdict != Verdict.CONSISTENT:
            raise ValueError("Additional selected views require a consistent completed view")
        reference = read_image(self._directory(investigation.id) / "reference.png")
        if reference is None:
            raise ValueError("Persisted trusted reference is unavailable")
        investigation.state, investigation.verdict = State.INSPECTING, None
        investigation.request, investigation.human_review_required = None, False
        return self._run(investigation, reference, inspection)

    def _review(self, investigation: Investigation, reason: str,
                verdict: Verdict = Verdict.INSUFFICIENT) -> Investigation:
        investigation.state, investigation.verdict = State.HUMAN_REVIEW, verdict
        investigation.human_review_required, investigation.request = True, reason
        return investigation

    def _request(self, investigation: Investigation, reason: str) -> None:
        if investigation.recaptures >= investigation.policy["max_recaptures"]:
            self._review(investigation, "Recapture limit reached. " + reason)
        else:
            investigation.state, investigation.verdict = State.AWAITING_EVIDENCE, Verdict.INSUFFICIENT
            investigation.request = reason

    def _record(self, investigation: Investigation, tool: str, reason: str, observations: dict) -> None:
        investigation.trace.append({"step": len(investigation.trace) + 1,
                                    "state": str(investigation.state), "tool": tool,
                                    "reason": reason, "observations": observations})
        self._save(investigation)

    def _budget(self, investigation: Investigation) -> bool:
        if len(investigation.trace) >= investigation.policy["max_steps"]:
            self._review(investigation, "Tool-call limit reached; remaining evidence uninspected.")
            return False
        return True

    def _run(self, investigation: Investigation, reference: Image | None,
             inspection: Image | None) -> Investigation:
        settings = Settings(**investigation.policy["settings"])
        active_tool = "quality"
        try:
            if reference is None:
                if not self._budget(investigation):
                    return self._save(investigation)
                quality = inspect_image_quality(inspection, settings)
                if quality.valid:
                    self._image(investigation, f"unresolved_{len(investigation.trace)}", inspection)
                self._record(investigation, "reference_resolution", "A trusted reference is required.",
                             {"identifier": investigation.identifier, "reference_available": False,
                              "inspection_quality": asdict(quality)})
                investigation.state = State.MANUAL_RESOLUTION
                investigation.verdict = Verdict.INSUFFICIENT
                investigation.request = "Unknown or unresolved identifier: select a trusted catalog reference manually."
                return self._save(investigation)
            if not self._budget(investigation):
                return self._save(investigation)
            rq = inspect_image_quality(reference, settings)
            iq = inspect_image_quality(inspection, settings)
            self._record(investigation, "quality", "Check evidence before attempting geometry.",
                         {"reference": asdict(rq), "inspection": asdict(iq)})
            if rq.valid:
                self._image(investigation, "reference", reference)
            version = f"inspection_{investigation.recaptures}_{len(investigation.trace)}"
            if iq.valid:
                self._image(investigation, version, inspection)
            if not rq.valid or rq.recommended_actions:
                return self._save(self._review(investigation, "Trusted reference quality is insufficient; review catalog evidence."))
            if not iq.valid or iq.recommended_actions:
                if inspection is None:
                    return self._save(self._review(investigation, "No inspection evidence supplied; human review required."))
                self._request(investigation, "Request retake: " + " ".join(iq.recommended_actions))
                return self._save(investigation)
            if not self._budget(investigation):
                return self._save(investigation)
            active_tool = "alignment"
            alignment, aligned, valid = align_images(reference, inspection, settings)
            self._record(investigation, "alignment", "Usable quality permits ORB/RANSAC geometry checks.", asdict(alignment))
            if not alignment.success:
                self._request(investigation, "Request an alternative viewpoint with matching visible detail: " + alignment.reason)
                return self._save(investigation)
            self._image(investigation, version + "_aligned", aligned)
            if not self._budget(investigation):
                return self._save(investigation)
            active_tool = "differences"
            differences, overlay, mask = inspect_differences(reference, aligned, valid, settings)
            self._image(investigation, version + "_overlay", overlay)
            self._image(investigation, version + "_mask", mask)
            self._record(investigation, "differences", "Reliable heuristic overlap permits candidate-region inspection.",
                         asdict(differences))
            if not differences.regions:
                investigation.state, investigation.verdict = State.COMPLETE, Verdict.CONSISTENT
                investigation.request = None
                return self._save(investigation)
            for index, (x, y, width, height) in enumerate(differences.regions[:3]):
                if not self._budget(investigation):
                    return self._save(investigation)
                # Preserve native pixels and compare the local crop with the independent tool.
                # Local offset can disagree with global evidence; do not erase that uncertainty.
                crop = aligned[y:y + height, x:x + width]
                active_tool = "targeted_inspection"
                local, local_overlay, _ = inspect_differences(
                    reference[y:y + height, x:x + width], crop,
                    valid[y:y + height, x:x + width], settings)
                self._image(investigation, version + f"_region_{index}", local_overlay)
                self._record(investigation, "targeted_inspection", "Suspicious global region requires actual native crop reinspection.",
                             {"region": [x, y, width, height], "local": asdict(local),
                              "artifact": investigation.artifacts[version + f"_region_{index}"]})
            return self._save(self._review(investigation,
                "Candidate differences require human review; lighting/registration remain possible causes. "
                f"Reinspected {min(3, len(differences.regions))} of {len(differences.regions)} regions.",
                Verdict.SUSPECTED_MISMATCH))
        except (cv2.error, ValueError) as error:
            # I/O failures propagate: callers must not mistake failed persistence for a saved report.
            self._review(investigation, f"Vision tool failed: {type(error).__name__}: {error}")
            if len(investigation.trace) < investigation.policy["max_steps"]:
                self._record(investigation, active_tool, "Attempted tool failed; no measurement produced.",
                             {"error_type": type(error).__name__, "error": str(error)})
            return self._save(investigation)
