export interface PersonalityDimensions {
  energy: number;
  warmth: number;
  humor: number;
  expressiveness: number;
  narrative: number;
  verbosity: number;
}

export interface LinguisticPatterns {
  emoji_style: string;
  favorite_emojis: string[];
  greeting: string;
  farewell: string;
  filler_phrases: string[];
  avg_message_length: string;
  punctuation_style: string;
  humor_type: string;
  unique_vocabulary: string[];
}

export interface SampleExchange {
  context: string;
  other_message: string;
  author_response: string;
}

export interface PresetSummary {
  key: string;
  name: string;
  icon: string;
  description: string;
  sample_message: string;
  dimensions: PersonalityDimensions;
}

export interface PersonalityProfile {
  id: string;
  name: string;
  profile_type: "preset" | "cloned" | "interview" | "manual";
  preset_key: string | null;
  is_active: boolean;
  dimensions: PersonalityDimensions;
  linguistic_patterns: LinguisticPatterns;
  sample_exchanges: SampleExchange[];
  negative_constraints: string[];
  system_instruction: string | null;
  source_metadata: Record<string, unknown>;
  anchor_count: number;
  created_at: string;
  updated_at: string;
}

export interface SimulationResponse {
  responses: Array<{
    context: string;
    prospect_message: string;
    agent_response: string;
  }>;
}

export const DIMENSION_LABELS: Record<
  keyof PersonalityDimensions,
  { label: string; low: string; high: string }
> = {
  energy: { label: "Energía", low: "Calma", high: "Eléctrica" },
  warmth: { label: "Calidez", low: "Distante", high: "Íntima" },
  humor: { label: "Humor", low: "Serio", high: "Cómico" },
  expressiveness: { label: "Expresividad", low: "Minimalista", high: "Maximalista" },
  narrative: { label: "Narrativa", low: "Factual", high: "Cinematográfica" },
  verbosity: { label: "Verbosidad", low: "Telegráfico", high: "Elaborado" },
};

export const DIMENSION_LEVEL_NAMES: Record<string, string[]> = {
  energy: ["Muy baja", "Baja", "Media", "Alta", "Eléctrica"],
  warmth: ["Distante", "Cordial", "Amable", "Cercana", "Íntima"],
  humor: ["Serio", "Sutil", "Natural", "Juguetón", "Cómico"],
  expressiveness: ["Minimalista", "Sobria", "Equilibrada", "Expresiva", "Maximalista"],
  narrative: ["Factual", "Analítica", "Balanceada", "Narrativa", "Cinematográfica"],
  verbosity: ["Telegráfico", "Conciso", "Moderado", "Detallado", "Elaborado"],
};

export function getDimensionLevelName(
  dimension: keyof PersonalityDimensions,
  value: number,
): string {
  const levels = DIMENSION_LEVEL_NAMES[dimension];
  const index = Math.min(Math.floor(value * 5), 4);
  return levels[index];
}
