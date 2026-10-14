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
This standalone video CLI selects evidence only. The integrated investigation CLI below performs
QR/catalog lookup and bounded reference inspection. UI/API and AWS remain unimplemented.

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

## Integrated local video investigation

Generate the video above once, then its matching trusted synthetic catalog:

```powershell
.\.venv\Scripts\python.exe scripts/generate_demo_catalog.py
.\.venv\Scripts\python.exe -m prooflens.investigation_cli start sample_data/generated/video-inspection.mp4 --catalog sample_data/generated/demo-catalog/catalog.json --identifier synthetic-geometric-video
```

Omit `--identifier` for automatic OpenCV QR lookup across selected frames. Unknown/conflicting codes
require manual resolution. Local catalog format: `{"references":[{"identifier":"product-001","image":"reference.png"}]}`;
image paths must remain within the catalog directory. Reading QR does not verify authenticity.
The demo catalog generator refuses to overwrite its existing catalog; reuse it on later runs.

The integrated CLI persists investigation UUID, state, original evidence, overlays, crop inspections
and trace under `artifacts/investigations/`. It consumes complementary selected views in response to
an evidence request and after a consistent per-view result. Suspicious findings require human review.
Reports explicitly identify inspected/uninspected selected frames and limit verdicts to inspected evidence.
This is a heuristic state machine with lifetime tool-step/recapture limits, not an LLM or unattended coding runner.

Resume a waiting/manual-resolution investigation using its printed ID:

```powershell
.\.venv\Scripts\python.exe -m prooflens.investigation_cli resume INVESTIGATION_UUID "C:\path\followup.jpg"
```

For manual resolution also pass `--catalog path/to/catalog.json --identifier product-001`.
For a custom start workspace, use the same `--workspace` on resume. Recapture cannot replace an established
product/reference. Human-review findings stay terminal. Operations assume one writer per investigation.

## Development evaluation

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_suite.py
.\.venv\Scripts\python.exe scripts/suite_gate.py
.\.venv\Scripts\python.exe scripts/benchmark_agent.py
.\.venv\Scripts\python.exe scripts/agent_gate.py
.\.venv\Scripts\python.exe scripts/benchmark_keyframes.py sample_data/generated/video-inspection.mp4 sample_data/generated/video-inspection.metadata.json
```

100 seeded synthetic cases are defined, split by original source: 80 development, 20 holdout reserved
for final evaluation. The default gates evaluate development only; real-world results remain unavailable.
[Integration report](docs/local-integration-report.md) records measured outcomes, failures and limitations.
Nothing has been pushed, merged into main, deployed or connected to paid services.
