# Phase 0 and Phase 1 verification

Audit date: October 14, 2026 (user timezone: Asia/Calcutta).

## Environment

Empty workspace at start; Git repository initialized locally without a remote or commit.
Windows 10 build 19045 x64. Default `python` is 3.9.13; `py -3.13` selects 3.13.2.
No cv2 module existed in that Python installation before setup.
Docker CLI was found but daemon/container functionality was not tested or needed.

`pip index versions opencv-python-headless` (also with `--pre`) listed 5.0.0.93.
Binary-only installation succeeded with the Windows `cp37-abi3-win_amd64` wheel.
Actual import reports cv2 **5.0.0**, NumPy **2.5.4**, Python **3.13.2**.
ORB and QRCodeDetector construction succeeded. `findHomography`, `warpPerspective`, RANSAC,
and USAC_MAGSAC symbols are available; actual ORB/RANSAC/warp processing is exercised in tests.
ALIKED symbol exists, LightGlue symbol does not; neither advanced integration was attempted.

Official sources checked:
- [Competition rules](https://opencv26.devpost.com/rules): deadline October 26, 2026 at 11:45 p.m. PDT;
  equivalent October 27 at 12:15 p.m. IST. Reverify before submission.
- [OpenCV 5 docs](https://docs.opencv.org/5.0/) and
  [pip installation](https://docs.opencv.org/5.0/py_tutorials/py_setup/py_pip_install/py_pip_install.html).
- [Documented source-build alternative](https://docs.opencv.org/5.0/tutorials/introduction/linux_install/linux_install.html)
  was identified but not needed; no source build/container is claimed to be verified.

## Implemented files

- Project setup: AGENTS.md, .gitignore, pyproject.toml, requirements-lock.txt, README.md.
- Typed settings/results: src/prooflens/config.py and schemas.py.
- Vision tools: quality.py, alignment.py, differences.py and package initializers.
- Local processing and CLI: pipeline.py, cli.py.
- Reproducible fixtures: synthetic.py and scripts/generate_samples.py.
- Audit: scripts/audit_environment.py.
- Tests: tests/test_vertical_slice.py.
- Documentation: architecture.md, limitations.md, this report.

## Commands actually executed

```powershell
python --version
py -0p
py -3.13 -m pip index versions opencv-python-headless
py -3.13 -m pip index versions opencv-python-headless --pre
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: opencv-python-headless==5.0.0.93 numpy pytest
.\.venv\Scripts\python.exe -m pip install setuptools==82.0.1
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe scripts/audit_environment.py
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip freeze
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/generate_samples.py
.\.venv\Scripts\python.exe -m prooflens.cli sample_data/generated/reference.png sample_data/generated/perspective.png --output artifacts/phase1-perspective
.\.venv\Scripts\python.exe -m prooflens.cli sample_data/generated/reference.png sample_data/generated/modified.png --output artifacts/phase1-modified
.\.venv\Scripts\python.exe -m prooflens.cli sample_data/generated/reference.png sample_data/generated/blurry.png --output artifacts/phase1-blurry
.\.venv\Scripts\python.exe -m prooflens.cli sample_data/generated/reference.png sample_data/generated/perspective.png --output artifacts/phase1-perspective-verified
```

Initial tests: 12 passed in 1.99 seconds. CLI then revealed that the default blur threshold of 80
rejected the resampled perspective fixture (variance 69.94). The sharp reference measured 185.47,
and the blurred fixture 1.09. Threshold adjusted to 50; an end-to-end perspective test was added.
Final executed tests: **13 passed in 0.94 seconds**. `pip check`: no broken requirements found.
These elapsed test times are test-run durations, not processing latency benchmarks.

| Synthetic CLI case | Observed result |
|---|---|
| Modified rectangle | DIFFERENCES_AVAILABLE; one region at (390,280), size 76x61 pixels; retained fraction 0.01531 |
| Blurry | QUALITY_INSUFFICIENT; focus retake recommendation; no alignment |
| Perspective, initial threshold | QUALITY_INSUFFICIENT (documented heuristic false rejection) |
| Perspective, corrected threshold | DIFFERENCES_AVAILABLE; 975/1020 inliers; 0.98547 overlap; no retained regions |

The first perspective output is retained locally as audit evidence; corrected output is in
`artifacts/phase1-perspective-verified`. Tests additionally exercise matching images,
failed alignment, invalid files, exposure extremes, lighting offset, masked borders, and empty overlap.
Artifacts and fixtures are ignored by Git and reproducible with the scripts.

## Remaining work and blockers

No blocker for running this local prototype. Threshold calibration and real-photograph validation remain.
No QR catalog tool, region reinspection, autonomous loop, resume support, interface, benchmark comparison,
AWS deployment, submission report, or video is implemented. No competition compliance is claimed.
Do not begin Phase 2 or AWS before user review. Next recommended milestone is the bounded typed
state machine with persisted observations, grounded recapture requests, limits, and resume tests.

Suggested Git commit: `feat: add verified OpenCV 5 local inspection vertical slice`
