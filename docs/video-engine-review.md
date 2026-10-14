# Video engine focused reliability review

Worker A, isolated `worker/video-engine` worktree; Python 3.13.2 / OpenCV 5.0.0.
Owned changes: `src/prooflens/video.py`, `tests/test_video.py`, this report.
No dependencies, image-pipeline settings, smoke labels or evaluation thresholds changed.

## Observed weakness and correction

The greedy selector always started with the highest-quality candidate. A candidate near the
center of three complementary appearances can be below the diversity threshold against each
of them, although those three are mutually sufficiently different. This reproducibly returned
one keyframe despite a feasible three-frame set. Expected impact: avoid unnecessary recapture
when useful evidence already exists; real-video failure frequency remains unknown.

Added a deterministic compatible-set fallback only when greedy selection returns fewer than
three. It checks eligible, distinct frame identities, prefers three over two, enforces the same
pairwise diversity threshold, and ranks feasible sets by mean quality and minimum appearance
distance using the existing weight. Sampling permits at most 60 candidates (34,220 triples).
Successful existing greedy selections remain unchanged. Report reasons now describe either
selection path accurately.

The controlled-descriptor regression failed before the fix: selected `[0]` instead of `[1,2,3]`.
After the fix it selects `[1,2,3]`, passes repeated deterministic selection and pairwise-distance
checks, and selects only two when identities are duplicated. This proves selector behavior on
the fixture, not physical viewpoint coverage or real-video reliability.

## Executed verification

Every Python invocation used the root venv executable and worktree `src` in `PYTHONPATH`:

```powershell
$env:PYTHONPATH='C:\Users\palar\Downloads\prooflens-worktrees\video\src'
& 'C:\Users\palar\Downloads\recheck-ai\.venv\Scripts\python.exe' -m pytest -q
& 'C:\Users\palar\Downloads\recheck-ai\.venv\Scripts\python.exe' -m pytest -q tests/test_video.py::test_selection_recovers_feasible_triplet_blocked_by_best_quality
& 'C:\Users\palar\Downloads\recheck-ai\.venv\Scripts\python.exe' scripts/quality_gate.py
& 'C:\Users\palar\Downloads\recheck-ai\.venv\Scripts\python.exe' scripts/generate_video_sample.py --output sample_data/generated/video-review.mp4
& 'C:\Users\palar\Downloads\recheck-ai\.venv\Scripts\python.exe' artifacts/benchmark_video.py
& 'C:\Users\palar\Downloads\recheck-ai\.venv\Scripts\python.exe' -m pytest -q tests/test_video.py
git diff --check
```

- Before: existing full suite **42 passed in 2.17 s**.
- New targeted test before correction: **1 failed** (intended reproduction).
- After correction: full suite **43 passed in 2.02 s**.
- Quality gate: **43 passed in 2.01 s**, **4/4 unchanged smoke cases**, no contract failures.
- Expanded regression assertions: owned video suite **25 passed in 1.21 s**.
- No unsuccessful repair cycles; first implementation passed. Native decoder warning from
  deliberately corrupt MP4 is expected; structured-invalid-video test passed.
- `git diff --check`: passed.

## Same-video before/after measurements and visual review

Generated one deterministic six-second 1080p MP4 (60 frames, 10 FPS), sampled 24 candidates,
and ran each implementation five times on that same file. The benchmark loaded the original
`video.py` from the worktree base Git commit as a separate module and the revised implementation
from worktree `src`. Both used identical settings and supporting quality code; all ten runs
selected indices `[48,12,38]` and reported `KEYFRAMES_SELECTED`.

| End-to-end time, decode/scoring/PNG writes | Before | After |
|---|---:|---:|
| Median, 5 runs | 0.829256 s | 0.820559 s |
| p95, NumPy interpolated percentile | 0.834365 s | 0.824137 s |

Before seconds: `[0.829256,0.826755,0.830223,0.828134,0.835400]`.
After seconds: `[0.821029,0.820559,0.820498,0.824914,0.813276]`.
This normal fixture uses the unchanged greedy path. Small timing differences are observational
noise, not a claimed performance improvement. Timing excludes final JSON writing as documented
by `inspect_video`; no production latency claim or acceptance threshold is inferred.

Opened and inspected all three resulting PNGs: original, reflected and rotated synthetic tiled
patterns are visibly distinct; no blur/overexposure classes were selected. Native-resolution
and decoder-pixel-equality tests continue to pass. Generated videos, PNGs and timing JSON remain
ignored local artifacts, not committed.

## Limitations and next work

- Grayscale thumbnail distance can treat lighting changes as diversity and cannot certify actual
  warehouse viewpoints. Quality/glare heuristics need separate real-video validation.
- Fallback adds bounded combination work on insufficient-selection cases; it is not learned matching.
- Native FFmpeg decoding has no process-level timeout or sandbox. File/frame/memory/dimension
  bounds remain tested, but public upload hardening remains outside local scope.
- No real video, holdout, AWS, learned matcher or remote CI results were produced.

Recommended next task: lead integrates this commit with agent/evaluation work and runs the full
integrated gates, then compares uniform/top-quality/diverse selection on identical candidates.
