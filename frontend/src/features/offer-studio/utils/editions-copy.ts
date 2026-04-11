import { OfferArchetype } from "@/features/offer-studio/types";

/**
 * Wizard-facing copy for the "will this offer have editions?" question.
 * Spoken in the language of each archetype — cohortes / salidas / convocatorias.
 * Only archetypes that support editions have an entry.
 */
export interface EditionsCopy {
  readonly title: string;
  readonly description: string;
  readonly yesLabel: string;
  readonly noLabel: string;
  readonly helper: string;
}

const COPY: Partial<Record<OfferArchetype, EditionsCopy>> = {
  [OfferArchetype.PROGRAMA]: {
    title: "¿Se dictará en cohortes?",
    description:
      "Las cohortes son grupos de alumnos que empiezan y terminan juntos en fechas fijas.",
    yesLabel: "Sí, en cohortes con fechas fijas",
    noLabel: "No, es evergreen (cada alumno entra cuando quiere)",
    helper:
      "Podés cambiar esta decisión más tarde desde la sección de detalles del programa.",
  },
  [OfferArchetype.EXPERIENCIA]: {
    title: "¿Tendrá varias salidas en fechas distintas?",
    description:
      "Si vas a repetir esta experiencia en distintas fechas (ej: cada trimestre), elegí Sí.",
    yesLabel: "Sí, con múltiples salidas programadas",
    noLabel: "No, es una corrida única",
    helper:
      "Podés cambiar esta decisión más tarde desde la sección de detalles del evento.",
  },
  [OfferArchetype.SERVICIO]: {
    title: "¿Se ofrecerá en convocatorias?",
    description:
      "Las convocatorias agrupan clientes que empiezan al mismo tiempo en fechas fijas.",
    yesLabel: "Sí, con convocatorias agrupadas",
    noLabel: "No, cada cliente agenda su propia fecha",
    helper:
      "Podés cambiar esta decisión más tarde desde la sección de detalles del servicio.",
  },
};

/**
 * Returns copy for the editions wizard step, or null if the archetype doesn't
 * support editions (PRODUCTO, MEMBRESIA) — in which case the step is skipped.
 */
export function getEditionsCopy(archetype: OfferArchetype): EditionsCopy | null {
  return COPY[archetype] ?? null;
}

/**
 * Does this archetype support the "editions" concept at all? When false, the
 * wizard skips the question and the offer editor hides the Ediciones section.
 */
export function archetypeSupportsEditions(archetype: OfferArchetype): boolean {
  return getEditionsCopy(archetype) !== null;
}
