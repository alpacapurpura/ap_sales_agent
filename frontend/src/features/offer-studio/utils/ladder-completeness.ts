import { OfferValueLevel } from "../types";

import type { Offer } from "../types";

export interface LadderGap {
  /** Ladder rung with no offer yet. Callers resolve label/description
   *  via ``useValueLevelCatalog()`` — keeps this module catalog-agnostic
   *  and eliminates drift with backend copy. */
  group: OfferValueLevel;
  priority: "critico" | "recomendado" | "opcional";
  suggestedPresetIds: string[];
}

export interface LadderCompleteness {
  filledGroups: Set<OfferValueLevel>;
  totalGroups: number;
  percentage: number;
  gaps: LadderGap[];
  score: "vacia" | "iniciando" | "creciendo" | "completa" | "avanzada";
}

/** Priority + suggested starter formats per rung.
 *
 *  Priority is strategic logic (a ladder without LEAD_MAGNET is critical;
 *  without CORPORATIVO is optional) and stays local.
 *  ``suggestedPresetIds`` references format ids from ``FORMAT_CATALOG`` —
 *  the wizard uses them to propose first-click formats when filling a gap.
 *  If the suggested format is later removed from ``FORMAT_CATALOG``,
 *  the frontend renders the entries it can resolve and silently drops
 *  the rest. */
const GROUP_CONFIG: Record<
  OfferValueLevel,
  {
    priority: LadderGap["priority"];
    suggestedPresetIds: string[];
  }
> = {
  [OfferValueLevel.LEAD_MAGNET]: {
    priority: "critico",
    suggestedPresetIds: ["producto_ebook", "experiencia_summit"],
  },
  [OfferValueLevel.ACTIVACION]: {
    priority: "recomendado",
    suggestedPresetIds: ["producto_curso", "programa_masterclass", "membresia_comunidad"],
  },
  [OfferValueLevel.TRANSFORMACION]: {
    priority: "critico",
    suggestedPresetIds: ["programa_bootcamp", "programa_certificacion", "servicio_vip_day"],
  },
  [OfferValueLevel.MAXIMIZACION]: {
    priority: "opcional",
    suggestedPresetIds: ["servicio_mentoria", "membresia_mastermind", "experiencia_retiro"],
  },
  [OfferValueLevel.CORPORATIVO]: {
    priority: "opcional",
    suggestedPresetIds: ["servicio_dfy"],
  },
};

function computeScore(filledCount: number, total: number): LadderCompleteness["score"] {
  if (filledCount === 0) return "vacia";
  if (filledCount === 1) return "iniciando";
  if (filledCount < total - 1) return "creciendo";
  if (filledCount === total - 1) return "completa";
  return "avanzada";
}

export function computeLadderCompleteness(offers: Offer[]): LadderCompleteness {
  const allGroups = Object.values(OfferValueLevel);
  const totalGroups = allGroups.length;

  const filledGroups = new Set<OfferValueLevel>();
  for (const offer of offers) {
    if (offer.value_level && allGroups.includes(offer.value_level)) {
      filledGroups.add(offer.value_level);
    }
  }

  const gaps: LadderGap[] = [];
  for (const group of allGroups) {
    if (!filledGroups.has(group)) {
      const config = GROUP_CONFIG[group];
      gaps.push({
        group,
        priority: config.priority,
        suggestedPresetIds: config.suggestedPresetIds,
      });
    }
  }

  const priorityOrder = { critico: 0, recomendado: 1, opcional: 2 };
  gaps.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

  const percentage = Math.round((filledGroups.size / totalGroups) * 100);

  return {
    filledGroups,
    totalGroups,
    percentage,
    gaps,
    score: computeScore(filledGroups.size, totalGroups),
  };
}
