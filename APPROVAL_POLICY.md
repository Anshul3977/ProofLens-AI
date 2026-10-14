# ProofLens approval policy

Authority: user's October 14, 2026 attached bounded autonomous parallel-development request.
Allowed: scoped local edits/tests/benchmarks, synthetic artifacts, defect repairs (at most three
attempts per failing task), feature branches/worktrees, verified local commits and integration
onto an isolated integration branch. Continue across the three approved local workstreams.

Approval required BEFORE: merge major workstreams into main; fundamental scope/architecture changes;
high-risk/untrusted dependencies; credentials/paid services; AWS infrastructure/deployment;
external pushes/publication; user data deletion, force push/history rewriting; disabling important gates/tests.
Silence is not approval. No such action is needed to complete the local milestone.

For a requested approval provide concrete action, necessity, verified evidence, risks, rollback,
and recommendation. Record explicit authorization in APPROVALS.md. Stop on repeated failures
(three repair attempts), missing required credentials, unexpected cost or unresolved security concern.
Local integrations are reviewable via commit history and diffs; do not merge to main automatically.
