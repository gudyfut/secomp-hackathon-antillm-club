# Feature extraction and WorldState

Ownership: Developer B.

This module consumes only `contracts.PerceptionFrame`, maintains bounded track history, computes
deterministic evidence, and emits `contracts.WorldState`. It must remain testable using
`tests/fixtures/synthetic.py` without YOLO, videos, or model weights.

Add small modules as features are implemented. Likely seams are history, geometry, motion,
interaction, and the coordinating extractor; do not create the whole tree in advance.

Distances should use body or bounding-box scale when possible. Every feature must document its
unit/range and its behavior when keypoints or history are insufficient.

## Implemented pipeline

`TemporalFeaturePipeline.update(frame)` absorbs every `PerceptionFrame`, keeps bounded histories
per temporary `track_id`, and emits `WorldState` at configurable cadence. It uses only frame
timestamps, never execution time. Bbox center is global movement reference. Torso-relative pose
coordinates remove global translation before wrist and body articulation measurements.

Initial engineering defaults in `FeatureConfig` are `0.5 s`, `2.0 s`, and `5.0 s` conceptual
windows; `5.0 s` retained history; `0.25 s` output cadence; `0.25` EMA alpha; and `0.35` minimum
keypoint confidence. These values require calibration against recorded camera data.

Contract fields use these units:

- `PersonFeatures.body_speed`: body-heights/second, smoothed bbox-center speed.
- `wrist_speed` and `wrist_acceleration`: torso-relative wrist articulation in
  body-heights/second and body-heights/second-squared.
- `motion_intensity`: torso-relative body articulation in body-heights/second.
- `distance_between_people`: bbox-center distance in body-heights.
- `wrist_to_head_distance` and `wrist_to_torso_distance`: image-space point distance in
  body-heights.
- `bbox_overlap`: visual bbox IoU in `[0, 1]`, not physical contact.

Missing history, invalid timing, degenerate boxes, insufficient torso points, or low-confidence
keypoints emit `None`; observed zero motion emits `0.0`.

## Contract gaps

Current immutable `WorldState` contracts cannot carry continuous body acceleration, local arm and
body motion separately, pose quality/coverage, distance rate, movement vector, or direction
similarity. `rapid_approach` is Boolean, but no calibrated threshold exists and this module must
not add one; it remains `None`. `possible_contact` and `repeated_aggressive_motion` also remain
`None`, because they require semantic interpretation. Minimal future contract addition: optional
continuous fields for these measurements, each documented with units. No contract changes were
made here.

## Limitations

Bbox normalization does not fully correct perspective. Two-dimensional distance is not physical
distance. Pose confidence can degrade under occlusion. Track IDs are temporary and can switch.
Local pose motion remains detector-noise sensitive. Different cameras need calibration. Pairwise
work is O(n-squared) for `n` active tracks.
