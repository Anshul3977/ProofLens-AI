import json

import cv2
import numpy as np
import pytest

from prooflens.catalog.repository import ReferenceCatalog
from prooflens.synthetic import reference_image
from prooflens.vision.qr import identify_reference


def catalog_at(directory):
    cv2.imwrite(str(directory / "reference.png"), reference_image())
    path = directory / "catalog.json"
    path.write_text(json.dumps({"references": [{"identifier": "product-001", "image": "reference.png"}]}))
    return ReferenceCatalog(path)


def qr_image(identifier):
    qr = cv2.QRCodeEncoder_create().encode(identifier)
    qr = cv2.copyMakeBorder(qr, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=255)
    qr = cv2.resize(qr, None, fx=8, fy=8, interpolation=cv2.INTER_NEAREST)
    return cv2.cvtColor(qr, cv2.COLOR_GRAY2BGR)


def test_actual_qr_catalog_resolution(tmp_path):
    catalog = catalog_at(tmp_path)
    resolved = identify_reference(qr_image("product-001"), catalog)
    assert resolved.status == "RESOLVED" and resolved.source == "qr"
    assert resolved.record.identifier == "product-001"
    assert identify_reference(qr_image("unknown"), catalog).status == "UNKNOWN_IDENTIFIER"


def test_missing_and_manual_resolution(tmp_path):
    catalog = catalog_at(tmp_path)
    assert identify_reference(np.full((200, 200, 3), 130, np.uint8), catalog).status == "MISSING_CODE"
    assert identify_reference(None, catalog).status == "INVALID_IMAGE"
    result = identify_reference(None, catalog, "product-001")
    assert result.status == "RESOLVED" and result.source == "manual"
    assert identify_reference(None, catalog, "unknown").recommended_action


@pytest.mark.parametrize("image", ["../outside.png", "C:/outside.png"])
def test_catalog_rejects_escaping_paths(tmp_path, image):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"references": [{"identifier": "id", "image": image}]}))
    with pytest.raises(ValueError):
        ReferenceCatalog(path)


def test_invalid_reference_and_duplicate_catalog(tmp_path):
    catalog = catalog_at(tmp_path)
    (tmp_path / "reference.png").write_text("not image")
    assert identify_reference(None, catalog, "product-001").status == "INVALID_REFERENCE"
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps({"references": [{"identifier": "id", "image": "ref.png"}] * 2}))
    with pytest.raises(ValueError, match="Duplicate"):
        ReferenceCatalog(path)


def test_multiple_qr_identifiers_in_one_frame_require_manual_resolution(tmp_path):
    catalog = catalog_at(tmp_path)
    first, second = qr_image("product-001"), qr_image("unknown")
    canvas = np.full((max(first.shape[0], second.shape[0]) + 40,
                      first.shape[1] + second.shape[1] + 60, 3), 255, np.uint8)
    canvas[20:20 + first.shape[0], 20:20 + first.shape[1]] = first
    canvas[20:20 + second.shape[0], 40 + first.shape[1]:40 + first.shape[1] + second.shape[1]] = second
    resolution = identify_reference(canvas, catalog)
    assert resolution.status == "CONFLICTING_IDENTIFIERS"
    assert resolution.record is None and resolution.recommended_action
    from prooflens.investigation import resolve_keyframes
    aggregate, attempts = resolve_keyframes([({"index": 0}, canvas), ({"index": 1}, first)], catalog, None)
    assert attempts[1]["result"]["status"] == "RESOLVED"
    assert aggregate.status == "CONFLICTING_IDENTIFIERS" and aggregate.record is None
