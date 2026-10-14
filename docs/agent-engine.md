# Bounded local inspection agent

Implemented on `worker/inspection-agent`, isolated from the lead integration and other workers.
Changed files: `src/prooflens/agent/__init__.py`, `src/prooflens/agent/controller.py`,
`tests/test_agent.py`, this report. No shared planning files or vision settings changed.

## API and state

`InspectionAgent(workspace: Path, settings=Settings(), max_steps=40, max_recaptures=2)`
exposes `start(reference, inspection, identifier=None)`,
`resume(investigation_id, inspection, reference=None, identifier=None)` and `load(id)`.
The returned `Investigation` is a dataclass, serializable using `dataclasses.asdict`;
fields include `id`, `state`, `verdict`, `trace`, `request`, `human_review_required`,
`identifier`, `recaptures`, `artifacts` and persisted `policy`.

States are `inspecting`, `manual_resolution`, `awaiting_evidence`, `complete`,
`human_review`. Verdicts are `consistent_with_reference`, `suspected_mismatch`,
`insufficient_evidence`, or null while processing. Human review and completed
investigations are terminal; only requests for evidence/catalog resolution resume.

Each trace entry records `step`, `state`, `tool`, `reason`, `observations`.
Tools: `reference_resolution`, `quality`, `alignment`, `differences`,
`targeted_inspection`. Successful observations come directly from the independent
OpenCV tools; failures record error type/message and no invented measurements.
Total trace count measures tool invocations, not individual OpenCV functions;
`quality` groups both image-quality calls, and unresolved-reference handling
records the quality check performed on retained input evidence.

## Decisions and safety

- Missing reference requests manual trusted catalog resolution and retains supplied
  valid evidence. Catalog and QR resolution remain the lead's responsibility.
- Quality warnings request a grounded retake; unusable trusted references and missing
  inspection evidence require human review.
- Failed geometry requests an alternative viewpoint, without running differences.
- Successful overlap runs global differences; no regions produces a qualified
  `consistent_with_reference` verdict, never an authenticity claim.
- Candidate regions trigger up to three actual native-resolution crop comparisons
  using the existing difference tool. The crop observations and overlay PNGs are saved.
  Local lighting compensation can disagree with global evidence; that uncertainty
  never erases the global candidate or automatically clears a suspicious inspection.
  Candidate differences always require human review. More than three regions are
  explicitly reported as not all reinspected.
- Lifetime step and recapture limits, plus exact settings, are persisted. A new
  controller with looser constructor bounds cannot reset an existing investigation's
  limits or thresholds. Exhaustion escalates without claiming an unexecuted tool.
- IDs are canonical UUIDs; resolved directories cannot escape the workspace.
  Native PNG files and state JSON use temporary files and atomic replacement.
  Trace/evidence survive restart between evidence requests. Persistence errors propagate.

This is a deterministic typed perception–decision–action controller, not an LLM,
unattended runner or multi-agent runtime. No dependencies, cloud calls or credentials
were added. Persistence supports one writer per investigation; concurrent writers,
power-loss transactions spanning several files, and automatic recovery from a crash
mid-tool are not guaranteed. An interrupted `inspecting` state needs explicit review.
The image heuristics retain their known grayscale/color and glare/white-surface
limitations. A consistent result is based on one geometrically eligible image pair;
the lead's video adapter supplies complementary images when recapture is requested.

## Executed verification (Windows, OpenCV 5.0.0, Python 3.13.2)

All commands used the root environment and explicit worktree source path:

```powershell
$env:PYTHONPATH='C:\Users\palar\Downloads\prooflens-worktrees\agent\src'
& 'C:\Users\palar\Downloads\recheck-ai\.venv\Scripts\python.exe' -m pytest -q tests/test_agent.py
& 'C:\Users\palar\Downloads\recheck-ai\.venv\Scripts\python.exe' -m pytest -q
& 'C:\Users\palar\Downloads\recheck-ai\.venv\Scripts\python.exe' scripts/evaluate.py
& 'C:\Users\palar\Downloads\recheck-ai\.venv\Scripts\python.exe' scripts/quality_gate.py
```

Initial owned test run: **17 passed in 1.66 s**, no failed tests. Initial whole suite:
**59 passed in 2.84 s**. Review added failed-tool tracing and four additional bounds
tests; final whole suite: **63 passed in 3.29 s**, comprising 42 original tests and
21 agent tests. Final quality gate independently reran **63 passed in 3.27 s** and
reported **4/4 unchanged smoke cases passed**, no failures. The deliberately corrupt
MP4 test emits an expected FFmpeg `moov atom not found` diagnostic.

The standalone smoke evaluation also passed **4/4**, retaining recorded dataset,
generator and settings hashes. Final gate measured smoke median **47.213 ms**, p95
**556.726 ms**, versus recorded baseline **70.573 ms / 645.846 ms**. These are
informational single-run smoke timings, not an agent speed improvement or latency gate.
No repair attempt was needed for a failed test. No real-world or holdout results exist;
remote CI was not executed here.

Tests exercise clear, blur, glare, poor alignment, suspicious-region crop inspection,
unknown-reference persistence/manual resolution, missing evidence/bad reference,
cross-controller follow-up with preserved ID/trace, cumulative recapture and tool
budgets, constructor bounds, safe IDs, stored settings and injected real tool errors.
The counterfactual test changes only inspection pixels with fixed reference/identifier
and verifies that blur stops after quality while clear evidence selects alignment.

Next task: lead integration and identical-case fixed-pipeline/adaptive decision
measurement, plus video lineage tests. No further feature work in this worker.
