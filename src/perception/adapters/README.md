# Perception adapters

The first implementation here must convert an Ultralytics result into the project-owned types:

```text
Ultralytics Result -> adapter -> PerceptionFrame
```

The adapter must copy only required scalar data (boxes, pose points, confidence, track IDs,
frame/timestamp metadata). Never return tensors, Ultralytics `Results`, ByteTrack objects, or
OpenCV frames as part of `PerceptionFrame`.
