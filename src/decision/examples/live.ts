import { TypeSafeClient, type Fetch } from "@typesafe-ai/sdk";

import { evaluatePrototypeWorldState } from "../jev/index.js";
import type { PrototypeJevInput } from "../jev/index.js";

function printJson(label: string, value: unknown): void {
  console.log(`\n=== ${label} ===`);
  console.log(JSON.stringify(value, null, 2));
}

function parseJsonForLog(text: string): unknown {
  try {
    const parsed: unknown = JSON.parse(text);
    return parsed;
  } catch {
    return text;
  }
}

/**
 * Logs only URL, method and bodies. Request headers are intentionally omitted so the API key
 * can never appear in this diagnostic output.
 */
function createInspectableFetch(): Fetch {
  let attempt = 0;

  return async (url, init) => {
    attempt += 1;
    const requestBody = typeof init?.body === "string"
      ? parseJsonForLog(init.body)
      : "<body ausente ou nao textual>";

    printJson(`HTTP REQUEST ${attempt} - JSON REALMENTE ENVIADO`, {
      url,
      method: init?.method ?? "GET",
      body: requestBody,
    });

    const response = await globalThis.fetch(url, init);
    const rawResponseBody = await response.clone().text();

    printJson(`HTTP RESPONSE ${attempt} - JSON BRUTO RECEBIDO`, {
      status: response.status,
      body: parseJsonForLog(rawResponseBody),
    });

    return response;
  };
}

const input: PrototypeJevInput = {
  worldState: {
    source_id: "synthetic-live-example",
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

if (!process.env.TYPESAFE_API_KEY?.trim()) {
  throw new Error("TYPESAFE_API_KEY ausente. Configure o arquivo .env na raiz do repositorio.");
}

printJson("INPUT DO EXEMPLO ANTES DO SDK", input);

const client = new TypeSafeClient({
  fetch: createInspectableFetch(),
  logLevel: "off",
});
const output = await evaluatePrototypeWorldState(client, input);

printJson("OUTPUT MAPEADO PELO NOSSO ADAPTER", output);
