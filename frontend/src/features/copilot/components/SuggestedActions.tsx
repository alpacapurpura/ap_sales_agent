"use client";

import { Lightbulb } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "../store/copilot-store";
import { useCopilotChat } from "../hooks/useCopilotChat";
import { reportCopilotEvent } from "../api/copilot-api";

/**
 * Route-aware quick actions shown when the copilot chat is empty.
 */

interface SuggestedAction {
  label: string;
  prompt: string;
}

const ROUTE_SUGGESTIONS: Record<string, SuggestedAction[]> = {
  "brand-settings": [
    { label: "¿Qué me falta de mi marca?", prompt: "¿Qué secciones de mi Brand Studio están incompletas?" },
    { label: "Mejora mi UVP", prompt: "Revisa mi UVP actual y sugiere mejoras" },
    { label: "Extrae mi marca de mi web", prompt: "Quiero extraer la identidad de mi marca desde mi sitio web" },
  ],
  "offer-studio": [
    { label: "Crea una oferta", prompt: "Ayúdame a crear una nueva oferta para mi negocio" },
    { label: "Revisa mi escalera", prompt: "Analiza mi escalera de ofertas y sugiere mejoras" },
    { label: "Mejora mis objeciones", prompt: "Revisa las objeciones de mis ofertas y sugiere mejores respuestas" },
  ],
  "growth-studio": [
    { label: "¿Cómo van mis métricas?", prompt: "Dame un resumen de mis métricas de ventas y conversión" },
    { label: "¿Dónde pierdo conversiones?", prompt: "Analiza mi funnel y dime en qué etapa pierdo más conversiones" },
    { label: "Explica mi funnel", prompt: "Explica qué significan las métricas de mi funnel" },
  ],
  sales: [
    { label: "¿Cómo va mi agente?", prompt: "Dame un resumen del rendimiento de mi agente de ventas" },
    { label: "¿Quiénes son mis mejores leads?", prompt: "Muéstrame mis leads más calientes y con mayor intent score" },
    { label: "Resumen del pipeline", prompt: "Dame un panorama de mi pipeline de ventas" },
  ],
  connections: [
    { label: "¿Qué debo conectar primero?", prompt: "¿Qué integraciones me recomiendas configurar primero y por qué?" },
    { label: "Estado de mis conexiones", prompt: "Muéstrame el estado de todas mis conexiones" },
  ],
  default: [
    { label: "¿Qué me falta configurar?", prompt: "¿Qué módulos de mi negocio están incompletos?" },
    { label: "Guíame paso a paso", prompt: "Guíame en la configuración inicial de mi negocio paso a paso" },
    { label: "¿Cómo está mi negocio?", prompt: "Dame un resumen general del estado de configuración de todo mi negocio" },
  ],
};

function getSuggestionsForRoute(route: string | null): SuggestedAction[] {
  if (!route) return ROUTE_SUGGESTIONS.default;
  for (const [key, suggestions] of Object.entries(ROUTE_SUGGESTIONS)) {
    if (key !== "default" && route.includes(key)) {
      return suggestions;
    }
  }
  return ROUTE_SUGGESTIONS.default;
}

export function SuggestedActions() {
  const currentRoute = useCopilotStore((s) => s.currentRoute);
  const messages = useCopilotStore((s) => s.messages);
  const { sendMessage } = useCopilotChat();
  const { getToken } = useAuth();

  // Only show when chat is empty
  if (messages.length > 0) return null;

  const suggestions = getSuggestionsForRoute(currentRoute);

  const handleClick = (s: SuggestedAction) => {
    sendMessage(s.prompt);
    getToken().then((token) => {
      if (token) {
        reportCopilotEvent("suggested_action_clicked", { action_label: s.label }, token);
      }
    });
  };

  return (
    <div className="space-y-2 px-4 pb-2">
      <div className="flex items-center gap-1.5 text-xs text-slate-400">
        <Lightbulb className="h-3 w-3" />
        <span>Sugerencias</span>
      </div>
      <div className="flex flex-col gap-1.5">
        {suggestions.map((s) => (
          <Button
            key={s.label}
            variant="outline"
            size="sm"
            onClick={() => handleClick(s)}
            className="h-auto justify-start whitespace-normal rounded-lg px-3 py-2 text-left text-xs font-normal text-slate-600 hover:bg-purple-50 hover:text-purple-700 dark:text-slate-300 dark:hover:bg-purple-900/20"
          >
            {s.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
