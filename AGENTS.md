# ProofLens AI

This workspace builds ProofLens AI for the OpenCV AI Competition 2026.
The user's ProofLens brief supersedes the unrelated Airbnb instructions in the parent directory.

## Scope and constraints
- Product is video-first autonomous warehouse return inspection; retain the image comparison tools.
- Current authorized scope: specification update and local video inspection vertical slice only.
- Phase numbering follows PLAN.md: Phase 2 evaluation, Phase 3 agent, Phase 4 UI/API, Phase 5 AWS/submission.
- Stop after video sampling/quality/keyframe artifacts and tests; do not begin another milestone without approval.
- OpenCV 5 must do substantive processing. Never substitute OpenCV 4.
- No authenticity, fraud-certainty, or calibrated physical-dimension claims.
- Heuristics and synthetic tests do not establish real-world performance.
- Never provision paid resources, publish endpoints, or incur AWS charges without explicit approval.
- Never commit credentials, personal images, environments, or generated artifacts.
- Prefer typed, small modules and deterministic pytest tests; no unnecessary frameworks.
- No MCP, graph database, or complex multi-agent framework without a demonstrated need.
- Target 5–10-second 1080p inspection videos; explicitly bound local file size, dimensions,
  decoding and retained samples. Never claim thumbnail diversity verifies physical viewpoint.

## Setup and verification (PowerShell)
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe scripts/audit_environment.py
.\.venv\Scripts\python.exe -m pytest -q
```
Python 3.13.2 and cv2 5.0.0 verified on Windows x64; other Python versions need verification.
Report actual tests, limitations, changed files, and a suggested commit for each milestone.

## Bounded engineering loop
1. Read PRODUCT_SPEC.md, PLAN.md, EVAL_SPEC.md and existing implementation/tests.
2. Select the smallest change addressing the assigned milestone's highest-impact failure.
3. Add/update meaningful tests, implement, and execute relevant tests/evaluation.
4. Diagnose failures; allow at most three repair attempts per failure, then stop and report.
5. Compare the same cases against the recorded baseline; retain changes only when required gates pass.
6. Review the diff, update PLAN.md and PROGRESS.md, and report verified outcomes.

Use Builder, Evaluator, Reviewer, and Planner as sequential roles in this session, not parallel agents.
Priority heuristic: expected impact × observed failure frequency / estimated effort.
Do not weaken thresholds or change labels to improve scores. Separate holdout from tuning data.
Preserve working behavior and ground every measurement/decision in executed tools.
Use a local Git checkpoint or isolated branch before risky changes. No automatic push, merge,
publication, deployment, secret access, or cloud spending. Do not start unattended runners.

Additional local checks:
```powershell
.\.venv\Scripts\python.exe scripts/evaluate.py
.\.venv\Scripts\python.exe scripts/quality_gate.py
```
The current gate verifies only the Phase 1 synthetic smoke contract; it is not full agent evaluation.
Completion reports include files changed, executed tests and actual results, baseline comparison
when applicable, risks, and recommended next task. Never claim CI ran remotely without evidence.
