# Synthetic development evaluation

This suite creates **100 self-authored geometric image cases**: ten original source scenes,
ten derivatives each. Eight sources (80 cases) are development; two (20 cases) are holdout.
Source membership is assigned before augmentation. Mismatched pairs use another source in the
same split, and the loader rejects leakage through either member of a pair. No customer data,
downloaded images, fraud incidents or physical product identity claims are involved.

`eval_data/synthetic_manifest.json` freezes source/case seeds, exact transformation parameters,
source pairs, intended actions and ground truth. `render_case` creates uint8 BGR 480×360 images
using seeded NumPy and substantive OpenCV blur, drawing and perspective operations. The suite
spans matching, blur, low/high exposure, possible glare, perspective, visible modifications and
mismatched references. Source seed fixes the original scene; case seed controls any sensor noise.
Determinism is tested on development only. Holdout metadata is validated for separation, but
holdout images were **not rendered or evaluated** during development.

## Commands

From the repository with its installed environment:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/evaluate_suite.py
.\.venv\Scripts\python.exe scripts/suite_gate.py
```

The evaluation defaults to development. `--split holdout` explicitly selects the protected split
for a later authorized final evaluation; it is never selected by the gate. Reports and failure
images go under ignored `artifacts/evaluation/`. Neither script rewrites the baseline by default.
The initial baseline was explicitly recorded with `--output eval_data/suite_baseline.json`.
No earlier image smoke manifest, baseline, evaluation script or gate was edited.

## Metric definitions and baseline

The fixed pipeline runs quality → alignment → differences; its **suggested action mapping** is:
quality insufficient → `request_retake`; alignment failed → `request_alternative_viewpoint`;
candidate regions → `targeted_inspection`; no candidate regions → `continue_inspection`.
Invalid input maps to `human_review`, although the generated suite has no invalid-image cases.
These suggestions are a baseline policy, not autonomous agent tool calls or actual human decisions.
The agent comparison must measure actual agent observations/actions separately on these same cases.

Baseline executed on Python 3.13.2, OpenCV 5.0.0 (Windows CPU):

| Metric | Recorded result |
|---|---:|
| Expected pipeline status/action cases | 80/80 |
| Binary acceptable-quality classification | 80/80 |
| Alignment successes among geometrically eligible, acceptable pairs | 48/48 |
| Expected next-action suggestion | 80/80 |
| Candidate mismatch precision | 16/16 = 1.0 |
| Candidate mismatch recall | 16/24 = 0.6667 |
| Abstentions (no completed difference inspection) | 32/80 = 0.4 |
| Image-pipeline latency median / p95 | 45.845 ms / 176.294 ms |

Precision counts candidate-positive cases that are labeled synthetic mismatches. Recall counts
all mismatch-positive cases, including abstentions as undetected positives. Eight mismatched
reference pairs fail alignment and therefore produce no candidate regions: this lowers recall
even though their expected safe viewpoint request passes. Quality accuracy is binary quality
acceptability, not independent blur/glare/exposure subtype classification. Alignment denominator
excludes intentionally poor-quality images and unrelated reference pairs.

Latency measures a single sequential evaluation run, one call per case, including pipeline
artifact writing; fixture generation and copying failure evidence are excluded. No repeated-run
performance or real-video latency claim follows from these numbers. The final baseline was
recorded while other development workers were active; earlier runs measured 31.014 / 48.926 ms.
This observed variability is why latency has no gate threshold. Tool calls, real-world
accuracy, pixel-region precision/recall, human review, frame selection, agent actions and holdout
performance are unavailable here. Rectangle ground truth is available for future region metrics.

## Gates, failures and review

The dedicated suite gate reruns development and compares dataset, generator/evaluator, settings
and OpenCV fingerprints plus case identity and recorded categorical outcomes. Previously passing
cases cannot fail. Other changed outcomes must represent a newly passing labeled case; unexplained
drift fails. Latency is informational. Contract migrations require review; baseline rewriting is
never automatic. The full test suite and existing smoke gate are separate required checks.

Measured initial setup: 8 dedicated tests passed in 4.57 seconds; fresh suite gate passed with
zero categorical regressions. All 50 worktree tests then passed in 6.04 seconds. The original
four-case smoke evaluation passed 4/4; its unchanged quality gate reran 50 tests (5.93 seconds)
and passed with no smoke regressions. The corrupt-video test's expected decoder diagnostic
(`moov atom not found`) was present and is not a test failure. The dedicated suite gate's
latency differed (median 30.990 ms / p95 36.800 ms), which is
not treated as a reliability improvement or a gate threshold. There were no failed tests or
test repair attempts in this workstream. A post-commit portability review found that Windows
generated CRLF manifest bytes were normalized by Git while the recorded fingerprint hashed the
original bytes. The manifest was normalized to LF and the initial baseline/gate/tests rerun;
labels and parameters were unchanged. This prevents cross-worktree fingerprint drift.

Failure evidence is saved for incorrect expected outcomes **and** missed mismatch candidates.
Example `source-00-case-06` uses independent texture/layout from source 01 against source 00;
inspection evidence was visually opened and checked. It fails alignment, safely requests another
viewpoint and has no detected mismatch region. The same limitation affects eight cases. No labels,
quality thresholds or existing vision implementation were changed to hide it.

These scenes are deliberately simple and severe quality degradations are easy to classify.
80/80 expected actions therefore do not establish warehouse reliability. This is the initial
recorded baseline, with no claimed before/after improvement. Next: compare the integrated agent
and keyframe policies on development, and collect separate consented/self-created real validation
data before tuning or reporting operational accuracy. Do not tune on the holdout.
