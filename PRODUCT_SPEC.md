# ProofLens AI product specification

## Mission
Competition-ready, video-first autonomous warehouse return inspection using substantive OpenCV 5.
Current authorization: local video engine, synthetic evaluation, bounded resumable inspection agent
and integration. Previous image-comparison CLI remains supported. See APPROVAL_POLICY.md for stop points.

## User journeys
1. Supply a 5–10-second inspection video, initially targeting 1080p.
2. Safely validate locally, extract a configurable subset of frames using OpenCV 5.
3. Evaluate sharpness, exposure, possible glare and a viewpoint-diversity proxy.
4. Select three complementary high-quality keyframes; preserve original-resolution images.
5. Identify product using QR or manual catalog selection and retrieve the trusted reference record.
6. Align suitable keyframes with ORB/robust homography only when geometry supports it.
7. Inspect suspicious differences, annotate evidence, and let a bounded stateful agent choose
   another tool, targeted inspection, a new viewpoint request, or human review.
8. Produce an evidence-backed investigation report and full action trace; resume after follow-up evidence.

## Requirements and acceptance
- Verify actual cv2 major version 5; CPU-first, independent typed vision tools.
- Quality: Laplacian variance, exposure/glare heuristics, dimensions, recommendations.
- Alignment: interchangeable matcher, ORB, RANSAC, inlier and geometric checks, valid-overlap mask.
- Differences: lighting adjustment, threshold/morphology, contours, annotated artifacts and limitations.
- Phase 1: CLI accepts two images, saves JSON and overlay on successful alignment, returns
  structured failure otherwise; at least three executed passing tests.
- Future agent: bounded state machine, persistent observations and tool-selection reasons,
  retry/step limits, recapture/resume, human review; no fabricated tool output.
- Future verdicts: consistent with reference, suspected mismatch, insufficient evidence, human review required.
- Future interface/API: Streamlit, FastAPI, Pydantic; meaningful AWS image processing only with approval.
- Reproducible evaluation, installation, deployment instructions, report, and ≤5-minute demo.

## Non-goals
Authenticity proof, certain fraud detection, uncalibrated physical measurements, synthetic-only
real-world claims, GPU requirement, large agent frameworks, databases/microservices without need.
Advanced matching and Graviton/COOL wait until the baseline, agent, and AWS component work.
No paid deployment, public endpoint, push, merge, or secret access is authorized by this specification.

## Priorities
P0: safe video ingestion, configurable sampling, quality/diverse keyframes, QR/catalog lookup,
explicit alignment failure, difference overlays, bounded perception–decision–action loop,
FastAPI/Streamlit, reproducible evaluation and meaningful AWS processing.
P1: 100 deterministic synthetic cases, separate real-world validation, fixed-vs-adaptive agent
and keyframe-selection baselines, ALIKED + LightGlue feasibility investigation.
P2 only after core completion: verified COOL/Graviton with reproducible benchmarks and additional
defect-segmentation models. No MCP, graph database or complex multi-agent framework without need.

## Immediate video slice acceptance
Accept local MP4, validate size/metadata/decode limits, configurable deterministic sampling,
reuse quality metrics, balance quality and appearance diversity, retain native-resolution PNGs,
and write JSON with sampled indices/timestamps/metrics, selected frames, reasons, limitations and timing.
Select three when sufficient acceptable diverse frames exist; otherwise report explicit insufficiency
and preserve only available evidence. Do not duplicate frames to satisfy the count.
Test sampling, scoring, selection, invalid videos and edge cases; inspect generated images and report
measured processing time. Verify OpenCV 5 compatibility first. This slice is complete; latest user
authorization extends local development through evaluation, agent and integration, without cloud/publication.
