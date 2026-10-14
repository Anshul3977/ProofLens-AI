# ProofLens AI evaluation contract

## Dataset separation
- `eval_data/smoke.json`: self-created deterministic synthetic fixtures, functional checks only.
- Development: future consented/self-created real photographs with fixed labels; not collected yet.
- Holdout: future separately stored frozen manifest/images; never used for tuning. Not collected or evaluated.
- Version manifests, generator and settings; never edit labels/thresholds merely to improve scores.
- Video-first augmentation protocol: fixed recorded seeds, source IDs, transformations/parameters,
  source frame indices/timestamps, quality labels, reference pairing, region ground truth where meaningful.
  Include blur, glare, exposure, perspective, visible modifications and mismatched reference pairs.
  Split by original source/product/session BEFORE augmenting; related derivatives cannot cross splits.
  Report synthetic and real-world results separately; synthetic modifications are not real fraud incidents.
  The 100-case synthetic suite and real-world set are future work, not generated yet.

## Current Phase 1 smoke protocol
`scripts/evaluate.py` generates each labeled fixture in memory using a fixed seed, runs the same
local pipeline, writes temporary artifacts and saves case outcomes in JSON, and records actual wall-clock latency including
artifact writing. Temporary images are removed after the run; use the CLI for retained visual evidence.
No warmup or repeated-run latency study is claimed. `eval_data/phase1-baseline.json`
records the first smoke run; latency is informational and has no acceptance threshold.
`scripts/quality_gate.py` executes pytest and evaluation afresh, then requires identical dataset,
settings and generator digests and no failing cases. Comparison with the baseline is per case.
Gate failure requires diagnosis; do not update baseline automatically. Settings/dataset changes need
an explicit reviewed evaluation-contract migration. The initial baseline is not a fixed-pipeline vs agent benchmark.

## Future full metrics
Quality classification accuracy against labeled quality/action annotations; alignment success rate
on eligible pairs; region mask IoU/precision/recall against labeled candidate regions; task success;
mismatch precision/recall and false-positive/negative rates after a decision policy exists;
correct next action; recapture and human-review/abstention rates; median/p95 processing latency;
tool calls per investigation. Always state denominators, eligibility, data provenance and limitations.
Use identical cases and preprocessing budgets for the fixed-sequence baseline and adaptive agent.
Report unavailable metrics as unavailable, never as zero or fabricated performance.
Set numerical performance thresholds only after baseline measurements and user review.

## Video slice verification
Test deterministic bounded sampling, quality scores/order, quality rejection, distinct-frame selection,
insufficient quality/diversity, native resolution, invalid/corrupt/oversized input and decoding limits.
Use self-created synthetic MP4 fixtures with known frame classes; do not change the old image baseline.
Current diversity is a visual-appearance proxy, not calibrated physical viewpoint measurement.
Record actual per-run end-to-end latency including decode/scoring/saving; repeated-run median/p95
may be reported with repetitions and workload, without asserting production performance.
Future frame-selection metrics: selected-frame quality eligibility/precision, coverage of labeled views,
duplicate rate, ability to select three, and downstream alignment; compare uniform and top-quality
selection against diverse selection on identical candidate sets. No arbitrary accuracy gates.
Future investigation metrics also include correct next action, mismatch precision/recall,
abstention/human-review rate and tool calls per investigation, plus failure examples and limitations.

## Required future scenarios
1. Clear matching image → continue inspection.
2. Blur → grounded retake request.
3. Severe glare → appropriate recapture/review.
4. Failed alignment → alternative viewpoint request; perspective match → proceed when reliable.
5. Suspicious visible region → targeted inspection.
6. Unknown identifier → manual resolution.
7. Insufficient/ambiguous evidence → human review.
8. Follow-up image → resume existing investigation.
Counterfactual test: alter visual evidence while holding context fixed and verify the next action changes.
Only the current quality/alignment/difference behavior is testable before Phase 3.

## Regression and improvement rules
All critical tests and previously passing cases must pass; no critical safety/data-leakage regressions.
Compare actual recorded baseline results; claimed gains must be reproducible.
Choose the highest-impact failing category; change one major variable at a time; reject changes failing gates.
Maximum three unsuccessful repair attempts, then report the limitation and stop.
No continuous autonomous development or automatic baseline rewriting is enabled.
