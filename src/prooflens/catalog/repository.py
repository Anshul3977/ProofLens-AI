from dataclasses import dataclass
import json
from pathlib import Path

from prooflens.pipeline import read_image
from prooflens.vision.quality import Image


@dataclass(frozen=True)
class ReferenceRecord:
    identifier: str
    image_path: Path
    description: str = ""


class ReferenceCatalog:
    """Explicitly configured trusted local JSON, with images confined to its directory."""

    def __init__(self, path: Path):
        self.path = path.resolve(strict=True)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("references"), list):
            raise ValueError("Catalog must contain a references list")
        self.records: dict[str, ReferenceRecord] = {}
        for item in data["references"]:
            if not isinstance(item, dict):
                raise ValueError("Catalog record must be an object")
            identifier = item.get("identifier")
            image = item.get("image")
            if not isinstance(identifier, str) or not 0 < len(identifier) <= 256:
                raise ValueError("Catalog identifier must be a nonempty string up to 256 characters")
            if identifier in self.records:
                raise ValueError("Duplicate catalog identifier")
            if not isinstance(image, str) or not image:
                raise ValueError("Catalog image must be a local relative path")
            relative = Path(image)
            if relative.is_absolute():
                raise ValueError("Catalog image must be relative to its catalog")
            resolved = (self.path.parent / relative).resolve()
            if not resolved.is_relative_to(self.path.parent):
                raise ValueError("Catalog image escapes the trusted catalog directory")
            description = item.get("description", "")
            if not isinstance(description, str):
                raise ValueError("Catalog description must be a string")
            self.records[identifier] = ReferenceRecord(identifier, resolved, description)

    def get(self, identifier: str) -> ReferenceRecord | None:
        return self.records.get(identifier)

    def read(self, record: ReferenceRecord) -> Image | None:
        if self.records.get(record.identifier) != record:
            raise ValueError("Record is not part of this trusted catalog")
        return read_image(record.image_path)
