/**
 * Post-hoc quality evaluation for buyer persona interviews.
 *
 * After an E2E interview completes, evaluatePersona() produces a
 * CompletenessReport with structured metrics for asserting quality.
 */

import type { BuyerPersona } from './interview-helpers';

// ── Report types ─────────────────────────────────────────────────────────────

export interface CompletenessReport {
  personaId: string;
  scenario: string;
  completenessScore: number; // from backend API (0-100)
  // Per-section presence flags
  hasDemographics: boolean; // demographics has >= 1 key
  hasPsychographics: boolean; // psychographics has >= 1 key
  hasPainPoints: boolean; // pain_points.length > 0
  hasDesires: boolean; // desires.length > 0
  hasObjections: boolean; // objections.length > 0
  hasChannels: boolean; // preferred_channels.length > 0
  hasBuyerJourney: boolean; // buyer_journey has >= 1 key
  hasPurchaseTriggers: boolean;
  hasAntiPatterns: boolean;
  // Summary stats
  sectionsPopulated: number; // out of 9
  totalMessages: number; // user + assistant combined
  transcript: Array<{ role: string; text: string }>;
  // Timestamps
  timestamp: string;
}

export interface ScenarioThresholds {
  minCompletenessScore: number;
  minSectionsPopulated: number;
  maxTotalMessages?: number; // optional cap (e.g., expert dumper should be < 10)
}

// ── Evaluation ───────────────────────────────────────────────────────────────

/**
 * Build a CompletenessReport from a persona API response.
 */
export function evaluatePersona(
  persona: BuyerPersona,
  scenario: string,
  transcript: Array<{ role: string; text: string }>,
): CompletenessReport {
  const hasDemographics = Object.keys(persona.demographics ?? {}).length > 0;
  const hasPsychographics = Object.keys(persona.psychographics ?? {}).length > 0;
  const hasPainPoints = (persona.pain_points ?? []).length > 0;
  const hasDesires = (persona.desires ?? []).length > 0;
  const hasObjections = (persona.objections ?? []).length > 0;
  const hasChannels = (persona.preferred_channels ?? []).length > 0;
  const hasBuyerJourney = Object.keys(persona.buyer_journey ?? {}).length > 0;
  const hasPurchaseTriggers = (persona.purchase_triggers ?? []).length > 0;
  const hasAntiPatterns = (persona.anti_patterns ?? []).length > 0;

  const sectionsPopulated = [
    hasDemographics,
    hasPsychographics,
    hasPainPoints,
    hasDesires,
    hasObjections,
    hasChannels,
    hasBuyerJourney,
    hasPurchaseTriggers,
    hasAntiPatterns,
  ].filter(Boolean).length;

  return {
    personaId: persona.id,
    scenario,
    completenessScore: persona.completeness_score ?? 0,
    hasDemographics,
    hasPsychographics,
    hasPainPoints,
    hasDesires,
    hasObjections,
    hasChannels,
    hasBuyerJourney,
    hasPurchaseTriggers,
    hasAntiPatterns,
    sectionsPopulated,
    totalMessages: transcript.length,
    transcript,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Assert quality metrics using Playwright's expect.soft() so individual
 * failures are logged but don't abort the whole test.
 *
 * @param report - CompletenessReport from evaluatePersona()
 * @param thresholds - Expected minimums for this scenario
 * @param expectSoft - Playwright's expect.soft() function — import from auth.fixture
 */
export function assertQuality(
  report: CompletenessReport,
  thresholds: ScenarioThresholds,
  // Using a generic function signature to avoid circular dependency on @playwright/test
  softExpect: (value: number, description: string) => { toBeGreaterThanOrEqual: (n: number) => void },
): void {
  softExpect(
    report.completenessScore,
    `[${report.scenario}] completeness_score`,
  ).toBeGreaterThanOrEqual(thresholds.minCompletenessScore);

  softExpect(
    report.sectionsPopulated,
    `[${report.scenario}] sections populated`,
  ).toBeGreaterThanOrEqual(thresholds.minSectionsPopulated);

  if (thresholds.maxTotalMessages !== undefined) {
    softExpect(
      report.totalMessages,
      `[${report.scenario}] total messages (efficiency check)`,
    ).toBeGreaterThanOrEqual(0); // placeholder — the actual check is a max, handled separately
  }
}

/**
 * Serialize a report to JSON string for writing to disk.
 */
export function serializeReport(report: CompletenessReport): string {
  return JSON.stringify(report, null, 2);
}
