# Bounded autonomous local integration — October 14, 2026

## Authorization, audit and checkpoint
User explicitly authorized video, synthetic evaluation, bounded resumable agent and local integration,
with up to three real parallel workers and verified local feature commits. Earlier per-task stop rules
were superseded. Read all five project files, checked Git/ignore/history, reran baseline before changes.
Actual baseline was 42 tests (the attachment's 18-test description was stale) and four passing smoke cases.
No unknown user edits found. Reviewed prior untracked foundation committed as 299543a; interface and
approval contracts committed as 40f86fb. No secrets, generated artifacts or environments staged.

## Genuine parallel work and controlled integration
Native subagents ran on three separate worktrees; ownership was established before implementation.
No concurrent shared-file editing. Root retained contracts, catalog, integration and planning.

| Worker | Branch/worktree | Verified commit | Local result before integration |
|---|---|---|---|
| A video | worker/video-engine / Downloads/prooflens-worktrees/video | cd0ad6c | 43 tests, unchanged 4-case smoke |
| B evaluation | worker/evaluation / Downloads/prooflens-worktrees/evaluation | 8fe230a | 50 tests, development suite gate and unchanged smoke |
| C agent | worker/inspection-agent / Downloads/prooflens-worktrees/agent | 1d38679 | 63 tests, unchanged smoke |

Workers set PYTHONPATH to their worktree src while using root .venv interpreter, preventing accidental
testing of root's editable installation. Diffs reviewed; commits cherry-picked in controlled sequence
onto `integration/local-inspection` (eb012db, 84e4498, d2ba5cd). No main branch was created or merged.
Root implemented tested catalog/QR and keyframe baselines as 254e720, then integration adapters,
agent comparison, review repairs, regressions, documentation and final verification.

## Completed behavior
- Preserve original static-image pipeline/CLI and unchanged smoke contract.
- Video engine retains native 1080p frames; fallback now finds a compatible three-frame set when
  the best individual seed blocks it. Failing-before reproduction selected one; fixed selects three.
  Existing demo selection remains [48,12,38].
- 100 recorded seeded source-grouped synthetic cases: 80 development, 20 holdout reserved.
  Renderer, immutable manifest, baseline, failure artifacts and gates implemented.
- Typed deterministic agent: persisted UUID/state/evidence/reference, quality/geometry/difference tools,
  native targeted crop inspection, grounded requests, cumulative step and recapture limits and resume.
  Suspicious results always require human review. It is not an LLM/continuous coding runner.
- Trusted local catalog, manual selection, multi-code QR lookup across selected frames, structured
  unknown/unreadable/conflicting reference handling. Catalog association is not authenticity proof.
- Video adapter inspects complementary selected evidence after consistency or when requested;
  keeps one investigation ID, reports inspected/uninspected selected indices, stops for human review.
- JSON investigation report/action trace and local CLI; resume works across process/controller restart.
- Approval policy/record, plans/progress, reproducibility docs and expanded CI definition.
  Remote CI was not executed; no cloud/publication/dependency installation/secret access occurred.

## Independent review and repairs
Read-only worker reviews checked actual code, saved outputs and tests rather than trusting summaries.
Reproduced and fixed during integration, with focused regressions:
1. Core resume accepted a different reference/product under the same investigation ID; now rejected
   outside manual-resolution state, before retry counters/state mutate.
2. Selection coverage denominator included unsampled appearance classes; sampled and full-video
   denominators are now separate.
3. Duplicate metadata frame indices silently replaced labels; now rejected before dictionary creation.
4. QR readable only in a later keyframe was missed; now all selected frames scanned, conflicts dominate.
5. Later suspicious selected frame could be left unexamined after first consistent result; now inspected
   with preserved lifetime policy and trace. Uninspected evidence is explicit on review escalation.
6. Single-code decoding missed two conflicting codes in one frame; multi-code decoder now detects them,
   and conflicting earlier evidence cannot be overridden by a later clean code.
No existing tests were disabled, settings relaxed, or labels altered. B corrected Windows CRLF manifest
serialization before freezing its baseline; seeds/ground truth unchanged. No failing task exceeded three
repair attempts or remained blocked. Known model/data limitations are retained rather than tuned away.

## Final executed verification
```powershell
.\.venv\Scripts\python.exe scripts/quality_gate.py
.\.venv\Scripts\python.exe scripts/suite_gate.py
.\.venv\Scripts\python.exe scripts/agent_gate.py
.\.venv\Scripts\python.exe scripts/benchmark_keyframes.py sample_data/generated/video-inspection.mp4 sample_data/generated/video-inspection.metadata.json --output artifacts/evaluation/keyframes-final.json
.\.venv\Scripts\python.exe -m pip check
git diff --check
```
Final complete suite: **92 passed in 8.00 seconds**. Original smoke **4/4**, synthetic development
gate **80/80**, agent regression gate **passed with zero failures**. pip check: no broken requirements.
Expected native FFmpeg corrupt-input diagnostic occurs in negative tests. Actual cv2 remains **5.0.0**.
Holdout was neither rendered nor evaluated; sources and paired sources are disjoint across splits.
Additional scoped tests exercised original static workflow, actual MP4/catalog/agent integration,
counterfactual quality actions, native reinspection, multi-code/manual identity and restart follow-ups.

## Measured benchmark results (synthetic development only)
Same 80 source-grouped 360x480 image pairs and unchanged vision thresholds; one measured pass per
system, no separate warmup, timings include actual artifact persistence but exclude fixture rendering.
The fixed vision baseline has safety aborts; agent additionally re-inspects and enforces human control.

| Metric | Fixed vision pipeline | Actual bounded agent |
|---|---:|---:|
| Labeled next actions correct | 80/80 | 80/80 |
| Alignment success on eligible pairs | 48/48 | 48/48 |
| Candidate mismatch precision | 16/16 = 1.0 | 16/16 = 1.0 |
| Candidate mismatch recall | 16/24 = 0.6667 | 16/24 = 0.6667 |
| Abstention | 32/80 = 40% | 32/80 = 40% |
| Human review | No review policy | 16/80 = 20%; all suspicious findings |
| Actual vision API calls | 264 total; median 4 | 280 total; median 4 |
| Latest gate median/p95 latency | 30.83 / 40.53 ms | 39.90 / 51.93 ms |

Frozen initial comparison at eval_data/agent_baseline.json: fixed 32.87/52.05 ms, agent 42.95/49.74 ms.
Variability is noise/workload effects; no speed gain or detection-accuracy improvement is claimed.
16 extra agent calls are actual targeted crop difference inspections. API-call counts are instrumented;
logical trace steps are separately recorded. Eight mismatched source pairs abstain on poor alignment,
so they remain missed mismatch candidates. Expected safe actions can pass while detection recall is limited.
Failure evidence is retained under ignored artifacts; case source-00-case-06 exemplifies the limitation.
Viewed source-00-case-05 actual overlay and native crop: marked rectangle and targeted local evidence
match recorded observations, not a claimed physical defect/fraud incident.

Identical 24-frame candidate selection on six-second 1080p synthetic MP4:

| Selector | Quality-eligible selected | Labeled appearance coverage | Duplicate appearance |
|---|---:|---:|---:|
| Uniform | 1/3 | 1/3 | 0 |
| Top quality | 3/3 | 2/3 | 1 |
| Quality + diversity | 3/3 | 3/3 | 0 |

These are artificial appearance classes, not verified physical viewpoints or general selection accuracy.
Actual integrated CLI demo took **3.340 s** including frame scoring, reference inspection, persistence
and report generation (report's final write excluded from internal timer). It failed geometry on first
frame48, requested an alternative, consumed frame12, then inspected frame38 before consistent completion.
Logical tool trace: quality/alignment, quality/alignment/differences, quality/alignment/differences.
Report: artifacts/integration-demo/reports/a57322ef79804b3aa597fb7bc878734e.json.

## Remaining limitations and review checkpoint
- Synthetic results only; no real-world validation, tuned confidence or final holdout result.
- Planar ORB geometry, grayscale/color-only misses, white/glare ambiguity and appearance proxy limits remain.
- Native video decoder is bounded by metadata/resources, not sandbox/hard timeout; no public upload service.
- Single-writer investigation persistence; mid-tool crash recovery and concurrent mutation are not supported.
- At most three regions inspected; suspicious findings are human-reviewed, not automatically accused.
- Verdicts concern inspected selected reference-visible evidence; they do not cover unseen product surfaces.
- No FastAPI/Streamlit, AWS, ALIKED/LightGlue inference, COOL or segmentation-model integration.

All authorized local workstreams are integrated and verified on an isolated branch, ready for human
review. No remaining local blocker or required approval to finish this branch. Further main merge,
external push/cloud/deployment require explicit approval under APPROVAL_POLICY.md. Rollback is local
commit revert, preserving checkpoint 299543a and independent worker branches. No history rewrite needed.
Recommended next milestone: review this integration, authorize real-video validation and then UI/API.
