import { BrandSettings, BrandIdentity, BrandStrategy, BrandStory, KeyFigure, ContactData, BrandVisuals, AuthorityItem, BrandPositioning, BrandNarrative, CommunicationAssets } from "@/features/brand/types";
import { Avatar } from "@/lib/api/avatar";

export type ValidationStatus = "complete" | "partial" | "empty";

export interface StatusResult {
  status: ValidationStatus;
  label: string;
  missingFields: string[];
  score: number; // 0-100
}

/**
 * Helper to determine status based on missing fields
 */
const calculateStatus = (missingFields: string[], totalFields: number, criticalMissing: boolean): StatusResult => {
  const filled = totalFields - missingFields.length;
  // Ensure score is not negative
  const safeFilled = Math.max(0, filled);
  const score = Math.round((safeFilled / totalFields) * 100);
  
  if (safeFilled === 0) {
    return { status: "empty", label: "Pendiente", missingFields, score: 0 };
  }
  
  if (criticalMissing || score < 100) {
    return { status: "partial", label: "En Progreso", missingFields, score };
  }
  
  return { status: "complete", label: "Completo", missingFields: [], score: 100 };
};

export const validateIdentity = (identity: BrandIdentity): StatusResult => {
  const missing: string[] = [];
  if (!identity) return { status: "empty", label: "Pendiente", missingFields: ["Datos de Identidad"], score: 0 };
  
  if (!identity.brand_name) missing.push("Nombre de Marca");
  if (!identity.website) missing.push("Sitio Web");
  if (!identity.industry) missing.push("Industria");
  if (!identity.logo_url) missing.push("Logo");

  const criticalMissing = !identity.brand_name || !identity.logo_url;
  
  return calculateStatus(missing, 4, criticalMissing);
};

export const validateStrategy = (strategy: BrandStrategy): StatusResult => {
  const missing: string[] = [];
  if (!strategy) return { status: "empty", label: "Pendiente", missingFields: ["Metodologia"], score: 0 };

  if (!strategy.methodology_name) missing.push("Nombre de Metodologia");
  if (!strategy.methodology_pillars || strategy.methodology_pillars.length === 0) missing.push("Pilares de Metodologia");

  const criticalMissing = !strategy.methodology_name;

  return calculateStatus(missing, 2, criticalMissing);
};

export const validateStory = (story: BrandStory): StatusResult => {
  const missing: string[] = [];
  if (!story) return { status: "empty", label: "Pendiente", missingFields: ["Historia de Marca"], score: 0 };
  
  if (!story.origin_story) missing.push("Historia de Origen");
  if (!story.milestones || story.milestones.length === 0) missing.push("Hitos Importantes");
  
  const filled = 2 - missing.length;
  return calculateStatus(missing, 2, filled === 0);
};

export const validateVisuals = (visuals: BrandVisuals): StatusResult => {
  const missing: string[] = [];
  if (!visuals) return { status: "empty", label: "Pendiente", missingFields: ["Identidad Visual"], score: 0 };
  
  if (!visuals.primary_color) missing.push("Color Primario");
  if (!visuals.accent_color) missing.push("Color de Acento");
  if (!visuals.font_heading) missing.push("Fuente de Títulos");
  if (!visuals.font_body) missing.push("Fuente de Cuerpo");
  
  return calculateStatus(missing, 4, missing.length > 0);
};

export const validateTeam = (team: KeyFigure[]): StatusResult => {
  if (!team || team.length === 0) return { status: "empty", label: "Sin Equipo", missingFields: ["Miembros del Equipo"], score: 0 };
  
  // Check if at least one member is "complete"
  const validMembers = team.filter(m => m.name && m.role && m.headshot_url);
  
  if (validMembers.length === team.length) {
    return { status: "complete", label: "Equipo Listo", missingFields: [], score: 100 };
  }
  
  // If we have members but some are incomplete
  const missingCount = team.length - validMembers.length;
  const missing = missingCount > 0 ? [`${missingCount} Miembros incompletos`] : [];
  
  return { status: "partial", label: "Faltan datos", missingFields: missing, score: 50 };
};

export const validateContact = (contact: ContactData): StatusResult => {
  const missing: string[] = [];
  if (!contact) return { status: "empty", label: "Pendiente", missingFields: ["Datos de Contacto"], score: 0 };
  
  if (!contact.support_email) missing.push("Email de Soporte");
  
  // Social check: needs at least one (Instagram OR LinkedIn)
  if (!contact.social_instagram && !contact.social_linkedin) {
    missing.push("Instagram o LinkedIn");
  }
  
  const totalFields = 2; // Email + Social
  
  return calculateStatus(missing, totalFields, !contact.support_email);
};

export const validateAuthority = (vault: AuthorityItem[]): StatusResult => {
  if (!vault || vault.length === 0) {
    return { status: "empty", label: "Sin Autoridad", missingFields: ["Items de Autoridad"], score: 0 };
  }
  return { status: "complete", label: "Autoridad Activa", missingFields: [], score: 100 };
};

export const validateVoice = (identity: BrandIdentity): StatusResult => {
  const missing: string[] = [];
  if (!identity) return { status: "empty", label: "Pendiente", missingFields: ["Idioma Principal", "Tono de Voz"], score: 0 };

  if (!identity.language) missing.push("Idioma Principal");
  // BrandIdentity does not have a tone_of_voice field yet — treat as always missing for now
  missing.push("Tono de Voz");

  const criticalMissing = false; // language defaults to "Español" in UI
  return calculateStatus(missing, 2, criticalMissing);
};

export const validateAvatars = (visuals: BrandVisuals): StatusResult => {
  // TODO: Integrate with avatars API count when available in BrandSettings.
  // Avatars are fetched via React Query in the component, not stored in BrandSettings directly.
  return { status: "partial", label: "Revisar", missingFields: ["Buyer Personas"], score: 50 };
};

// Item Level Validation

export const validateTeamMember = (member: KeyFigure): StatusResult => {
  const missing: string[] = [];
  if (!member.name) missing.push("Nombre");
  if (!member.role) missing.push("Rol");
  if (!member.headshot_url) missing.push("Foto");
  if (!member.bio) missing.push("Bio");

  return calculateStatus(missing, 4, !member.name || !member.role);
};

export const validateAvatar = (avatar: Avatar): StatusResult => {
  const missing: string[] = [];
  
  if (!avatar.name) missing.push("Nombre");
  if (!avatar.icp_description) missing.push("Descripción ICP");
  if (!avatar.pain_points || avatar.pain_points.length === 0) missing.push("Puntos de Dolor");
  if (!avatar.desires || avatar.desires.length === 0) missing.push("Deseos");

  return calculateStatus(missing, 4, !avatar.name);
};

export const validatePositioning = (positioning?: BrandPositioning): StatusResult => {
  if (!positioning) return { status: "empty", label: "Pendiente", missingFields: ["Posicionamiento"], score: 0 };

  const missing: string[] = [];
  if (!positioning.unique_value_proposition) missing.push("Propuesta de Valor Unica");
  if (!positioning.brand_essence) missing.push("Esencia de Marca");
  if (!positioning.discriminator) missing.push("Diferenciador");
  if (!positioning.insight?.tension) missing.push("Insight del Consumidor");
  if (!positioning.benefits?.functional_benefits?.length && !positioning.benefits?.emotional_benefits?.length) missing.push("Beneficios");

  const criticalMissing = !positioning.unique_value_proposition || !positioning.brand_essence;
  return calculateStatus(missing, 5, criticalMissing);
};

export const validateNarrative = (narrative?: BrandNarrative): StatusResult => {
  if (!narrative) return { status: "empty", label: "Pendiente", missingFields: ["Narrativa StoryBrand"], score: 0 };

  const missing: string[] = [];
  if (!narrative.hero?.identity) missing.push("Héroe");
  if (!narrative.problem?.villain) missing.push("Problema/Villano");
  if (!narrative.guide?.empathy_statement) missing.push("Guía");
  if (!narrative.one_liner) missing.push("One-Liner");

  const criticalMissing = !narrative.hero?.identity;
  return calculateStatus(missing, 4, criticalMissing);
};

export const validateCommunicationAssets = (assets?: CommunicationAssets): StatusResult => {
  if (!assets) return { status: "empty", label: "Pendiente", missingFields: ["Activos de Comunicación"], score: 0 };

  const missing: string[] = [];
  if (!assets.creative_concepts?.length) missing.push("Conceptos Creativos");
  if (!assets.assets?.length) missing.push("Activos por Funnel");

  return calculateStatus(missing, 2, missing.length === 2);
};

// --- Chapter-level aggregation ---

export interface ChapterHealth {
  id: string;
  label: string;
  scrollTo: string;
  score: number;
  status: ValidationStatus;
  missingFields: string[];
}

export const getChapterHealthMap = (settings: BrandSettings): ChapterHealth[] => {
  const aggregate = (results: StatusResult[]): Pick<ChapterHealth, "score" | "status" | "missingFields"> => {
    const score = Math.round(results.reduce((a, r) => a + r.score, 0) / results.length);
    const allComplete = results.every(r => r.status === "complete");
    const allEmpty = results.every(r => r.status === "empty");
    const status: ValidationStatus = allComplete ? "complete" : allEmpty ? "empty" : "partial";
    const missingFields = results.flatMap(r => r.missingFields);
    return { score, status, missingFields };
  };

  const chapters: ChapterHealth[] = [
    { id: "origen", label: "Origen", scrollTo: "identity", ...aggregate([
      validateIdentity(settings.identity ?? {}),
      validateStory(settings.story ?? {}),
      validateStrategy(settings.strategy ?? { methodology_pillars: [] }),
    ]) },
    { id: "diferenciacion", label: "Diferenciacion", scrollTo: "positioning", ...aggregate([
      validatePositioning(settings.positioning),
    ]) },
    { id: "mercado", label: "El Mercado", scrollTo: "market", ...aggregate([
      validatePositioning(settings.positioning),
    ]) },
    { id: "personalidad", label: "Personalidad", scrollTo: "values-essence", ...aggregate([
      validatePositioning(settings.positioning),
    ]) },
    { id: "historia", label: "La Historia", scrollTo: "storybrand", ...aggregate([
      validateNarrative(settings.narrative),
    ]) },
    { id: "voz", label: "La Voz", scrollTo: "voice", ...aggregate([
      validateVoice(settings.identity ?? {}),
      validateCommunicationAssets(settings.communication_assets),
    ]) },
    { id: "publico", label: "El Publico", scrollTo: "avatars", ...aggregate([
      validateAvatars(settings.visuals ?? {}),
    ]) },
    { id: "imagen", label: "La Imagen", scrollTo: "visuals", ...aggregate([
      validateVisuals(settings.visuals ?? {}),
    ]) },
    { id: "credibilidad", label: "Credibilidad", scrollTo: "team", ...aggregate([
      validateTeam(settings.team ?? []),
      validateAuthority(settings.authority_vault ?? []),
    ]) },
    { id: "contacto", label: "Contacto", scrollTo: "contact", ...aggregate([
      validateContact(settings.contact ?? {}),
    ]) },
  ];

  return chapters;
};

export const getBrandHealth = (settings: BrandSettings): number => {
  const scores = [
    validateIdentity(settings.identity ?? {}).score,
    validateStrategy(settings.strategy ?? { methodology_pillars: [] }).score,
    validateStory(settings.story ?? {}).score,
    validateVoice(settings.identity ?? {}).score,
    validateAvatars(settings.visuals ?? {}).score,
    validateVisuals(settings.visuals ?? {}).score,
    validateTeam(settings.team ?? []).score,
    validateContact(settings.contact ?? {}).score,
    validateAuthority(settings.authority_vault ?? []).score,
    validatePositioning(settings.positioning).score,
    validateNarrative(settings.narrative).score,
    validateCommunicationAssets(settings.communication_assets).score,
  ];

  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
};
