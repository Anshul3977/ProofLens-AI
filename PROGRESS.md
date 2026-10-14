# ProofLens AI progress

## October 14, 2026 — GitHub publication preparation
- User explicitly supplied the GitHub repository and main push commands, authorizing initial publication.
- Existing local history preserved; remote ls-remote succeeded with no refs (empty repository).
- Configured origin to https://github.com/Anshul3977/ProofLens-AI.git; verified generated artifacts,
  video/images and .venv remain ignored, and reviewed tracked file list before push.
- Publication will use a main branch at the verified integration history; worker branches/worktrees retained.
- Last executed complete tests remain 92 passing plus all three gates; only approval/progress docs change.

## October 14, 2026 — Authorized parallel local development
- Read all five instruction files and inspected Git state/history/ignore rules before modifications.
  No unknown user changes found: prior session files were untracked, with no commits.
- Baseline rerun: 42 tests passed in 2.01 s; unchanged four-case image smoke gate passed.
- Reviewed and checkpointed project files as 299543a; contracts/policies as 40f86fb.
- Native subagents and worktrees available: three real workers running on worker/video-engine,
  worker/evaluation, worker/inspection-agent under Downloads/prooflens-worktrees.
- Lead branch integration/local-inspection owns catalog, integration, planning and final review.
- Added APPROVAL_POLICY.md and APPROVALS.md; no main/cloud/push/credential action approved or attempted.
- Lead QR/manual trusted catalog tests: 5 passed in 0.28 s; no authenticity claim.
- Existing historical stop rules above are superseded by this user authorization. Final results follow below.

### Parallel milestone verified completion
- Actual independent workers completed and committed: video cd0ad6c (43 tests), evaluation8fe230a
  (50 tests), agent1d38679 (63 tests). Ownership/diffs reviewed; cherry-picked to integration/local-inspection
  as eb012db, d2ba5cd, 84e4498. No conflicting edits, no main merge/push.
- Root added trusted QR/manual catalog, video-agent adapters, same-ID follow-up CLI, 100-case
  development evaluation integration, actual fixed-vs-agent instrumentation and keyframe baselines.
- Independent read-only reviews reproduced identity/reference substitution, sampled-denominator and
  duplicate-label bugs, missed later/multi-code QR conflicts and early per-video consistency. Fixed with
  regressions; review findings and limitations preserved in docs/local-integration-report.md.
- Final executed quality_gate.py: **92 tests passed in 8.00 s**, old smoke **4/4** unchanged.
  suite_gate.py: **80/80** development outcomes pass; agent_gate.py: no failures. pip check passed.
- 100 manifest cases (80 dev,20 holdout) generated deterministically by source; holdout untouched.
  Identical-image fixed/agent comparison: actions80/80, eligible alignment48/48, candidate precision1.0,
  recall0.6667, abstention32/80 both. Agent human review16/80 and actual API calls280 vs fixed264.
- Latest comparison median/p95: fixed30.83/40.53ms, agent39.90/51.93ms. No measured accuracy/speed gain claimed.
- Actual1080p integrated CLI: all selected indices48,12,38 consumed conditionally; geometry failure changed
  next action and led to complementary evidence. Finalconsistent within inspected evidence; 3.340s internal time.
- Keyframe baseline on same24 candidates: uniform1/3 eligible and1/3 appearances; topquality3/3 and2/3;
  diverse3/3 and3/3. Viewed actual overlay/crop and worker videoPNG evidence; synthetic only.
- Expanded CI definition includes suite/agent gates; not executed remotely. No new dependencies,
  credentials, paid resources, AWS, UI/API, learned matching or publication.
- Worktrees retained with clean worker commits; root integration branch prepared for review.
  Next recommended milestone: human integration review, then real-video validation and UI/API authorization.

## October 14, 2026 — Video-first specification upgrade (before implementation)
- Updated AGENTS.md, PRODUCT_SPEC.md, PLAN.md and EVAL_SPEC.md for warehouse video returns,
  P0/P1/P2 priorities, source-grouped evaluation and immediate video-only acceptance.
- Authorized scope is local MP4 sampling/quality/diverse keyframes, JSON/artifacts/tests only.
- Verified actual cv2 5.0.0; VideoCapture and VideoWriter present; build reports FFmpeg enabled.
  Actual codec encode/decode verification will occur with the synthetic MP4 integration tests.
- Preserve image pipeline and baseline. No AWS, learned matcher, agent, API or UI is started.

### Video milestone completion
- Implemented video.py, video_cli.py, generate_video_sample.py and test_video.py; updated README,
  architecture/limitations and docs/video-slice-report.md. No dependencies added.
- Repair 1: mean diversity diluted sparse detail (20 passed/2 failed); changed metric to RMS,
  then 22 video tests passed. Repair 2: actual 1080p thumbnail lost detail; increased descriptor
  resolution to 160x90 and added regressions; 24 video tests passed. Thresholds/labels unchanged.
- Final full gate: 42 tests passed in 2.15 s; four existing image cases still match unchanged baseline.
- Viewed three generated native 1920x1080 PNGs. Five runs consistently selected indices 48,12,38
  from 24 samples of a six-second synthetic MP4; excluded blurry/overexposed frames.
- End-to-end processing including artifact/report writes: median 0.891 s, p95 0.980 s (five sequential
  runs, no separate warmup). Synthetic only; no real-video or baseline-selection performance claim.
- Verified MP4 encoding/decoding and pip check. Detailed commands/results: docs/video-slice-report.md.
- Final CLI invocation succeeded (indices 48,12,38; report-internal 0.9423 s); changed-file
  trailing-whitespace check passed. Project files remain untracked; no Git commit was created.
- Plan updated to complete locally/awaiting review. No agent, catalog, UI/API, AWS or learned matcher started.
- Next recommended milestone: review video slice, then authorize labeled video evaluation and QR/catalog integration.
- Suggested commit: `feat: add bounded OpenCV 5 video keyframe inspection slice`.

## October 14, 2026 — Phase 0/1 implementation
- Empty Windows workspace audited; default Python 3.9.13, installed alternate Python 3.13.2 selected.
- OpenCV headless wheel 5.0.0.93 installed; actual cv2 version 5.0.0 verified.
- Built typed quality checks, ORB/RANSAC alignment, valid-overlap masks, differences, CLI and local artifacts.
- Original 12 tests passed. CLI revealed a perspective fixture false rejection at blur threshold 80.
  Threshold changed to 50 based on observed synthetic values; regression test added; 13 tests passed.
  This historical adjustment predates the new locked evaluation contract; it is not a measured model improvement.
- See docs/phase1-report.md for exact commands, outputs and known limitations.

## October 14, 2026 — Bounded workflow setup
- Updated AGENTS.md and created PRODUCT_SPEC.md, PLAN.md, EVAL_SPEC.md and this log.
- Added synthetic smoke manifest and recorded first executed baseline; no customer data or holdout exists.
- Added scripts/evaluate.py and scripts/quality_gate.py. Gate executes fresh tests/evaluation,
  rejects changed contract fingerprints, missing cases and failing/regressed case outcomes.
- Added four negative/positive gate tests, .gitattributes and Windows GitHub Actions workflow.
- Phase ordering updated per latest user instruction; no Phase 2 full benchmark or Phase 3 agent begun.
- No dependencies, vision settings, existing labels, or existing pipeline behavior changed in this milestone.
- Initial local gate: 13 tests passed in 1.07 seconds; four of four smoke cases matched baseline.
- Baseline latency median 70.57 ms / p95 645.85 ms; next fresh gate median 55.94 ms / p95 622.41 ms.
  Single executions include cold-start effects and artifact writes; these are informational, not improvement claims.
- Final executed verification: `scripts/audit_environment.py` confirmed cv2 5.0.0/Python 3.13.2;
  `python -m pip check` reported no broken requirements; `scripts/evaluate.py` passed 4/4 cases;
  `scripts/quality_gate.py` executed pytest (**17 passed in 1.01 seconds**) and passed all four
  baseline comparisons with zero failures. Standalone evaluation median/p95: 51.46/612.00 ms;
  gate fresh evaluation: 48.70/557.52 ms. No latency improvement claim or threshold.
- `git diff --check` returned success, but all project files are still untracked so this is not
  a whitespace review of their contents. Source/tests/workflow were reviewed directly.
- No test failures in this milestone; no repair attempts used. CI remains unexecuted remotely.
- Suggested commit: `chore: establish bounded ProofLens workflow and synthetic regression checks`.

## Boundaries and next task
Guided session work with up to three repairs within an approved milestone is supported by repository
instructions and executed tools. No continuous runner, separate role agents, automatic rollback,
push/merge/deployment, or remotely executed CI is enabled or claimed.
No new failures required repair during workflow setup. Real-photo quality, region ground truth,
development/holdout separation, fixed-vs-agent metrics, and agent action scenarios remain unimplemented.
Next: user review, then approve Phase 2 full evaluation harness and labeled dataset protocol.

## October 14, 2026 — Authorized Phase 1 reliability review
- Reviewed product/plan/evaluation criteria and vision/CLI/pipeline implementation.
- Before gate: 17 tests passed; four smoke outcomes match original baseline.
- Reproduced three weaknesses: filled mask interiors, invisible equal-luminance color changes,
  and white-surface glare rejection. Ranking and estimated fix times: docs/phase1-review.md.
- Highest-priority fix only: intersect retained contours with post-morphology evidence.
- New ring regression failed before implementation; after fix all 18 tests passed in 1.14 s.
- Same fixture: falsely marked unchanged pixels 15,129 → 0; all 9,428 changed pixels retained.
- Gate still passes all four cases with unchanged contract fingerprints and baseline outcomes.
- Before/after overlays viewed; production diff reviewed against original backup; pip check passed.
- Local branch fix/preserve-difference-evidence created; original file backed up in ignored artifacts.
  No commit/push/merge/deployment. Labels, baseline, thresholds and dependencies unchanged.
- Changed differences.py, test_vertical_slice.py, PLAN.md, PROGRESS.md, docs/phase1-review.md.
- No failed repair attempts; only the requested fix implemented. Remaining two weaknesses deferred.
- Suggested commit: `fix: preserve unchanged holes in difference evidence masks`.
