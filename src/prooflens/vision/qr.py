from dataclasses import dataclass
from typing import Literal

import cv2

from prooflens.catalog.repository import ReferenceCatalog, ReferenceRecord
from prooflens.pipeline import require_opencv5
from prooflens.vision.quality import Image, inspect_image_quality


@dataclass
class ReferenceResolution:
    status: Literal["RESOLVED", "MISSING_CODE", "UNREADABLE_CODE", "UNKNOWN_IDENTIFIER", "INVALID_IMAGE", "INVALID_REFERENCE", "CONFLICTING_IDENTIFIERS"]
    identifier: str | None
    source: Literal["qr", "manual"]
    observations: list[str]
    recommended_action: str | None
    record: ReferenceRecord | None = None

    def summary(self) -> dict:
        return {"status": self.status, "identifier": self.identifier, "source": self.source,
                "observations": self.observations, "recommended_action": self.recommended_action,
                "reference_path": str(self.record.image_path) if self.record else None,
                "limitations": ["QR/catalog association is not authenticity or cryptographic verification."]}


def identify_reference(image: Image | None, catalog: ReferenceCatalog,
                       manual_identifier: str | None = None) -> ReferenceResolution:
    require_opencv5()
    if manual_identifier is not None:
        identifier, source = manual_identifier, "manual"
    else:
        source = "qr"
        if not inspect_image_quality(image).valid:
            return ReferenceResolution("INVALID_IMAGE", None, source, ["No valid image for QR detection."],
                                       "Provide a readable identifier photo or manually select the catalog entry.")
        try:
            detector = cv2.QRCodeDetector()
            _, decoded, points, _ = detector.detectAndDecodeMulti(image)
            identifiers = sorted({value for value in decoded if value})
            if len(identifiers) > 1:
                return ReferenceResolution("CONFLICTING_IDENTIFIERS", None, source,
                                           ["Multiple distinct QR identifiers decoded in one frame: " + repr(identifiers)],
                                           "Resolve the product manually; conflicting QR evidence requires review.")
            if identifiers and any(not value for value in decoded):
                return ReferenceResolution("UNREADABLE_CODE", None, source,
                                           ["Some detected QR identifiers were not decoded."],
                                           "Photograph all identifiers clearly or select the reference manually.")
            if identifiers:
                identifier = identifiers[0]
            else:
                identifier, points, _ = detector.detectAndDecode(image)
        except cv2.error:
            return ReferenceResolution("UNREADABLE_CODE", None, source, ["OpenCV QR decoding failed."],
                                       "Photograph the QR more clearly or select the reference manually.")
        if not identifier:
            status = "UNREADABLE_CODE" if points is not None else "MISSING_CODE"
            return ReferenceResolution(status, None, source, ["No decoded QR identifier."],
                                       "Provide a clearer QR photo or select the reference manually.")
    record = catalog.get(identifier)
    if record is None:
        return ReferenceResolution("UNKNOWN_IDENTIFIER", identifier, source,
                                   ["Identifier does not occur in the trusted catalog."],
                                   "Resolve the product manually against the trusted catalog.")
    if catalog.read(record) is None:
        return ReferenceResolution("INVALID_REFERENCE", identifier, source,
                                   ["Catalog reference image could not be decoded."],
                                   "Repair the trusted reference record before investigation.", record)
    return ReferenceResolution("RESOLVED", identifier, source,
                               ["Identifier matched a trusted local catalog record."], None, record)
