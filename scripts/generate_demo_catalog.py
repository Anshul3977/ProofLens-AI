"""Trusted reference fixtures for the existing self-created synthetic video demo."""
import json
from pathlib import Path

import cv2
import numpy as np
from prooflens.pipeline import require_opencv5
from prooflens.synthetic import reference_image

require_opencv5()
root = Path("sample_data/generated/demo-catalog")
root.mkdir(parents=True, exist_ok=True)
path = root / "catalog.json"
if path.exists():
    raise SystemExit("Demo catalog already exists; use it as-is rather than overwrite it")
source = np.tile(reference_image(), (3, 3, 1))[:1080, :1920].copy()
assert cv2.imwrite(str(root / "reference.png"), source)
identifier = "synthetic-geometric-video"
qr = cv2.QRCodeEncoder_create().encode(identifier)
qr = cv2.copyMakeBorder(qr, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=255)
qr = cv2.resize(qr, None, fx=8, fy=8, interpolation=cv2.INTER_NEAREST)
assert cv2.imwrite(str(root / "identifier-qr.png"), qr)
path.write_text(json.dumps({"synthetic": True, "references": [
    {"identifier": identifier, "image": "reference.png", "description": "Self-created seed-2026 geometric video identity view"}
]}, indent=2), encoding="utf-8")
print(f"Wrote {path}; reference pixels correspond to the generated demo's identity appearance")
