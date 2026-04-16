import { LandingPageArchetype } from "@/features/offer-studio/components/landing/types/schema";

import type { RootProps, Props } from "./puck.config";
import type {
  LandingPageConfig,
  TransformerContent,
  SqueezeContent,
  FlashOfferContent,
} from "@/features/offer-studio/components/landing/types/schema";
import type { Data } from "@puckeditor/core";

// Helper to generate a unique ID for blocks
const generateId = (type: string) => `${type}-${Math.random().toString(36).substr(2, 9)}`;

// --- Archetype Transformers ---

function transformTransformerArchetype(content: TransformerContent, data: Data<Props, RootProps>) {
  // 1. Hero
  data.content.push({
    type: "HeroSection",
    props: {
      id: generateId("HeroSection"),
      headline: content.headline,
      subheadline: content.subheadline,
      cta_text: content.cta_text,
      scarcity_text: content.scarcity_text,
      layout: content.hero_layout || "centered",
      video_url: content.video_url,
    },
  });

  // 2. PAS Grid
  data.content.push({
    type: "PasGridSection",
    props: {
      id: generateId("PasGridSection"),
      problem_text: content.problem_text,
      agitation_text: content.agitation_text,
      solution_text: content.solution_text,
    },
  });

  // 3. Solution (Mechanism)
  data.content.push({
    type: "SolutionSection",
    props: {
      id: generateId("SolutionSection"),
      method_name: content.method_name,
      method_description: content.method_description,
    },
  });

  // 4. Authority
  data.content.push({
    type: "AuthoritySection",
    props: {
      id: generateId("AuthoritySection"),
      authority_name: content.authority_name,
      authority_bio: content.authority_bio,
      authority_image_url: content.authority_image_url,
      story_hook: content.story_hook,
    },
  });

  // 5. Stack (Modules)
  if (content.modules && content.modules.length > 0) {
    data.content.push({
      type: "StackSection",
      props: {
        id: generateId("StackSection"),
        modules: content.modules.map((m) => ({
          title: m.title,
          description: m.description || "",
        })),
      },
    });
  }

  // 6. Offer
  data.content.push({
    type: "OfferSection",
    props: {
      id: generateId("OfferSection"),
      offer_headline: `Únete a ${content.headline}`,
      price_anchor: content.price_anchor,
      price_offer: content.price_offer,
      cta_text: content.cta_text,
      bonuses: (content.bonuses || []).map((b) => ({
        title: b.title,
        description: b.description || "",
      })),
    },
  });
}

function transformSqueezeArchetype(content: SqueezeContent, data: Data<Props, RootProps>) {
  // Squeeze pages focus on the Hero and Bullets
  data.content.push({
    type: "HeroSection",
    props: {
      id: generateId("HeroSection"),
      headline: content.headline,
      subheadline: content.subheadline,
      cta_text: content.cta_text,
      scarcity_text: content.privacy_text || "Tu privacidad es importante",
    },
  });

  if (content.bullets && content.bullets.length > 0) {
    data.content.push({
      type: "StackSection",
      props: {
        id: generateId("StackSection"),
        modules: content.bullets.map((b) => ({
          title: b,
          description: "",
        })),
      },
    });
  }
}

function transformFlashOfferArchetype(content: FlashOfferContent, data: Data<Props, RootProps>) {
  // Flash Offer: Hero -> Problem/Solution -> Offer
  data.content.push({
    type: "HeroSection",
    props: {
      id: generateId("HeroSection"),
      headline: content.headline,
      subheadline: content.offer_name,
      cta_text: content.cta_text,
      scarcity_text: content.guarantee_text,
    },
  });

  data.content.push({
    type: "PasGridSection",
    props: {
      id: generateId("PasGridSection"),
      problem_text: content.problem_agitation,
      agitation_text: "", // Flash offers might combine them
      solution_text: content.solution_description,
    },
  });

  data.content.push({
    type: "OfferSection",
    props: {
      id: generateId("OfferSection"),
      offer_headline: content.offer_name,
      price_anchor: content.original_price?.toString(),
      price_offer: content.discounted_price?.toString(),
      cta_text: content.cta_text,
      bonuses: [],
    },
  });
}

export function transformConfigToPuckData(config: LandingPageConfig): Data<Props, RootProps> {
  // Base structure
  const data: Data<Props, RootProps> = {
    root: {
      props: {
        theme: config.theme,
      },
    },
    content: [],
    zones: {},
  };

  // Dispatch based on Archetype
  switch (config.archetype) {
    case LandingPageArchetype.THE_TRANSFORMER:
      transformTransformerArchetype(config.content as TransformerContent, data);
      break;
    case LandingPageArchetype.THE_SQUEEZE:
      transformSqueezeArchetype(config.content as SqueezeContent, data);
      break;
    case LandingPageArchetype.THE_FLASH_OFFER:
      transformFlashOfferArchetype(config.content as FlashOfferContent, data);
      break;
    // Default fallback for other archetypes to Transformer logic (safest bet for now)
    default:
      console.warn(
        `Archetype ${config.archetype} not fully implemented, falling back to Transformer logic.`,
      );
      // Try to cast as TransformerContent as it has the most fields
      transformTransformerArchetype(config.content as TransformerContent, data);
      break;
  }

  return data;
}
