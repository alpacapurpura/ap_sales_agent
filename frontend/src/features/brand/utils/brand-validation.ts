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
 * Helper to determine status based on filled fields
 */
const calculateStatus = (filled: number, total: number, criticalMissing: boolean): StatusResult => {
  const score = Math.round((filled / total) * 100);
  
  if (filled === 0) {
    return { status: "empty", label: "Pendiente", missingFields: [], score: 0 };
  }
  
  if (criticalMissing || score < 100) {
    return { status: "partial", label: "En Progreso", missingFields: [], score };
  }
  
  return { status: "complete", label: "Completo", missingFields: [], score: 100 };
};

export const validateIdentity = (identity: BrandIdentity): StatusResult => {
  if (!identity) return { status: "empty", label: "Pendiente", missingFields: [], score: 0 };
  const fields = [
    identity.brand_name,
    identity.website,
    identity.industry,
    identity.logo_url
  ];
  const filled = fields.filter(Boolean).length;
  const criticalMissing = !identity.brand_name || !identity.logo_url;
  
  return calculateStatus(filled, fields.length, criticalMissing);
};

export const validateStrategy = (strategy: BrandStrategy): StatusResult => {
  if (!strategy) return { status: "empty", label: "Pendiente", missingFields: [], score: 0 };
  const fields = [
    strategy.unique_value_proposition,
    strategy.methodology_name,
    strategy.competitors?.length > 0,
    strategy.methodology_pillars?.length > 0
  ];
  const filled = fields.filter(Boolean).length;
  const criticalMissing = !strategy.unique_value_proposition;
  
  return calculateStatus(filled, fields.length, criticalMissing);
};

export const validateStory = (story: BrandStory): StatusResult => {
  if (!story) return { status: "empty", label: "Pendiente", missingFields: [], score: 0 };
  const fields = [
    story.origin_story,
    story.milestones?.length > 0
  ];
  const filled = fields.filter(Boolean).length;
  
  return calculateStatus(filled, fields.length, filled === 0);
};

export const validateVisuals = (visuals: BrandVisuals): StatusResult => {
  if (!visuals) return { status: "empty", label: "Pendiente", missingFields: [], score: 0 };
  const fields = [
    visuals.primary_color,
    visuals.accent_color,
    visuals.font_heading,
    visuals.font_body
  ];
  const filled = fields.filter(Boolean).length;
  
  return calculateStatus(filled, fields.length, filled < 4);
};

export const validateTeam = (team: KeyFigure[]): StatusResult => {
  if (!team || team.length === 0) return { status: "empty", label: "Sin Equipo", missingFields: [], score: 0 };
  
  // Check if at least one member is "complete"
  const validMembers = team.filter(m => m.name && m.role && m.headshot_url);
  
  if (validMembers.length === team.length) {
    return { status: "complete", label: "Equipo Listo", missingFields: [], score: 100 };
  }
  
  return { status: "partial", label: "Faltan datos", missingFields: [], score: 50 };
};

export const validateContact = (contact: ContactData): StatusResult => {
  if (!contact) return { status: "empty", label: "Pendiente", missingFields: [], score: 0 };
  const fields = [
    contact.support_email,
    contact.social_instagram || contact.social_linkedin
  ];
  const filled = fields.filter(Boolean).length;
  
  return calculateStatus(filled, fields.length, !contact.support_email);
};

export const validateAuthority = (vault: AuthorityItem[]): StatusResult => {
  if (!vault || vault.length === 0) return { status: "empty", label: "Sin Autoridad", missingFields: [], score: 0 };
  return { status: "complete", label: "Autoridad Activa", missingFields: [], score: 100 };
};

// Item Level Validation

export const validateTeamMember = (member: KeyFigure): StatusResult => {
  const fields = [member.name, member.role, member.headshot_url, member.bio];
  const filled = fields.filter(Boolean).length;
  return calculateStatus(filled, fields.length, !member.name || !member.role);
};

export const validateAvatar = (avatar: Avatar): StatusResult => {
  const fields = [
    avatar.name,
    avatar.icp_description,
    avatar.pain_points && avatar.pain_points.length > 0,
    avatar.desires && avatar.desires.length > 0
  ];
  const filled = fields.filter(Boolean).length;
  return calculateStatus(filled, fields.length, !avatar.name);
};

export const getBrandHealth = (settings: BrandSettings): number => {
  const scores = [
    validateIdentity(settings.identity).score,
    validateStrategy(settings.strategy).score,
    validateStory(settings.story).score,
    validateVisuals(settings.visuals).score,
    validateTeam(settings.team).score,
    validateContact(settings.contact).score
  ];
  
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
};
