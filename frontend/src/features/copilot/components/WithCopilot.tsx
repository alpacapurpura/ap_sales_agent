"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Plus, Check } from "lucide-react";
import { useCopilotStore } from "../store/copilot-store";

interface WithCopilotProps {
  fieldId: string;
  fieldLabel: string;
  getValue: () => string;
  children: React.ReactNode;
}

/**
 * Wrapper that makes any form field copilot-aware.
 * - Shows a pill button ("+ a Copilot") on hover/focus
 * - Purple outline when the field is selected as copilot context
 * - Listens for `copilot:field-update` events to highlight when AI updates the field
 */
export function WithCopilot({ fieldId, fieldLabel, getValue, children }: WithCopilotProps) {
  const isSelected = useCopilotStore((s) => s.selectedFields.some((f) => f.fieldId === fieldId));
  const addSelectedField = useCopilotStore((s) => s.addSelectedField);
  const removeSelectedField = useCopilotStore((s) => s.removeSelectedField);
  const openPanel = useCopilotStore((s) => s.openPanel);

  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [isHighlighted, setIsHighlighted] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Stable ref for getValue — avoids effect churn from inline arrow props
  const getValueRef = useRef(getValue);
  useEffect(() => {
    getValueRef.current = getValue;
  });

  const showButton = isHovered || isFocused || isSelected;

  const handleToggle = useCallback(() => {
    if (isSelected) {
      removeSelectedField(fieldId);
    } else {
      addSelectedField({
        fieldId,
        fieldLabel,
        fieldValue: getValueRef.current(),
      });
      openPanel();
    }
  }, [isSelected, fieldId, fieldLabel, addSelectedField, removeSelectedField, openPanel]);

  // Listen for copilot:collect-values — refresh field value in store before send
  useEffect(() => {
    const collectHandler = () => {
      const currentSelected = useCopilotStore.getState().selectedFields;
      if (currentSelected.some((f) => f.fieldId === fieldId)) {
        useCopilotStore.getState().updateFieldValue(fieldId, getValueRef.current());
      }
    };
    window.addEventListener("copilot:collect-values", collectHandler);
    return () => window.removeEventListener("copilot:collect-values", collectHandler);
  }, [fieldId]);

  // Listen for copilot:field-update events targeting this field
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail as {
        fieldId: string;
        newValue: string;
      };
      if (detail.fieldId === fieldId) {
        setIsHighlighted(true);
        setTimeout(() => setIsHighlighted(false), 2500);
      }
    };

    window.addEventListener("copilot:field-update", handler);
    return () => window.removeEventListener("copilot:field-update", handler);
  }, [fieldId]);

  return (
    <div
      ref={containerRef}
      className="group/copilot relative"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocusCapture={() => setIsFocused(true)}
      onBlurCapture={() => setIsFocused(false)}
    >
      {/* Outline overlay */}
      <div
        className={[
          "pointer-events-none absolute inset-0 rounded-lg border-2 transition-all duration-300",
          isSelected
            ? "border-purple-400 shadow-[0_0_0_1px_rgba(168,85,247,0.2)]"
            : isHighlighted
              ? "border-green-400 shadow-[0_0_8px_rgba(74,222,128,0.4)]"
              : "border-transparent",
        ].join(" ")}
      />

      {/* Pill toggle button — always rendered, animated via CSS */}
      <button
        type="button"
        onClick={handleToggle}
        className={[
          "absolute -top-3.5 right-3 z-10 flex items-center gap-1.5 rounded-full border px-2 py-1 text-[10px] font-medium shadow-sm transition-all duration-200",
          showButton
            ? "translate-y-0 opacity-100"
            : "pointer-events-none translate-y-1 opacity-0",
          isSelected
            ? "border-purple-300 bg-purple-500 text-white hover:bg-purple-600"
            : "border-purple-200 bg-white text-purple-700 hover:bg-purple-50 dark:border-purple-700 dark:bg-slate-800 dark:text-purple-300 dark:hover:bg-slate-700",
        ].join(" ")}
        title={
          isSelected
            ? `Quitar "${fieldLabel}" del contexto`
            : `Agregar "${fieldLabel}" al Copilot`
        }
      >
        {isSelected ? (
          <>
            <Check className="h-3 w-3" />
            <span>En contexto</span>
          </>
        ) : (
          <>
            <Plus className="h-3 w-3" />
            <span>a Copilot</span>
          </>
        )}
      </button>

      {children}
    </div>
  );
}
