"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import type { SelectedContactsBarAction } from "../types";

interface SelectedContactsBarProps {
  selectedIds: string[];
  actions: SelectedContactsBarAction[];
  onClearSelection: () => void;
}

/**
 * Barra de acciones para contactos seleccionados.
 * Visible cuando selectedIds.length > 0.
 * Slot pattern: actions prop array → PR-12 inyecta "Crear segmento"; PI-3 agrega más.
 *
 * Arch test: test_selected_contacts_bar_slot_pattern.test.ts enforces.
 */
export function SelectedContactsBar({
  selectedIds,
  actions,
  onClearSelection,
}: SelectedContactsBarProps) {
  if (selectedIds.length === 0) return null;

  return (
    <div
      role="region"
      aria-label="Acciones para contactos seleccionados"
      className={cn(
        "fixed bottom-0 left-0 right-0 z-40",
        "flex items-center justify-between gap-4 px-6 py-3",
        "bg-card border-t shadow-lg",
        "animate-in slide-in-from-bottom-2 duration-200",
      )}
    >
      <span className="text-sm font-medium">
        {selectedIds.length}{" "}
        {selectedIds.length === 1 ? "contacto seleccionado" : "contactos seleccionados"}
      </span>

      <div className="flex items-center gap-2">
        {actions.map((action) => {
          const disabled = action.requiresSelection !== false && selectedIds.length === 0;
          return (
            <Button
              key={action.id}
              variant={action.variant ?? "default"}
              size="sm"
              disabled={disabled}
              onClick={() => void action.onClick(selectedIds)}
            >
              {action.icon && <span className="mr-1">{action.icon}</span>}
              {action.label}
            </Button>
          );
        })}

        <Button variant="ghost" size="sm" onClick={onClearSelection} aria-label="Limpiar selección">
          Limpiar selección
        </Button>
      </div>
    </div>
  );
}
