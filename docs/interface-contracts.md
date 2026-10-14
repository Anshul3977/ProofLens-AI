# Local workstream contracts

Base checkpoint: 299543a (42 executed passing tests; unchanged four-case image smoke baseline).
Use existing OpenCV 5 + NumPy + pytest; do not add dependencies or alter image smoke labels/settings.
Keep original image CLI/API functions compatible. All real-image/holdout results remain unavailable.

## Ownership and isolation
- Worker A: src/prooflens/video.py, video_cli.py, scripts/generate_video_sample.py,
  tests/test_video.py, docs/video-engine-review.md. Review/improve already implemented engine,
  not duplicate it. Existing sample_video -> (metadata, list[FrameCandidate]) and inspect_video
  -> VideoReport signatures remain compatible. Native-resolution images and original tests retained.
- Worker B: src/prooflens/evaluation/, scripts/evaluate_suite.py, scripts/suite_gate.py,
  tests/test_evaluation_suite.py, eval_data/synthetic_manifest.json,
  eval_data/suite_baseline.json, docs/synthetic-evaluation.md. No edits to original evaluate/gate.
- Worker C: src/prooflens/agent/, tests/test_agent.py, docs/agent-engine.md.
- Lead: catalog/QR tools, integration CLI/video adapter and tests; all planning/contracts/policies,
  shared docs, README, existing CI and final integration reports.
Workers commit ONLY owned files after targeted tests; report actual commands/failures/commit IDs.
All testing in worktrees uses root .venv Python with PYTHONPATH set to that worktree's src,
so editable-install paths cannot accidentally test the root implementation.

## Evaluation interface (Worker B)
evaluation.dataset.load_manifest(path: Path | None = None) -> dict.
evaluation.dataset.render_case(case: dict) -> tuple[BGR uint8 reference, inspection].
Manifest cases contain id, source_id, split ('development'/'holdout'), seed, category,
transformations, expected_status and expected_next_action (documented ground truth).
Split by original source before augmentation. At least 100 cases spanning matching, blur, exposure,
glare, perspective, visible changes and mismatched reference pairs. Ground truth immutable once set.
Scripts default development only; holdout requires explicit --split holdout. Do not tune on holdout.
Evaluation reports denominators, actual latency, quality eligibility/alignment/regions, unavailable
metrics, failure records; initial baseline is executed fixed pipeline, no fabricated gains.
Lead adds agent and video baseline comparison using these APIs after integration.

## Agent interface (Worker C)
controller.InspectionAgent(workspace: Path, settings: Settings = Settings(),
                         max_steps: int = 40, max_recaptures: int = 2).
start(reference: Image | None, inspection: Image | None,
      identifier: str | None = None) -> Investigation.
resume(investigation_id: str, inspection: Image, reference: Image | None = None,
       identifier: str | None = None) -> Investigation.
load(investigation_id: str) -> Investigation.
Investigation dataclass: id, state, verdict (nullable string/str Enum), trace list,
request (nullable actionable text), human_review_required bool; serializable to JSON.
Trace records state/tool/reason/observations from actual calls; no invented measures.
Persist native evidence/reference and JSON atomically; validate investigation IDs and preserve trace
across restarts. Insufficient evidence/failure requests recapture, max attempts/steps escalate review.
No reference means manual catalog resolution; lead supplies QR/catalog integration.
Clear match -> continue through quality/alignment/differences, then consistent verdict.
Suspicious region -> actual targeted reinspection (crop/difference method and observation),
suspected mismatch/uncertainty ALWAYS requires human review, never automated accusation.
Poor quality -> grounded retake; poor alignment -> viewpoint request; new image resumes same ID.

## Lead integration
Trusted local JSON reference catalog + OpenCV QR structured resolution; manual selection supported.
Video wrapper samples/selects, supplies first eligible keyframe to agent, uses complementary frames
on evidence requests, preserves resumable state, records actual selected-image lineage.
Run counterfactual agent tests, complete regressions, unchanged smoke, synthetic development evaluation,
video uniform/top-quality/diverse comparison, and prepare report on isolated integration branch.
