# Video inspection vertical slice — October 14, 2026

## Scope and compatibility
Updated all five project instruction/specification/plan/evaluation/progress files BEFORE implementation
to reflect the user's video-first warehouse workflow. Retained substantive OpenCV 5, bounded agent
requirements, meaningful AWS requirements and reproducibility. Only the local video slice is implemented.
Branch: `feat/video-inspection-slice`. No commit, push, deployment, advanced matching or new dependencies.

Verified actual OpenCV **5.0.0**, Python **3.13.2**, FFmpeg enabled, VideoCapture/VideoWriter available.
Actual `mp4v` encode/decode exercised by integration tests and the 1080p demo. Local CPU execution.

## Implementation
- Typed `VideoSettings`, `FrameCandidate`, `VideoReport` in src/prooflens/video.py.
- Local MP4 size/signature/metadata validation, bounded duration/pixels/frames/sample memory,
  deterministic evenly spaced indices, sequential decode with explicit early/extra-frame failures.
- Original-resolution quality scoring uses the unchanged quality tool and eligibility recommendations.
- Quality score is sharpness/(sharpness+blur threshold), penalized by exposure/glare fractions.
- Quality-first then greedy quality/diversity utility; minimum RMS 160x90 thumbnail distance to
  all previously selected frames. This is appearance diversity, not physical viewpoint verification.
- Native-resolution PNGs with selected indices, estimated timestamps, metrics, reasons, limits,
  settings and timing in JSON. Invalid/insufficient input yields structured outcomes.
- `src/prooflens/video_cli.py`, reproducible `scripts/generate_video_sample.py`, `tests/test_video.py`.

## Actual tests and repairs
First focused run: **20 passed, 2 failed**. Mean thumbnail distance diluted sparse detail; measured
three pairwise distances 0.0215–0.0234. RMS at the same descriptor size measured 0.0503–0.0533.
Repair 1: changed distance to RMS; focused run **22 passed**. Threshold and test expectations unchanged.
Actual 1080p smoke then returned one keyframe: the 64x48 thumbnail lost detail (RMS 0.0312–0.0330).
Repair 2: preserve more detail with 160x90 descriptor (0.0447–0.0468 measured); added native-1080p
selection/pixel-identity regression and early-decode-release tests. Focused run **24 passed in 1.31 s**.
No third repair was needed; no labels, gates, old baseline or quality thresholds were weakened/changed.

Full `scripts/quality_gate.py`: **42 passed in 2.15 s**, old four-case image smoke baseline still passes.
`pip check`: no broken requirements. Negative corrupt-file test prints FFmpeg `moov atom not found`
diagnostic as expected; invalid result and report are verified by the test.
Tests cover sampling, scoring, quality rejection, diversity/determinism, static/all-bad/single-frame
cases, MP4 encode/decode, 1080p pixel-preserving PNGs, missing/empty/wrong-format/corrupt input,
resource limits, output reuse, invalid settings and early decode release.

Executed commands (PowerShell using .venv/Scripts/python.exe):
```text
python scripts/audit_environment.py
python -m pytest -q tests/test_video.py
python scripts/generate_video_sample.py
python -m prooflens.video_cli sample_data/generated/video-inspection.mp4 --output artifacts/video-slice/first-run
python artifacts/video-slice/measure.py
python scripts/quality_gate.py
python -m pip check
python -m prooflens.video_cli sample_data/generated/video-inspection.mp4 --samples 24 --output artifacts/video-slice/cli-verified
```
The first CLI run preserves the insufficient-result evidence. Five verified subsequent runs retain
three keyframes each. `measure.py` is a local ignored timing probe; workload generation is reproducible
with the committed sample script and normal CLI. No holdout or real-world evaluation was performed.

## Measured demo and actual images
Self-created deterministic 1920x1080 MP4, 10 FPS, 60 frames, 6 seconds. Seed 2026; source ID,
transform parameters and frame labels saved in `video-inspection.metadata.json` alongside the MP4.
Sampled 24 frames: 18 eligible; six blurry/overexposed samples rejected. Every measured run selected:
- Frame 48, 4.8 seconds: appearance C (horizontal reflection).
- Frame 12, 1.2 seconds: appearance A (identity).
- Frame 38, 3.8 seconds: appearance B (180-degree rotation).
Minimum diversity distances for subsequent selections: 0.04511 and 0.04501; threshold 0.04.
These are known synthetic appearances, not actual product surface viewpoints.

Viewed all three actual `verified-run-1` PNGs: distinct orientations of sharp geometric details/text,
without choosing blurred/white samples. They remain 1920x1080. Integration tests also compare saved
PNG pixels exactly against decoded selected-frame pixels.

Five sequential end-to-end timed calls in one Python process, no separate warmup, including final
JSON and PNG writes: **0.891, 0.887, 0.845, 0.999, 0.906 seconds**.
Median **0.891 s**, interpolated p95 **0.980 s**. Detailed timing JSON at
`artifacts/video-slice/timing.json`. This is a small synthetic CPU timing measurement, not a
production performance claim. Report-internal time excludes final JSON serialization/write.
Final CLI smoke succeeded with indices 48,12,38 and report-internal 0.9423 seconds.
Direct trailing-whitespace check of the changed instruction/code/test/report files passed.

## Remaining limitations and stop point
Need real-video calibration, phone codec/VFR verification and labeled physical viewpoints.
White/glare ambiguity and appearance-diversity limitations remain. Native decoder has resource
bounds but no sandbox/hard time limit; public ingestion needs isolation. No real holdout metrics,
100-case suite, selection baseline study or adaptive-agent performance exists yet.
Stopped at requested milestone: QR/catalog, video/reference alignment, agent, UI/API, AWS and
learned matching remain pending review/authorization.
Suggested commit: `feat: add bounded OpenCV 5 video keyframe inspection slice`.
