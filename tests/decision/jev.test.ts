import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  evaluatePrototypeWorldState,
  type PrototypeJevClient,
  type PrototypeJevInput,
  type PrototypeRequest,
  type PrototypeResult,
} from "../../src/decision/jev/index.js";

const input: PrototypeJevInput = {
  worldState: {
    source_id: "synthetic-test",
    observed_at_ms: 1_000,
    window_start_ms: 0,
    window_end_ms: 1_000,
    people: [
      {
        track_id: 1,
        body_speed: 1.2,
        wrist_speed: 2.1,
        wrist_acceleration: 1.4,
        motion_intensity: 0.8,
        person_fallen: false,
      },
      {
        track_id: 2,
        body_speed: 0.8,
        wrist_speed: 1.5,
        wrist_acceleration: 0.7,
        motion_intensity: 0.6,
        person_fallen: false,
      },
    ],
    interactions: [
      {
        first_track_id: 1,
        second_track_id: 2,
        distance_between_people: 0.45,
        rapid_approach: true,
        wrist_to_head_distance: 0.3,
        wrist_to_torso_distance: 0.25,
        bbox_overlap: 0.2,
        possible_contact: true,
        interaction_duration_ms: 800,
        repeated_aggressive_motion: null,
      },
    ],
  },
};

const simulatedApiResult: PrototypeResult = {
  model: "jev-test-double",
  answers: {
    assessment: {
      type: "choice",
      choice: "concerning_interaction",
      confidence: 0.82,
      probabilities: {
        no_clear_concern: 0.08,
        concerning_interaction: 0.82,
        insufficient_evidence: 0.1,
      },
    },
  },
  usage: { input_tokens: 25, output_tokens: 4 },
};

const expectedOutput = {
  assessment: "concerning_interaction",
  confidence: 0.82,
  probabilities: {
    no_clear_concern: 0.08,
    concerning_interaction: 0.82,
    insufficient_evidence: 0.1,
  },
  model: "jev-test-double",
  usage: { inputTokens: 25, outputTokens: 4 },
} as const;

function printStep(label: string, value: unknown): void {
  console.log(`\n--- ${label} ---`);
  console.log(typeof value === "string" ? value : JSON.stringify(value, null, 2));
}

class FakeJevClient implements PrototypeJevClient {
  public lastRequest: PrototypeRequest | undefined;

  systemOne(
    request: PrototypeRequest,
  ): PromiseLike<PrototypeResult> {
    this.lastRequest = request;
    return Promise.resolve(simulatedApiResult);
  }
}

describe("Adaptador Jev prototipo", () => {
  it("mostra a entrada, a resposta simulada e a saida esperada", async () => {
    const client = new FakeJevClient();

    printStep("CENARIO", "Dois tracks proximos, aproximacao rapida e possivel contato.");
    printStep("ENTRADA ENVIADA AO ADAPTER", input);
    printStep("RESPOSTA SIMULADA DA API JEV", simulatedApiResult);

    const output = await evaluatePrototypeWorldState(client, input);

    printStep("SAIDA PRODUZIDA PELO ADAPTER", output);
    printStep("SAIDA ESPERADA PELO TESTE", expectedOutput);

    assert.deepEqual(output, expectedOutput);
    assert.deepEqual(client.lastRequest?.state, { worldState: input.worldState });
    printStep("RESULTADO", "PASSOU: a entrada e a resposta foram mapeadas corretamente.");
  });

  it("diferencia falha da API de um evento normal", async () => {
    const client: PrototypeJevClient = {
      systemOne: () => Promise.reject(new Error("simulated API failure")),
    };

    printStep("CENARIO", "A API falha durante a avaliacao do mesmo WorldState sintetico.");
    printStep("ENTRADA", input);
    printStep("ERRO SIMULADO", "simulated API failure");
    printStep(
      "COMPORTAMENTO ESPERADO",
      "O erro deve ser propagado. Ele nao pode virar NORMAL nem no_clear_concern.",
    );

    await assert.rejects(
      evaluatePrototypeWorldState(client, input),
      /simulated API failure/,
    );
    printStep("RESULTADO", "PASSOU: a falha permaneceu distinta de uma decisao normal.");
  });
});
