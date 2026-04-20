import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * StoryBrand 7-step narrative. Each StoryBrand step lives at its own dotted
 * path in the `narrative` slice of BrandSettings. The runtime writes those
 * nested paths back via the feature's update function (composed in
 * FormRuntimeProvider).
 */
export const narrativeSchema: SectionSchema = {
  key: "brand.narrative",
  title: "Narrativa (StoryBrand)",
  description: "7 pasos para que tu cliente sea el héroe y tu marca la guía.",
  fields: [
    { id: "one_liner", label: "One-liner", type: "textarea", path: "one_liner", rows: 2 },

    {
      id: "hero_identity",
      label: "Héroe: identidad",
      type: "textarea",
      path: "hero.identity",
      rows: 2,
    },
    { id: "hero_desire", label: "Héroe: deseo", type: "textarea", path: "hero.desire", rows: 2 },

    { id: "problem_villain", label: "Villano", type: "textarea", path: "problem.villain", rows: 2 },
    {
      id: "problem_external",
      label: "Problema externo",
      type: "textarea",
      path: "problem.external_problem",
      rows: 2,
    },
    {
      id: "problem_internal",
      label: "Problema interno",
      type: "textarea",
      path: "problem.internal_problem",
      rows: 2,
    },
    {
      id: "problem_philosophical",
      label: "Problema filosófico",
      type: "textarea",
      path: "problem.philosophical_problem",
      rows: 2,
    },

    {
      id: "guide_empathy",
      label: "Empatía de la guía",
      type: "textarea",
      path: "guide.empathy_statement",
      rows: 2,
    },
    {
      id: "guide_authority",
      label: "Autoridad de la guía",
      type: "textarea",
      path: "guide.authority_statement",
      rows: 2,
    },

    {
      id: "plan",
      label: "Plan (pasos)",
      type: "array",
      path: "plan",
      itemSchema: {
        fields: [
          {
            id: "step_number",
            label: "Número",
            type: "number",
            path: "step_number",
            required: true,
          },
          { id: "title", label: "Título", type: "text", path: "title" },
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 2,
          },
        ],
      },
    },

    { id: "cta_direct", label: "CTA directo", type: "text", path: "cta.direct_cta" },
    {
      id: "cta_transitional",
      label: "CTA transicional",
      type: "text",
      path: "cta.transitional_cta",
    },

    {
      id: "outcome_success",
      label: "Transformación (éxito)",
      type: "textarea",
      path: "outcome.success_transformation",
      rows: 2,
    },
    {
      id: "outcome_failure",
      label: "Consecuencia (fracaso)",
      type: "textarea",
      path: "outcome.failure_consequence",
      rows: 2,
    },
  ],
};
