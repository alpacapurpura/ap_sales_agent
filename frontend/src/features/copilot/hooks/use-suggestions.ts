"use client";

// [COPILOT-SUGGESTIONS-ENGINE] — docs/domains/copilot/UI-SPEC.md §9
// Stub hook: returns static suggestions per route.
// When the real engine is ready:
//   - Create frontend/src/features/copilot/api/suggestions-api.ts exporting
//     fetchSuggestions(); use React Query here to call it.
//   - The hook interface (return type) MUST remain stable so callers need no changes.
//   - Engine endpoint: POST /api/v1/copilot/suggestions
//     Body: { conversation_id, route, recent_message_ids[], incomplete_fields[] }

import { useMemo } from "react";

import { useCopilotStore } from "../store/copilot-store";

import type { Suggestion } from "../types/suggestions";

// ── Route → suggestion map ────────────────────────────────────────────

const ROUTE_SUGGESTIONS: Record<string, Suggestion[]> = {
  "brand-studio": [
    {
      id: "stub-brand-1",
      label: "¿Qué me falta?",
      prompt: "¿Qué secciones de mi Brand Studio están incompletas?",
      category: "action",
    },
    {
      id: "stub-brand-2",
      label: "Mejora mi UVP",
      prompt: "Revisa mi UVP actual y sugiere mejoras",
      category: "action",
    },
    {
      id: "stub-brand-3",
      label: "Extrae mi marca",
      prompt: "Quiero extraer la identidad de mi marca desde mi sitio web",
      category: "action",
    },
  ],
  "offer-studio": [
    {
      id: "stub-offer-1",
      label: "Crea una oferta",
      prompt: "Ayúdame a crear una nueva oferta para mi negocio",
      category: "action",
    },
    {
      id: "stub-offer-2",
      label: "Revisa mi escalera",
      prompt: "Analiza mi escalera de ofertas y sugiere mejoras",
      category: "action",
    },
    {
      id: "stub-offer-3",
      label: "Mejora objeciones",
      prompt: "Revisa las objeciones de mis ofertas y sugiere mejores respuestas",
      category: "action",
    },
  ],
  "growth-studio": [
    {
      id: "stub-growth-1",
      label: "Mis métricas",
      prompt: "Dame un resumen de mis métricas de ventas y conversión",
      category: "action",
    },
    {
      id: "stub-growth-2",
      label: "¿Dónde pierdo conversiones?",
      prompt: "Analiza mi funnel y dime en qué etapa pierdo más conversiones",
      category: "clarify",
    },
    {
      id: "stub-growth-3",
      label: "Explica mi funnel",
      prompt: "Explica qué significan las métricas de mi funnel",
      category: "clarify",
    },
  ],
  sales: [
    {
      id: "stub-sales-1",
      label: "¿Cómo va mi agente?",
      prompt: "Dame un resumen del rendimiento de mi agente de ventas",
      category: "action",
    },
    {
      id: "stub-sales-2",
      label: "Mejores leads",
      prompt: "Muéstrame mis leads más calientes y con mayor intent score",
      category: "action",
    },
    {
      id: "stub-sales-3",
      label: "Mi pipeline",
      prompt: "Dame un panorama de mi pipeline de ventas",
      category: "action",
    },
  ],
  connections: [
    {
      id: "stub-conn-1",
      label: "¿Qué conecto primero?",
      prompt: "¿Qué integraciones me recomiendas configurar primero y por qué?",
      category: "action",
    },
    {
      id: "stub-conn-2",
      label: "Estado de conexiones",
      prompt: "Muéstrame el estado de todas mis conexiones",
      category: "action",
    },
  ],
  default: [
    {
      id: "stub-def-1",
      label: "¿Qué me falta configurar?",
      prompt: "¿Qué módulos de mi negocio están incompletos?",
      category: "action",
    },
    {
      id: "stub-def-2",
      label: "Guíame paso a paso",
      prompt: "Guíame en la configuración inicial de mi negocio paso a paso",
      category: "action",
    },
    {
      id: "stub-def-3",
      label: "¿Cómo está mi negocio?",
      prompt: "Dame un resumen general del estado de configuración de todo mi negocio",
      category: "action",
    },
  ],
};

function getSuggestionsForRoute(route: string | null): Suggestion[] {
  if (!route) return ROUTE_SUGGESTIONS.default;
  for (const [key, suggestions] of Object.entries(ROUTE_SUGGESTIONS)) {
    if (key !== "default" && route.includes(key)) {
      return suggestions;
    }
  }
  return ROUTE_SUGGESTIONS.default;
}

// ── Hook ─────────────────────────────────────────────────────────────

export interface UseSuggestionsReturn {
  chips: Suggestion[];
  isLoading: boolean;
}

/**
 * Returns suggested action chips for the current route.
 *
 * [COPILOT-SUGGESTIONS-ENGINE] stub implementation.
 * Replace with React Query call when the real engine endpoint is available.
 */
export function useSuggestions(): UseSuggestionsReturn {
  const currentRoute = useCopilotStore((s) => s.currentRoute);

  const chips = useMemo(() => getSuggestionsForRoute(currentRoute), [currentRoute]);

  return { chips, isLoading: false };
}
