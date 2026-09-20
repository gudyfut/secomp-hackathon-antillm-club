# Jev decision layer

Ownership: Developer B.

This module receives `contracts.WorldState`, asks Jev for typed contextual judgments, and maps the
result to `contracts.DecisionResult`. The interface must never receive SDK-specific objects.

The official SDK currently targets JavaScript/TypeScript and uses `TYPESAFE_API_KEY`. Keep the
runtime-specific client and mapping isolated under a future `jev/` module; choose the smallest
local integration only when implementing it. Do not introduce a microservice merely to preserve
folder symmetry.

Deterministic calculations stay in `features`. Decision policy may combine typed Jev judgments,
but must distinguish insufficient evidence, low confidence, and API failure. Do not replace Jev
with a large `if/else` classifier and do not claim model accuracy without labeled evaluation.
