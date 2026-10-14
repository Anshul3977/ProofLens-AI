import json
import platform
import sys
import cv2
import numpy as np

report = {
    "python": sys.version,
    "platform": platform.platform(),
    "opencv": cv2.__version__,
    "numpy": np.__version__,
    "capabilities": {name: hasattr(cv2, name) for name in [
        "ORB_create", "QRCodeDetector", "findHomography", "warpPerspective",
        "RANSAC", "USAC_MAGSAC", "ALIKED", "LightGlue"]},
}
print(json.dumps(report, indent=2))
assert cv2.__version__.split(".")[0] == "5", "OpenCV 5 required"
assert all(report["capabilities"][key] for key in ["ORB_create", "QRCodeDetector", "findHomography", "warpPerspective"])
cv2.ORB_create()
cv2.QRCodeDetector()
