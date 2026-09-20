import type { JsonValue } from "@typesafe-ai/sdk";

/** JSON-safe input owned by the provisional Jev adapter. */
export interface PersonFeaturesInput {
  readonly [key: string]: JsonValue;
  readonly track_id: number;
  readonly body_speed: number | null;
  readonly wrist_speed: number | null;
  readonly wrist_acceleration: number | null;
  readonly motion_intensity: number | null;
  readonly person_fallen: boolean | null;
}

export interface InteractionFeaturesInput {
  readonly [key: string]: JsonValue;
  readonly first_track_id: number;
  readonly second_track_id: number;
  readonly distance_between_people: number | null;
  readonly rapid_approach: boolean | null;
  readonly wrist_to_head_distance: number | null;
  readonly wrist_to_torso_distance: number | null;
  readonly bbox_overlap: number | null;
  readonly possible_contact: boolean | null;
  readonly interaction_duration_ms: number | null;
  readonly repeated_aggressive_motion: boolean | null;
}

export interface PrototypeWorldStateInput {
  readonly [key: string]: JsonValue;
  readonly source_id: string;
  readonly observed_at_ms: number;
  readonly window_start_ms: number;
  readonly window_end_ms: number;
  readonly people: PersonFeaturesInput[];
  readonly interactions: InteractionFeaturesInput[];
}

export interface PrototypeJevInput {
  readonly [key: string]: JsonValue;
  readonly worldState: PrototypeWorldStateInput;
}

export type PrototypeAssessment =
  | "no_clear_concern"
  | "concerning_interaction"
  | "insufficient_evidence";

export interface PrototypeJevOutput {
  readonly assessment: PrototypeAssessment;
  readonly confidence: number;
  readonly probabilities: Readonly<Record<PrototypeAssessment, number>>;
  readonly model: string;
  readonly usage: {
    readonly inputTokens: number;
    readonly outputTokens: number;
  };
}
