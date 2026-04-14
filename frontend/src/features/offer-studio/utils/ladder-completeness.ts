import { Offer, OfferValueLevel } from "../types";

export interface LadderGap {
  group: OfferValueLevel;
  label: string;
  description: string;
  suggestedPresetIds: string[];
  priority: "critico" | "recomendado" | "opcional";
}

export interface LadderCompleteness {
  filledGroups: Set<OfferValueLevel>;
  totalGroups: number;
  percentage: number;
  gaps: LadderGap[];
  score: "vacia" | "iniciando" | "creciendo" | "completa" | "avanzada";
}

const GROUP_CONFIG: Record<
  OfferValueLevel,
  {
    label: string;
    description: string;
    priority: LadderGap["priority"];
    suggestedPresetIds: string[];
  }
> = {
  [OfferValueLevel.LEAD_MAGNET]: {
    label: "Lead Magnet",
    description: "Necesitas un recurso gratuito para atraer prospectos.",
    priority: "critico",
    suggestedPresetIds: ["producto_ebook", "experiencia_summit"],
  },
  [OfferValueLevel.ACTIVACION]: {
    label: "Activacion",
    description: "Convierte leads en clientes con una primera compra de bajo riesgo.",
    priority: "recomendado",
    suggestedPresetIds: ["producto_curso", "programa_masterclass", "membresia_comunidad"],
  },
  [OfferValueLevel.TRANSFORMACION]: {
    label: "Transformacion",
    description: "Tu oferta principal — la que genera la mayor parte de tus ingresos.",
    priority: "critico",
    suggestedPresetIds: ["programa_bootcamp", "programa_certificacion", "servicio_vip_day"],
  },
  [OfferValueLevel.MAXIMIZACION]: {
    label: "Maximizacion",
    description: "Ofertas premium para maximizar el valor de vida del cliente.",
    priority: "opcional",
    suggestedPresetIds: ["servicio_mentoria", "membresia_mastermind", "experiencia_retiro"],
  },
  [OfferValueLevel.CORPORATIVO]: {
    label: "Corporativo",
    description: "Servicios B2B para empresas y organizaciones.",
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
        label: config.label,
        description: config.description,
        suggestedPresetIds: config.suggestedPresetIds,
        priority: config.priority,
      });
    }
  }

  // Sort gaps: critico first, then recomendado, then opcional
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
