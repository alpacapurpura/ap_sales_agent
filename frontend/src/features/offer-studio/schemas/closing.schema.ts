import { GuaranteeType } from "../types";

import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Closing — guarantee copy + last-push levers the SDR uses to move a
 * hesitating lead. Every lever here is consistent across editions
 * (a per-launch urgency timer lives on the ``LaunchEdition`` side).
 */
export const offerClosingSchema: SectionSchema = {
  key: "offer.closing",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "guarantee_type",
      label: "Tipo de garantía",
      type: "enum",
      path: "guarantee_type",
      options: [
        { value: GuaranteeType.NONE, label: "Sin garantía explícita" },
        { value: GuaranteeType.UNCONDITIONAL_30_DAY, label: "Incondicional 30 días" },
        { value: GuaranteeType.CONDITIONAL_ACTION_BASED, label: "Condicional por acción" },
        { value: GuaranteeType.DOUBLE_MONEY_BACK, label: "Doble devolución" },
        { value: GuaranteeType.SATISFACTION_OR_FREE_WORK, label: "Satisfacción o trabajo gratis" },
      ],
    },
    {
      id: "guarantee_terms",
      label: "Términos de la garantía",
      type: "textarea",
      path: "guarantee_terms",
      rows: 4,
      hint: "Copia textual que aparece en landing + checkout + contrato.",
    },
    {
      id: "urgency_drivers",
      label: "Disparadores de urgencia",
      type: "textarea",
      path: "urgency_drivers",
      rows: 3,
      hint: "Motivos reales para actuar ahora (cupos limitados, bonus, cierre de inscripción).",
    },
    {
      id: "final_push_copy",
      label: "Último empujón",
      type: "textarea",
      path: "final_push_copy",
      rows: 3,
      hint: "Frase que el SDR usa cuando la lead está a un paso de decidir.",
    },
  ],
};
