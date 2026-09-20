# Jev decision layer

Ownership: Developer B.

This module receives `contracts.WorldState`, asks Jev for typed contextual judgments, and will map
the result to `contracts.DecisionResult`. The interface must never receive SDK-specific objects.

The official SDK targets JavaScript/TypeScript and uses `TYPESAFE_API_KEY`. The runtime-specific
client and mapping are isolated under `jev/`; no service or database is introduced.

Deterministic calculations stay in `features`. Decision policy may combine typed Jev judgments,
but must distinguish insufficient evidence, low confidence, and API failure. Do not replace Jev
with a large `if/else` classifier and do not claim model accuracy without labeled evaluation.

## Current prototype

`jev/prototype.ts` provides one deliberately provisional `choice` question and a narrow client
interface that can be replaced by a deterministic fake. Its output is `PrototypeJevOutput`, not
the final `DecisionResult`; event, severity, urgency, action, question types, cadence, and policy
remain intentionally undecided.

Input fields use `null` for missing evidence. The adapter sends only the provided `worldState` and
does not infer absent values.

## Commands

From `src/decision`:

```powershell
npm install
npm test
npm run typecheck
npm run example:live
```

- `npm test` is fully offline and does not use the API key.
- `npm run example:live` loads the repository root `.env`, sends one synthetic state to the real
  API, and prints: input antes do SDK, body HTTP realmente enviado, body bruto recebido e output
  mapeado. Headers nunca sao impressos, portanto a chave nao aparece no log.

O SDK retorna `input_tokens` e `output_tokens` como telemetria. A precificacao publica atual do
Jev cobra tokens de entrada e informa output gratuito; a presenca de `output_tokens` em `usage`
nao significa, por si so, cobranca por esses tokens.

The live example proves connectivity and the adapter shape; it does not measure fight-detection
accuracy or define the final MVP policy.
