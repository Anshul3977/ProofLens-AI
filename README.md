# ProofLens AI

Video-first warehouse return inspection project. The current local CPU slice validates MP4s,
samples frames, scores quality, and saves up to three complementary native-resolution keyframes.
The existing image CLI checks quality, estimates ORB/RANSAC alignment, and saves candidate changes.
It does not determine authenticity, prove fraud, or measure physical damage dimensions.

## Run the video inspection slice

```powershell
.\.venv\Scripts\python.exe scripts/generate_video_sample.py
.\.venv\Scripts\python.exe -m prooflens.video_cli sample_data/generated/video-inspection.mp4 --samples 24
```

Or provide your own local MP4:

```powershell
.\.venv\Scripts\python.exe -m prooflens.video_cli "C:\path\inspection.mp4" --samples 24 --output artifacts/my-video
```

Writes native-resolution `keyframe_*.png` and `report.json` into a fresh output directory.
JSON includes source metadata, sample indices/estimated timestamps, quality metrics/scores,
selection reasons, configuration, limitations and processing time. Exit 0 means three keyframes
selected; exit 2 means invalid input or insufficient acceptable/distinct frames.
Static or poor-quality footage may produce fewer than three; the report requests additional viewpoints.
No QR/catalog lookup, agent investigation, reference alignment of video frames, UI or AWS is invoked.

The target is 5–10 seconds at 1080p. Shorter clips are allowed for testing but flagged outside target.
Default bounds: 100 MiB file, 15 seconds, 900 frames, 3840x2160 pixels, 256 MiB retained samples.
Default sampling is 24 evenly spaced frames; at most 60 may be configured and the memory budget applies.
These are local application bounds; the native decoder is not an isolated upload service.
`--config video-settings.json` accepts VideoSettings overrides, e.g.
`{"sample_count": 12, "diversity_weight": 0.6}`; explicit `--samples` takes precedence.
Only the 160x90 diversity descriptor is resized; PNGs retain decoded frame pixels and dimensions.

[Video milestone verification](docs/video-slice-report.md) records actual tests, failure repairs,
1080p artifact inspection and measured timing. Generated video fixtures are synthetic only.

## Verified environment

Windows 10 x64, Python 3.13.2, `cv2.__version__ == 5.0.0`, NumPy 2.5.4.
The installed wheel is `opencv-python-headless==5.0.0.93` (Windows `cp37-abi3-win_amd64`).
The CLI refuses OpenCV 4. Python 3.11 is not installed here; it has not been tested.
The initial runtime dependencies are OpenCV and NumPy; pytest is for development.
FastAPI, Pydantic, and Streamlit are deferred to Phase 3.

## Install (PowerShell, from this directory)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe scripts/audit_environment.py
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

No activation or PowerShell execution-policy change is needed. Select `.venv/Scripts/python.exe` in VS Code.
Keep only one OpenCV wheel variant in this environment. For package installation guidance see
[OpenCV's pip documentation](https://docs.opencv.org/5.0/py_tutorials/py_setup/py_pip_install/py_pip_install.html).

## Run the first prototype

```powershell
.\.venv\Scripts\python.exe scripts/generate_samples.py
.\.venv\Scripts\python.exe -m prooflens.cli sample_data/generated/reference.png sample_data/generated/modified.png
```

The CLI prints JSON and writes `result.json`, `aligned.png`, `overlay.png`, `evidence_mask.png`, and
`valid_mask.png` into a new `artifacts/<unique-id>/` directory. On quality or alignment failure it saves
structured JSON with observations rather than producing an unsupported comparison.
For your own images:

```powershell
.\.venv\Scripts\python.exe -m prooflens.cli "C:\path\reference.jpg" "C:\path\inspection.jpg" --output artifacts/my-inspection
```

Explicit output directories must be empty. Exit code 0 means differences are available; 2 means input,
quality, or alignment prevented analysis (or the command arguments were invalid). Candidate differences
are observations, not final product verdicts. Coordinates are pixels in the reference frame.

Thresholds are configurable with `--config path/to/settings.json`, for example
`{"blur_variance": 50.0, "difference_threshold": 35}`. Field names are in `src/prooflens/config.py`.
Defaults were checked against these synthetic fixtures and need real-photo calibration.

## Scope and evidence

- [Audit and executed checks](docs/phase1-report.md)
- [Architecture](docs/architecture.md)
- [Limitations](docs/limitations.md)

All generated examples are deterministic self-created geometric scenes, clearly synthetic.
They are reproducible with the sample script; they do not represent an e-commerce benchmark.
Git is initialized; no commit or remote has been created.

The [official rules](https://opencv26.devpost.com/rules) list the deadline as October 26, 2026,
11:45 p.m. PDT (October 27, 12:15 p.m. IST). Recheck before submission.
Competition compliance is not claimed: the agent loop, AWS deployment, interface, evaluation,
technical report, and video remain future milestones.

The updated phase order is in [PLAN.md](PLAN.md): Phase 2 full evaluation, Phase 3 agent,
Phase 4 UI/API, Phase 5 AWS/submission. Next milestone requires user approval.

Repository workflow rules and acceptance criteria: [AGENTS.md](AGENTS.md),
[PRODUCT_SPEC.md](PRODUCT_SPEC.md), [EVAL_SPEC.md](EVAL_SPEC.md), [PROGRESS.md](PROGRESS.md).
Run the current synthetic smoke evaluation and local regression gate:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate.py
.\.venv\Scripts\python.exe scripts/quality_gate.py
```

The gate runs pytest and compares fresh synthetic outcomes against `eval_data/phase1-baseline.json`.
It does not evaluate an agent or real-world accuracy. CI is defined in `.github/workflows/ci.yml`;
no remote CI execution has been verified.
