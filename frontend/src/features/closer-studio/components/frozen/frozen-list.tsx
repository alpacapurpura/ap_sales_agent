"use client";

import { useFrozen } from "../../hooks/use-frozen";

import { FrozenCard } from "./frozen-card";

export function FrozenList() {
  const { data: frozen, isLoading } = useFrozen();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-muted-foreground">
        Cargando conversaciones congeladas...
      </div>
    );
  }

  if (!frozen || frozen.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
        <span className="text-4xl mb-3">🎉</span>
        <span className="text-sm font-medium">No hay conversaciones congeladas</span>
        <span className="text-xs">Todas las conversaciones estan activas</span>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-3 overflow-y-auto h-full">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-muted-foreground">
          {frozen.length} conversaciones congeladas
        </h3>
      </div>
      {frozen.map((conv) => (
        <FrozenCard key={conv.lead_id} conversation={conv} />
      ))}
    </div>
  );
}
