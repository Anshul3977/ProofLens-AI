# Known limitations

- ORB/homography assumes a reasonably textured, largely planar scene and similar viewpoints.
  Nonplanar products, repeated patterns, occlusion, and weak texture can fail or align incorrectly.
- Blur, exposure, and glare values are heuristics. White surfaces can resemble glare; low texture
  can resemble blur. The current conservative quality gate stops on any recommended action.
- A well-supported homography is not proof that objects are identical.
- Grayscale differences can miss color-only changes. Morphology and minimum-area filtering can
  remove small genuine changes. Bounding boxes are candidate image regions only.
- Global lighting normalization can suppress global visual changes; local shadows and reflections
  can produce false regions. Residual registration error also produces apparent changes.
- No calibrated confidence score, damage size, authenticity finding, or fraud conclusion exists.
- Tests are synthetic only. No real-world performance, agentic improvement, or AWS compliance is claimed.
- Local CLI decodes whole files; it is not hardened for untrusted public uploads or concurrent workloads.
- Inputs are not copied to artifacts, but overlays contain image content. Keep personal images and outputs
  private. Generated artifacts, local environments, and private data are excluded from Git.
- ALIKED's Python symbol is present; models and inference have not been tested. `cv2.LightGlue` is absent;
  that symbol check does not establish whether another matching API exists. Advanced matching is deferred.

## Video slice
- Tested with self-created mp4v-encoded MP4s; arbitrary phone codecs/variable-frame-rate footage have
  not been validated. FPS/frame-count metadata can be unreliable; timestamps are index/FPS estimates.
- Local file/signature/metadata and frame/memory bounds are enforced; native decoder is not sandboxed
  or subject to a hard wall-clock limit. Public untrusted ingestion requires additional isolation.
- Grabs process intervening frames too; sampling limits scoring/retained frames, not all decode work.
- Diversity uses 160x90 luminance appearance differences. Motion, backgrounds, mirrors and orientation
  may appear diverse without revealing new product surfaces. Similar appearances can conceal useful angles.
- No learned models, QR/catalog retrieval, video-to-reference comparison or autonomous agent yet.
- Timing measurements include a small synthetic workload, not a real warehouse throughput benchmark.
