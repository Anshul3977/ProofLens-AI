from pathlib import Path
import cv2
from prooflens.synthetic import reference_image, perspective_image

output = Path("sample_data/generated")
output.mkdir(parents=True, exist_ok=True)
reference = reference_image()
modified = reference.copy()
cv2.rectangle(modified, (390, 280), (465, 340), (30, 30, 30), -1)
cases = {"reference": reference, "matching": reference.copy(), "perspective": perspective_image(reference),
         "modified": modified, "blurry": cv2.GaussianBlur(reference, (31, 31), 10)}
for name, image in cases.items():
    assert cv2.imwrite(str(output / f"{name}.png"), image)
print(f"Wrote {len(cases)} self-created synthetic images to {output}")
