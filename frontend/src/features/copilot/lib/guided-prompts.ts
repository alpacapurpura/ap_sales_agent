/**
 * Shared helpers para activar guided-setup mode del copilot desde cualquier
 * studio. Centralizan los strings que el LLM ve (`promptFor`) y la URL final
 * a la que el usuario navega después (`routeFor`), de modo que GuidedSetupButton,
 * useGuidedEntityCreation y los dashboards (Brand, Offer, BuyerPersona) no
 * dupliquen ese contrato.
 *
 * Mantener este archivo y los catálogos editables (`copilot_editable_fields*`)
 * alineados al esquema FE — un drift acá hace que el LLM llame a
 * start_guided_setup con un domain que el backend no soporta y la sesión
 * guiada nunca arranca.
 */

/** Dominios soportados por start_guided_setup en el backend. */
export type GuidedDomain = "brand" | "buyer_persona" | "offer";

/** URL canónica a la que navegar después de disparar el guided. */
export function routeFor(
  domain: GuidedDomain | (string & {}),
  tenantId: string,
  entityId?: string,
): string {
  switch (domain) {
    case "brand":
      return `/${tenantId}/brand-studio`;
    case "buyer_persona":
      return entityId
        ? `/${tenantId}/brand-studio/publico/persona/${entityId}`
        : `/${tenantId}/brand-studio/publico`;
    case "offer":
      return entityId ? `/${tenantId}/offer-studio/offer/${entityId}` : `/${tenantId}/offer-studio`;
    default:
      return `/${tenantId}/${domain.replace("_", "-")}-studio`;
  }
}

/**
 * Prompt que se envía al chat para que el LLM responda con un tool-call
 * `start_guided_setup`. Usar el mismo wording asegura que el modelo no se
 * desvíe a una conversación libre cuando el usuario quiere guiarse.
 */
export function promptFor(domain: GuidedDomain | (string & {}), entityId?: string): string {
  const entity = entityId ? ` (id: ${entityId})` : "";
  switch (domain) {
    case "brand":
      return `Llama start_guided_setup con domain="brand" para guiarme paso a paso en Brand Studio.`;
    case "buyer_persona":
      return `Llama start_guided_setup con domain="buyer_persona" y entity_id="${entityId ?? ""}"${entity} para guiarme en este buyer persona.`;
    case "offer":
      return `Llama start_guided_setup con domain="offer" y entity_id="${entityId ?? ""}"${entity} para guiarme en esta oferta.`;
    default:
      return `Llama start_guided_setup con domain="${domain}" para guiarme en este módulo.`;
  }
}

/**
 * Indica si el dominio puede arrancar guided sin entity_id. Brand opera a
 * nivel tenant (1 brand por tenant), por eso no requiere id; offer y
 * buyer_persona necesitan una entidad concreta para que el persister tenga
 * blanco al que escribir.
 */
export function canStartGuided(domain: GuidedDomain | (string & {}), entityId?: string): boolean {
  if (domain === "brand") return true;
  if (domain === "buyer_persona" || domain === "offer") return Boolean(entityId);
  return Boolean(entityId);
}
