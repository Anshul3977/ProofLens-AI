# ProofLens AI milestone plan

The product is now video-first. The local video slice and specification update are authorized;
all subsequent major milestones require review. Existing image tools and gates remain intact.
This numbering supersedes the earlier phase numbering in docs/phase1-report.md.

| Milestone | Priority | Dependencies | Acceptance | Status |
|---|---|---|---|---|
| Phase 0: environment audit | P0 | Python and wheel availability | actual OpenCV 5 import and required APIs verified | Complete |
| Phase 1: comparison slice | P0 | Phase 0 | typed quality/alignment/differences, saved artifacts, ≥3 passing tests | Complete |
| Repository workflow setup | P0 | Phase 1 | five instruction files, executable smoke checks, local verification, CI definition | Complete locally; remote CI unverified |
| Phase 1 focused reliability review | P0 | User-requested review | rank three weaknesses, fix only highest, failing-before regression and passing gates | Complete; contour evidence fix only |
| Video inspection vertical slice | P0 | Verified OpenCV 5 video I/O | bounded MP4 sampling, quality/diverse three-frame selection, native PNGs/JSON, tests, visual review/timing | Complete locally; awaiting review |
| Phase 2: full evaluation and regression gates | P0 | User approval, Phase 1 | labeled development/holdout sets, baseline protocol, metrics, immutable case regression | Pending approval |
| Phase 3: inspection agent | P0 | User approval, Phase 2 | structured tools/trace, bounds, recapture/resume and all eight scenarios | Pending approval |
| Phase 4: UI/API | P1 | User approval, Phase 3 | usable Streamlit/FastAPI flow and integration tests | Pending approval |
| Phase 5: AWS/evaluation/submission | P0 | User approval, local verification, explicit cloud authorization | hosted processing proof, final holdout report, reproducibility, demo | Pending approval |
| Learned matching / COOL | P2 | Verified baseline, agent and AWS | documented compatible APIs and identical-workload benchmarks | Deferred |

Next task after video slice review: approve evaluation and QR/catalog/agent integration scope.
Prioritize observed failures using impact × failure frequency / effort; no speculative benchmark claims.

P1 backlog: source-grouped 100-case synthetic augmentations; separate real validation; fixed-vs-agent
and uniform/top-quality-vs-diverse keyframe comparisons; ALIKED/LightGlue feasibility.
P2: verified COOL on AWS Graviton and additional segmentation models only after core completion.
