# ProofLens AI milestone plan

Latest attached authorization allows autonomous local video/evaluation/agent integration workstreams.
Preserve existing image tools/gates. Approval checkpoints: APPROVAL_POLICY.md.
This numbering supersedes the earlier phase numbering in docs/phase1-report.md.

| Milestone | Priority | Dependencies | Acceptance | Status |
|---|---|---|---|---|
| Phase 0: environment audit | P0 | Python and wheel availability | actual OpenCV 5 import and required APIs verified | Complete |
| Phase 1: comparison slice | P0 | Phase 0 | typed quality/alignment/differences, saved artifacts, ≥3 passing tests | Complete |
| Repository workflow setup | P0 | Phase 1 | five instruction files, executable smoke checks, local verification, CI definition | Complete locally; remote CI unverified |
| Phase 1 focused reliability review | P0 | User-requested review | rank three weaknesses, fix only highest, failing-before regression and passing gates | Complete; contour evidence fix only |
| Video inspection vertical slice | P0 | Verified OpenCV 5 video I/O | bounded MP4 sampling, quality/diverse three-frame selection, native PNGs/JSON, tests, visual review/timing | Complete locally; awaiting review |
| Phase 2: synthetic evaluation and regression gates | P0 | Approved local scope | 100 reproducible source-grouped cases, development/default and protected holdout, actual baseline/failure records | In progress (worker B) |
| Phase 3: inspection agent | P0 | Approved local scope | typed bounded persistence/tools/trace, recapture/resume and behavior tests | In progress (worker C) |
| Video engine review/integration | P0 | Approved local scope | preserve validated slice, focused regressions, intelligent selection | In progress (worker A) |
| Local end-to-end integration | P0 | Three workstreams | QR/manual reference, video/agent integration, complete gate and measured comparisons | In progress (lead) |
| Phase 4: UI/API | P1 | User approval, Phase 3 | usable Streamlit/FastAPI flow and integration tests | Pending approval |
| Phase 5: AWS/evaluation/submission | P0 | User approval, local verification, explicit cloud authorization | hosted processing proof, final holdout report, reproducibility, demo | Pending approval |
| Learned matching / COOL | P2 | Verified baseline, agent and AWS | documented compatible APIs and identical-workload benchmarks | Deferred |

Next task after video slice review: approve evaluation and QR/catalog/agent integration scope.
Prioritize observed failures using impact × failure frequency / effort; no speculative benchmark claims.

P1 backlog: source-grouped 100-case synthetic augmentations; separate real validation; fixed-vs-agent
and uniform/top-quality-vs-diverse keyframe comparisons; ALIKED/LightGlue feasibility.
P2: verified COOL on AWS Graviton and additional segmentation models only after core completion.
