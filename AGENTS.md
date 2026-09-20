# AGENTS.md

## Project mission

Build **Campus Sentinel - Deteccao Inteligente de Ocorrencias de Seguranca em Ambientes
Universitarios** for the SECOMP 2026 computer-vision hackathon.

The current MVP has one priority: detect observable evidence related to aggression/fights in
video, aggregate it over time, and let Jev make the contextual decision. Do not expand the MVP
to vandalism, robbery, databases, distributed infrastructure, or model training unless the user
explicitly asks.

These instructions apply to the whole repository.

## Read first

Before changing files:

1. Read `README.md`, this file, and the README in the module you own.
2. Inspect `git status`; preserve work already present.
3. Read `src/contracts/README.md` before consuming or changing a contract.
4. Keep facts, plans, and unverified assumptions distinct. Never invent results or evidence.

## Architecture and data flow

```text
video/camera
  -> YOLO26n-pose + ByteTrack
  -> PerceptionFrame
  -> TrackHistory / FeaturePipeline
  -> WorldState
  -> Jev DecisionEngine
  -> DecisionResult
  -> interface/dashboard
```

- `perception` converts frames into objective observations. It never decides that a fight exists.
- `features` performs deterministic temporal, geometric, and motion calculations. It owns track
  history and creates `WorldState`; it does not import Ultralytics types.
- `decision` sends the relevant `WorldState` evidence to Jev and maps the typed response to
  `DecisionResult`. Do not replace Jev with a large decision tree.
- `interface` consumes project contracts, never Ultralytics results or Jev SDK objects directly.
- `contracts` contains stable data structures and ports only; no business logic.

Perception may run for every frame. Features update continuously. Jev should run at a lower,
configurable cadence or when state changes materially; do not add complex scheduling yet.

## Ownership boundaries

### Perception agent

May normally modify:

```text
src/perception/**
tests/perception/**
docs specific to perception
```

May read:

```text
src/contracts/**
```

Do not modify without explicit user authorization:

```text
src/features/**
src/decision/**
tests/features/**
tests/decision/**
```

### Feature/Decision agent

May normally modify:

```text
src/features/**
src/decision/**
tests/features/**
tests/decision/**
docs specific to features/decision
```

May read:

```text
src/contracts/**
src/perception/**
```

Reading `src/perception/**` to understand existing behavior is allowed. Do not modify it without
explicit user authorization.

### Shared

```text
src/contracts/**
src/interface/**
tests/contracts/**
global configuration files
README.md and cross-cutting documentation
```

These are shared areas. Changes must be minimal, intentional, justified, and coordinated. Do not
perform global refactors while completing a module-local task.

## Shared contract rules

The stable boundaries are:

```text
PerceptionFrame -> FeaturePipeline
WorldState      -> DecisionEngine
DecisionResult  -> Interface
```

When a contract change is truly necessary:

1. prefer backward compatibility;
2. make the smallest possible change;
3. update its documentation and synthetic fixtures;
4. find and test every consumer;
5. do not use it as an excuse to refactor another developer's module;
6. communicate the change before merge.

Ultralytics/ByteTrack objects must be converted by an adapter under `src/perception/adapters/`.
Features must receive `PerceptionFrame`, not external SDK objects. Likewise, Jev SDK results must
be mapped inside `src/decision/jev/`; the interface receives only `DecisionResult`.

## Technology boundaries

- Python 3.11+ is the project language for contracts, perception, and feature extraction.
- Planned perception stack: Ultralytics YOLO26n-pose, ByteTrack, OpenCV, NumPy, and optionally
  Supervision.
- Jev/TypeSafe integration belongs only under `src/decision/jev/`. Verify the installed SDK API
  before coding; never expose `TYPESAFE_API_KEY` to a client or commit it.
- Keep third-party types and imports inside their owning adapter.

## Implementation conventions

- Prefer small modules and pure functions over shared mutable state.
- Use type hints. Public functions and contract fields need short, useful docstrings.
- Express distances relative to body/bounding-box scale when possible; document units and ranges.
- Treat missing keypoints and insufficient history as unknown data, not as zero or false evidence.
- Keep deterministic math in `features`; keep contextual judgment in Jev.
- Preserve timestamps, frame indices, source IDs, track IDs, and confidence where applicable.
- A Jev/API failure, insufficient evidence, and a normal event are different states.
- Do not derive an overall decision confidence by casually averaging SDK confidences.
- Never log secrets, raw personal data, or unnecessary identifiable imagery.

## Tests

- Perception tests must be runnable independently of features and decision when practical.
- Feature tests must use synthetic `PerceptionFrame` values and run without YOLO/model weights.
- Decision tests must use synthetic `WorldState` values and a mocked/injected Jev client; offline
  tests validate integration logic, not model accuracy.
- Contract changes require updates to `tests/contracts/` and `tests/fixtures/synthetic.py`.
- Before handoff, run `python -m pytest` and any module-specific checks documented by that module.

## Git collaboration

Use small branches such as:

```text
feature/perception-video-input
feature/perception-tracking
feature/features-motion
feature/decision-jev
```

Keep commits module-focused. Rebase/update before handoff, avoid drive-by formatting, and do not
mix shared-contract changes with unrelated implementation. The expected merge is normally one
Perception change plus one Feature/Decision change with shared files changed only when agreed.

## Do not do

- Do not add a fight verdict to perception or deterministic feature code.
- Do not pass Ultralytics results beyond perception or Jev responses beyond decision.
- Do not create microservices, queues, Kafka, Redis, or a database for the current MVP.
- Do not add VLM/Qwen/general LLMs to the main path.
- Do not train a new model unless explicitly requested.
- Do not create giant central files, speculative abstractions, or empty directory trees.
- Do not implement timers, dashboards, or a broad incident taxonomy before the fight MVP works.
- Do not commit videos, weights, datasets, generated outputs, secrets, or real `.env` files.

## Definition of done

A task is done when it respects ownership, consumes/produces the correct contract, has focused
tests, documents configuration or limitations, credits external resources when added, and does
not claim unverified behavior.
