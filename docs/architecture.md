# Phase 1 architecture

```text
CLI image paths
  -> OpenCV decode -> OpenCV 5 runtime guard
  -> typed quality reports for both images
     -> invalid/quality issue: structured JSON
     -> quality acceptable: ORB matcher -> RANSAC homography
        -> weak support/geometrically implausible/low overlap: structured failure
        -> warp inspection into reference frame + eroded valid-overlap mask
           -> median grayscale lighting-offset correction
           -> threshold -> morphology -> candidate contours
           -> local JSON, overlay, aligned image, and masks
```

`Matcher` is a protocol for interchangeable correspondences; only ORB is implemented.
RANSAC inliers, spatial coverage, quadrilateral geometry, horizon and overlap are checked.
Difference analysis only sees valid overlap. A global median offset accounts for simple additive
lighting shifts; it cannot correct local illumination or all exposure changes.

There is no Phase 2 state machine, persisted investigation history, QR catalog resolution,
targeted inspection, final verdict, API, UI, or cloud deployment yet.

## Video-first local slice

`python -m prooflens.video_cli` -> local MP4 path/file/header checks -> OpenCV FFmpeg metadata
and resource bounds -> sequential bounded `grab` with `retrieve` for evenly sampled indices
-> original-resolution quality metrics and normalized scores -> 160x90 RMS appearance distances
-> greedy quality/diversity selection -> up to three native PNGs and JSON report.
Quality eligibility uses the existing quality recommendations. The best eligible quality score is
selected first; subsequent frames maximize `(1-weight)*quality + weight*minimum_distance`, with
distance above the configured threshold to every prior selection. Stable frame-index tie breaking.
No physical-viewpoint verification or video-reference investigation is implemented yet.
