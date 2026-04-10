/**
 * Campaign health scoring and deterministic diagnosis.
 *
 * Campaigns are single-email sends (no sequence), so scoring weights
 * differ from automations: no completion_rate, but bounces are penalized.
 */

import type { EmailCampaign } from '../types/mail-types';

function clamp100(value: number): number {
  return Math.max(0, Math.min(100, value));
}

function normalize(value: number, refMax: number): number {
  if (refMax <= 0) return 0;
  return clamp100((value / refMax) * 100);
}

/**
 * Compute composite health score 0-100 for a single campaign.
 *
 * Weights (with benchmark reference maxima calibrated to email industry):
 *   0.35 × open_rate (ref max 60% — 50%+ is already excellent)
 *   0.30 × click_rate (ref max 15% — 10%+ is elite)
 *   0.25 × CTOR (ref max 25% — 15%+ is great)
 *   −0.10 × unsub_rate (ref max 5%)
 *   −0.10 × bounce_rate (ref max 10%)
 *
 * Returns 0 when the campaign has no emails sent.
 */
export function computeCampaignHealthScore(campaign: EmailCampaign): number {
  if (campaign.emailsSent === 0) return 0;

  const unsubRate =
    campaign.emailsSent > 0
      ? (campaign.unsubscribes / campaign.emailsSent) * 100
      : 0;

  const score =
    0.35 * normalize(campaign.openRate, 60) +
    0.3 * normalize(campaign.clickRate, 15) +
    0.25 * normalize(campaign.clickToOpenRate, 25) -
    0.1 * normalize(unsubRate, 5) -
    0.1 * normalize(campaign.bounceRate, 10);

  return Math.round(clamp100(score));
}

/**
 * Generate actionable insights for a single campaign.
 *
 * Rules (deterministic, no LLM):
 *  - High open + low click → weak CTA
 *  - Low open → subject or timing issue
 *  - High unsub rate → content mismatch
 *  - High bounce rate → list hygiene issue
 */
export function diagnoseCampaign(campaign: EmailCampaign): string[] {
  const insights: string[] = [];

  if (campaign.openRate > 50 && campaign.clickRate < 2) {
    insights.push(
      'Subject line efectivo pero CTA débil — el email abre bien pero no genera acción. Prueba un botón más visible o copy más directo.',
    );
  }

  if (campaign.openRate < 18 && campaign.emailsSent > 0) {
    insights.push(
      'Apertura baja — el subject no engancha. Prueba personalizar, añadir urgencia o cambiar el horario de envío.',
    );
  }

  const unsubRate =
    campaign.emailsSent > 0
      ? (campaign.unsubscribes / campaign.emailsSent) * 100
      : 0;
  if (unsubRate > 1 || campaign.unsubscribes > 10) {
    insights.push(
      'Desuscripciones elevadas — el contenido no cumple la expectativa del suscriptor. Revisa segmentación y frecuencia de envío.',
    );
  }

  if (campaign.bounceRate > 5) {
    insights.push(
      'Bounce rate alto — hay muchas direcciones inválidas en la lista. Limpia la lista antes de seguir enviando o tu dominio perderá reputación.',
    );
  } else if (campaign.bounceRate > 2) {
    insights.push(
      'Bounce rate elevado — empieza a monitorear la calidad de la lista y considera una limpieza preventiva.',
    );
  }

  return insights;
}
