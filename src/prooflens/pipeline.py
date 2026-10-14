from dataclasses import asdict
import json
from pathlib import Path

import cv2
import numpy as np

from prooflens.config import Settings
from prooflens.schemas import InspectionResult
from prooflens.vision.alignment import align_images
from prooflens.vision.differences import inspect_differences
from prooflens.vision.quality import Image, inspect_image_quality


def require_opencv5() -> None:
    if cv2.__version__.split(".")[0] != "5":
        raise RuntimeError(f"OpenCV 5 required; found {cv2.__version__}.")


def read_image(path: Path) -> Image | None:
    try:
        data = np.frombuffer(path.read_bytes(), dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None
    except (OSError, cv2.error):
        return None


def inspect_pair(reference: Image | None, inspection: Image | None,
                 output: Path, settings: Settings = Settings()) -> InspectionResult:
    require_opencv5()
    output.mkdir(parents=True, exist_ok=True)
    qr = inspect_image_quality(reference, settings)
    qi = inspect_image_quality(inspection, settings)
    result = InspectionResult("INVALID_INPUT", cv2.__version__, qr, qi)
    if qr.valid and qi.valid:
        if qr.recommended_actions or qi.recommended_actions:
            result.status = "QUALITY_INSUFFICIENT"
        else:
            result.alignment, aligned, valid = align_images(reference, inspection, settings)
            result.status = "ALIGNMENT_FAILED"
            if result.alignment.success:
                result.differences, overlay, evidence = inspect_differences(reference, aligned, valid, settings)
                result.status = "DIFFERENCES_AVAILABLE"
                for name, image in {"aligned": aligned, "overlay": overlay, "evidence_mask": evidence,
                                    "valid_mask": valid}.items():
                    path = output / f"{name}.png"
                    ok, encoded = cv2.imencode(".png", image)
                    if not ok:
                        raise OSError(f"Could not encode {name}")
                    path.write_bytes(encoded.tobytes())
                    result.artifacts[name] = str(path.resolve())
    result.artifacts["result"] = str((output / "result.json").resolve())
    (output / "result.json").write_text(json.dumps(asdict(result), indent=2, allow_nan=False), encoding="utf-8")
    return result
