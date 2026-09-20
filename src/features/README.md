# Feature extraction and WorldState

Ownership: Developer B.

This module consumes only `contracts.PerceptionFrame`, maintains bounded track history, computes
deterministic evidence, and emits `contracts.WorldState`. It must remain testable using
`tests/fixtures/synthetic.py` without YOLO, videos, or model weights.

Add small modules as features are implemented. Likely seams are history, geometry, motion,
interaction, and the coordinating extractor; do not create the whole tree in advance.

Distances should use body or bounding-box scale when possible. Every feature must document its
unit/range and its behavior when keypoints or history are insufficient.
