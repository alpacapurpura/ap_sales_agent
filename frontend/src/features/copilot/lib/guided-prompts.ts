/**
 * Single source of truth para activar guided-setup mode del copilot desde
 * cualquier studio. Centraliza:
 *
 *   - Wording natural que el LLM ve y traduce a un tool-call
 *     ``start_guided_setup`` (ver backend `start_guided_setup` docstring:
 *     dispara cuando el usuario dice "guíame", "ayúdame a completar...").
 *   - URL canónica a la que se navega después del trigger.
 *   - Si el dominio puede arrancar guided sin entity_id (brand opera a
 *     nivel tenant; offer/buyer_persona necesitan entidad concreta).
 *
 * Agregar un dominio nuevo = agregar UNA entrada en `GUIDED_DOMAINS`.
 * Mantener este archivo alineado con `_SUPPORTED_DOMAINS` en el backend
 * (`copilot/application/tools/guided/start.py`) — drift hace que el LLM
 * pida un dominio que el backend rechaza.
 */

/** Dominios soportados por start_guided_setup en el backend. */
export type GuidedDomain = "brand" | "buyer_persona" | "offer";

/**
 * Configuración por dominio. Diseñada para que el prompt suene a usuario
 * humano (no a instrucción técnica) y el `start_guided_setup` reciba el
 * `entity_id` vía interpolación natural — el LLM lo extrae igual que un
 * lector lo entendería.
 */
interface GuidedDomainConfig {
  /** Demostrativo + sustantivo, post-creación. Ej: "esta oferta". */
  readonly justCreatedNoun: string;
  /** Pronombre objeto que cierra el imperativo "configurar___" según género/número. */
  readonly objectPronoun: "lo" | "la" | "los" | "las";
  /** Frase corta para el caso "todavía no hay entidad". Ej: "tu marca". */
  readonly bareNoun: string;
  /** Si true, el dominio opera a nivel tenant y NO requiere entity_id. */
  readonly tenantScoped?: boolean;
  /** Construye la URL canónica de detalle/dashboard. */
  buildRoute(tenantId: string, entityId?: string): string;
}

const GUIDED_DOMAINS: Readonly<Record<GuidedDomain, GuidedDomainConfig>> = {
  brand: {
    justCreatedNoun: "tu marca",
    objectPronoun: "la",
    bareNoun: "tu marca",
    tenantScoped: true,
    buildRoute: (tenantId) => `/${tenantId}/brand-studio`,
  },
  buyer_persona: {
    justCreatedNoun: "este buyer persona",
    objectPronoun: "lo",
    bareNoun: "un buyer persona",
    buildRoute: (tenantId, entityId) =>
      entityId
        ? `/${tenantId}/brand-studio/publico/persona/${entityId}`
        : `/${tenantId}/brand-studio/publico`,
  },
  offer: {
    justCreatedNoun: "esta oferta",
    objectPronoun: "la",
    bareNoun: "una oferta",
    buildRoute: (tenantId, entityId) =>
      entityId ? `/${tenantId}/offer-studio/offer/${entityId}` : `/${tenantId}/offer-studio`,
  },
};

function configFor(domain: string): GuidedDomainConfig | null {
  return (GUIDED_DOMAINS as Record<string, GuidedDomainConfig | undefined>)[domain] ?? null;
}

/** URL canónica a la que navegar después de disparar el guided. */
export function routeFor(
  domain: GuidedDomain | (string & {}),
  tenantId: string,
  entityId?: string,
): string {
  const cfg = configFor(domain);
  if (cfg) return cfg.buildRoute(tenantId, entityId);
  // Fallback genérico para dominios no registrados (mismo contrato que antes).
  return `/${tenantId}/${domain.replace("_", "-")}-studio`;
}

/**
 * Mensaje que se envía al chat. Frases que el LLM mapea a
 * `start_guided_setup` por su system prompt ("guíame", "ayúdame a
 * completar..."). El `(id: ...)` queda discreto pero le da al modelo el
 * `entity_id` exacto que necesita pasar al tool.
 */
export function promptFor(domain: GuidedDomain | (string & {}), entityId?: string): string {
  const cfg = configFor(domain);
  if (!cfg) {
    return `Guíame paso a paso para terminar de configurar este módulo.`;
  }
  if (cfg.tenantScoped) {
    return `Guíame paso a paso para terminar de configurar ${cfg.bareNoun}.`;
  }
  if (!entityId) {
    return `Quiero crear ${cfg.bareNoun}. Guíame paso a paso.`;
  }
  return `Acabo de crear ${cfg.justCreatedNoun} (id: ${entityId}). Guíame paso a paso para configurar${cfg.objectPronoun}.`;
}

/**
 * Indica si el dominio puede arrancar guided sin entity_id. Brand opera a
 * nivel tenant, por eso no requiere id; offer y buyer_persona necesitan
 * una entidad concreta para que el persister tenga blanco al que escribir.
 */
export function canStartGuided(domain: GuidedDomain | (string & {}), entityId?: string): boolean {
  const cfg = configFor(domain);
  if (cfg?.tenantScoped) return true;
  return Boolean(entityId);
}
