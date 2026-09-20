# Perception

Ownership: Developer A.

This module reads video/camera frames, runs YOLO26n-pose with ByteTrack, and emits
`contracts.PerceptionFrame`. It reports only observations; it never labels an interaction as a
fight or assault.

`adapters/ultralytics.py` copies pose tracking scalars from one Ultralytics result into a
`PerceptionFrame`. `live.py` owns live capture, YOLO visualization, and passes frames to an
injected `FeaturePipeline`; it does not calculate features.

Prepare everything from the repository root with:

```powershell
python scripts/setup.py
python scripts/run.py --source 0
```

Press `q` or Escape to close preview. Overlay shows FPS, active ByteTrack, detected persons, and
whether FeaturePipeline emitted a WorldState. Terminal prints only emitted WorldStates.
