/**
 * Utilities for automation health scoring, drop-off computation,
 * step diagnosis, and best/attention step detection.
 *
 * Pure functions — no React dependencies. Fully testable in isolation.
 */

import type { EmailAutomation, AutomationStep } from "../types/mail-types";

/**
 * Clamp a value to [0, 100].
 */
function clamp100(value: number): number {
  return Math.max(0, Math.min(100, value));
}

/**
 * Normalize a value to a 0-100 scale given a reference maximum.
 * Values >= refMax map to 100; negatives clamp to 0.
 */
function normalize(value: number, refMax: number): number {
  if (refMax <= 0) return 0;
  return clamp100((value / refMax) * 100);
}

/**
 * Compute composite health score 0-100 for an automation.
 *
 * Weights:
 *   0.30 × open_rate (ref max 100%)
 *   0.25 × click_rate (ref max 30%)
 *   0.20 × CTOR (ref max 50%)
 *   0.15 × completion_rate (ref max 100%)
 *   −0.10 × unsub_rate (ref max 5%)
 *
 * Returns 0 if the automation has no emails sent (no data yet).
 */
export function computeHealthScore(auto: EmailAutomation): number {
  if (auto.emailsSent === 0) return 0;

  const unsubRate = auto.emailsSent > 0 ? (auto.unsubscribes / auto.emailsSent) * 100 : 0;

  const score =
    0.3 * normalize(auto.openRate, 100) +
    0.25 * normalize(auto.clickRate, 30) +
    0.2 * normalize(auto.clickToOpenRate, 50) +
    0.15 * normalize(auto.completionRate, 100) -
    0.1 * normalize(unsubRate, 5);

  return Math.round(clamp100(score));
}

/**
 * Compute drop-off percentage between two consecutive steps.
 */
export function computeDropoff(previousSent: number, currentSent: number): number {
  if (previousSent <= 0) return 0;
  const dropoff = (1 - currentSent / previousSent) * 100;
  return Math.round(clamp100(dropoff));
}

/**
 * Generate actionable insights for an individual email step.
 *
 * Rules (deterministic, no LLM):
 *  - High open + low click → weak CTA
 *  - Low open → subject/timing issue
 *  - High unsub → content mismatch
 *  - Steep drop vs previous → sequence fatigue
 */
export function diagnoseStep(step: AutomationStep, previousStep?: AutomationStep): string[] {
  const insights: string[] = [];
  if (step.type !== "email") return insights;

  if (step.openRate > 50 && step.clickRate < 2) {
    insights.push(
      "Subject line efectivo pero CTA débil — prueba un botón más visible o copy más directo",
    );
  }

  if (step.openRate < 25 && step.emailsSent > 0) {
    insights.push(
      "Apertura baja — prueba un subject más específico, personalizado o cambia el horario de envío",
    );
  }

  const unsubRate = step.emailsSent > 0 ? (step.unsubscribes / step.emailsSent) * 100 : 0;
  if (unsubRate > 5 || step.unsubscribes > 3) {
    insights.push(
      "Desuscripciones altas — el contenido no cumple la expectativa del suscriptor; revisa frecuencia y relevancia",
    );
  }

  if (
    previousStep?.type === "email" &&
    previousStep.openRate > 0 &&
    step.openRate < previousStep.openRate * 0.6
  ) {
    const dropPct = Math.round((1 - step.openRate / previousStep.openRate) * 100);
    insights.push(
      `Caída de ${dropPct}% en apertura vs email anterior — posible fatiga de secuencia o timing inadecuado`,
    );
  }

  return insights;
}

/**
 * Score a step for best/worst ranking.
 * Uses open × click product as a proxy for engagement quality.
 */
function scoreStep(step: AutomationStep): number {
  if (step.type !== "email") return -1;
  return step.openRate * step.clickRate;
}

/**
 * Find the best-performing email step in a sequence.
 * Returns null if the sequence has no email steps.
 */
export function findBestStep(steps: AutomationStep[]): AutomationStep | null {
  const emailSteps = steps.filter((s) => s.type === "email");
  if (emailSteps.length === 0) return null;

  let best = emailSteps[0];
  let bestScore = scoreStep(best);
  for (const step of emailSteps.slice(1)) {
    const score = scoreStep(step);
    if (score > bestScore) {
      best = step;
      bestScore = score;
    }
  }
  return best;
}

/**
 * Find the email step that needs attention (worst performer).
 * Criteria: 0% click rate OR open rate < 20%. Returns null if all steps
 * are performing acceptably.
 */
export function findAttentionStep(steps: AutomationStep[]): AutomationStep | null {
  const emailSteps = steps.filter((s) => s.type === "email");
  const problems = emailSteps.filter((s) => s.clickRate === 0 || s.openRate < 20);
  if (problems.length === 0) return null;

  let worst = problems[0];
  let worstScore = scoreStep(worst);
  for (const step of problems.slice(1)) {
    const score = scoreStep(step);
    if (score < worstScore) {
      worst = step;
      worstScore = score;
    }
  }
  return worst;
}
