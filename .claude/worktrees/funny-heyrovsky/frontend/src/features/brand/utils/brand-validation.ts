import { BrandSettings, BrandIdentity, BrandStrategy, BrandStory, KeyFigure, ContactData, BrandVisuals, AuthorityItem } from "@/features/brand/types";
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
  if (!strategy) return { status: "empty", label: "Pendiente", missingFields: ["Estrategia General"], score: 0 };
  
  if (!strategy.unique_value_proposition) missing.push("Propuesta de Valor");
  if (!strategy.methodology_name) missing.push("Nombre de Metodología");
  if (!strategy.competitors || strategy.competitors.length === 0) missing.push("Competidores");
  if (!strategy.methodology_pillars || strategy.methodology_pillars.length === 0) missing.push("Pilares de Metodología");

  const criticalMissing = !strategy.unique_value_proposition;
  
  return calculateStatus(missing, 4, criticalMissing);
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

export const getBrandHealth = (settings: BrandSettings): number => {
  const scores = [
    validateIdentity(settings.identity ?? {}).score,
    validateStrategy(settings.strategy ?? { competitors: [], methodology_pillars: [] }).score,
    validateStory(settings.story ?? {}).score,
    validateVisuals(settings.visuals ?? {}).score,
    validateTeam(settings.team ?? []).score,
    validateContact(settings.contact ?? {}).score,
    validateAuthority(settings.authority_vault ?? []).score
  ];
  
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
};
