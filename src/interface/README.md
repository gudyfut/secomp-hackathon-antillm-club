# Interface

Shared area; not a current MVP priority.

The future dashboard may render video overlays, track IDs, current state, event, severity,
urgency, action, and history. It should consume `PerceptionFrame`, `WorldState`, and
`DecisionResult` only. It must not import Ultralytics or Jev SDK types.
