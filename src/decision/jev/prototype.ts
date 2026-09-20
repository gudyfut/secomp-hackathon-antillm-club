import {
  TypeSafeClient,
  choice,
  type RequestOptions,
  type SystemOneRequest,
  type SystemOneResult,
} from "@typesafe-ai/sdk";

import type { PrototypeJevInput, PrototypeJevOutput } from "./types.js";

/**
 * Deliberately provisional options. Replace them when the MVP questions and policy are defined.
 * This question validates the API boundary; it is not a calibrated fight classifier.
 */
export const prototypeQuestions = {
  assessment: choice(
    "Considerando somente os sinais em `worldState`, qual opcao melhor descreve a evidencia " +
      "sobre uma interacao preocupante? Nao presuma valores para campos nulos e nao trate " +
      "ausencia de evidencia como uma interacao normal.",
    {
      no_clear_concern:
        "Os sinais disponiveis nao mostram evidencia clara de uma interacao preocupante.",
      concerning_interaction:
        "Os sinais disponiveis mostram evidencia de uma interacao que merece atencao.",
      insufficient_evidence:
        "Os sinais sao ausentes, incompletos ou ambiguos demais para esse julgamento.",
    },
  ),
} as const;

type PrototypeQuestions = typeof prototypeQuestions;
export type PrototypeRequest = SystemOneRequest<PrototypeQuestions>;
export type PrototypeResult = SystemOneResult<PrototypeQuestions>;

/** Narrow client surface that can be replaced by a deterministic fake in tests. */
export interface PrototypeJevClient {
  systemOne(
    request: PrototypeRequest,
    options?: RequestOptions,
  ): PromiseLike<PrototypeResult>;
}

export async function evaluatePrototypeWorldState(
  client: PrototypeJevClient,
  input: PrototypeJevInput,
  signal?: AbortSignal,
): Promise<PrototypeJevOutput> {
  const request: PrototypeRequest = {
    state: { worldState: input.worldState },
    questions: prototypeQuestions,
  };
  const options: RequestOptions | undefined = signal === undefined ? undefined : { signal };
  const result = await client.systemOne(request, options);
  const answer = result.answers.assessment;

  return {
    assessment: answer.choice,
    confidence: answer.confidence,
    probabilities: answer.probabilities,
    model: result.model,
    usage: {
      inputTokens: result.usage.input_tokens,
      outputTokens: result.usage.output_tokens,
    },
  };
}

/** Create the real server-side client; it reads TYPESAFE_API_KEY from the environment. */
export function createTypeSafeClient(): PrototypeJevClient {
  return new TypeSafeClient();
}
