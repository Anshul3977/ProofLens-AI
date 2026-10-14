# Phase 1 reliability review — October 14, 2026

## Acceptance assessment
The local vertical slice meets Phase 1's stated acceptance: OpenCV 5.0.0 runtime,
two-image CLI, typed quality metrics/recommendations, ORB/RANSAC alignment with structured
failure, difference overlay and local artifacts on success, and more than three executed tests.
This is functional acceptance, not proof of reliable performance on customer photographs.
Agent, UI and AWS requirements are future work and were not implemented in this review.

## Ranked weaknesses and fixes
Ranking considers evidence correctness and expected benefit per implementation effort.
Time ranges are engineering estimates for implementation plus focused tests, not measured durations.
No production failure frequencies or population-level improvement estimates are available.

| Rank | Reproduced weakness | Proposed fix | Expected reliability benefit | Estimated time |
|---|---|---|---|---|
| 1 | Filled external contours mark unchanged holes as evidence: 15,129 false pixels in a ring fixture | Intersect retained contour selection with the existing morphology evidence mask | Removes unsupported filled-interior evidence without changing thresholds or existing regions | 15–30 minutes |
| 2 | Equal-luminance color patch changes 10,000 pixels but grayscale comparison reports none | Benchmark a color-aware difference signal alongside luminance, using fixed lighting/color controls | Detects a known class of currently invisible appearance changes; false-positive tradeoff unmeasured | 2–4 hours |
| 3 | Sharp fixture with 25% white surface is blocked as glare (variance 224.40) | Separate possible glare observation from a blocking decision using white-surface/glare fixtures and spatial/detail evidence | Could reduce unnecessary recaptures; risk of accepting real glare needs validation | 3–6 hours plus real-image collection |

Only rank 1 was implemented. Before changing code, switched to local branch
`fix/preserve-difference-evidence` and backed up the original module in ignored artifacts.
The repository still has untracked project files; the branch is not a committed checkpoint.

## Measured before/after
Deterministic 240x240 synthetic image, gray background, dark rectangular ring.
Same reference, inspection, settings and valid mask before and after.

| Measurement | Before | After |
|---|---:|---:|
| Actual changed pixels | 9,428 | 9,428 |
| Reported evidence pixels | 24,557 | 9,428 |
| Unchanged pixels marked as evidence | 15,129 | 0 |
| Changed pixels retained | 9,428 | 9,428 |
| Center pixel evidence value | 255 | 0 |
| Candidate regions | 1 | 1 |

Visual inspection of before/after overlays confirmed the unchanged center is no longer tinted.
Local evidence: `artifacts/review/before-probes.json`, `after-ring.json`, and before/after masks/overlays.
These measurements apply only to the synthetic ring fixture. Morphology itself can still alter
small mask details; the fix specifically prevents contour filling from adding further evidence.

## Executed verification
- Before: `python scripts/quality_gate.py` — 17 tests passed in 1.01 s; 4/4 smoke cases pass.
- Added regression: `python -m pytest -q tests/test_vertical_slice.py::test_ring_change_preserves_unchanged_interior`
  — failed before implementation at the unchanged center assertion (expected 0, observed 255).
- After: `python scripts/quality_gate.py` — 18 tests passed in 1.14 s; 4/4 smoke cases pass;
  dataset/settings/generator contract and baseline outcomes unchanged.
- Fresh gate latency before: median 60.11 ms, p95 554.75 ms; after: median 46.97 ms, p95 551.37 ms.
  Single-run timings are noisy and include cold-start/artifact writes; no speed improvement is claimed.
- `python -m pip check` — no broken requirements.
- Reviewed saved overlays and the module diff against the saved pre-change copy.

## Changed files and limits
Production: src/prooflens/vision/differences.py (one mask intersection).
Regression: tests/test_vertical_slice.py. Tracking: PLAN.md, PROGRESS.md, this report.
No labels, baseline, thresholds, dependency versions, or additional features changed.
One fix attempt succeeded; no unsuccessful repairs. Color-only changes and white/glare ambiguity remain.
Recommended next task, requiring authorization: validate color-aware comparison on fixed synthetic and
real-photo development cases. No new milestone or other feature was started.
Suggested commit: `fix: preserve unchanged holes in difference evidence masks`.
