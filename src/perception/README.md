# Perception

Ownership: Developer A.

This module will read video/camera frames, run YOLO26n-pose with ByteTrack, and emit
`contracts.PerceptionFrame`. It reports only observations; it never labels an interaction as a
fight or assault.

Suggested modules should be added only when implemented: `video`, `detectors`, `tracking`, and
technical visualization. Third-party results must cross the adapter documented in `adapters/`.
