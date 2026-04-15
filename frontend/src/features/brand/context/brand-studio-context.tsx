"use client";

import { createContext, useContext, useState, useCallback, useMemo, type ReactNode } from "react";

import type { KeyFigure, AuthorityItem, TestimonialItem } from "../types";
import type { EditMode } from "../types/edit-mode";
import type { Avatar } from "@/lib/api/avatar";

type SelectedEditItem = KeyFigure | AuthorityItem | TestimonialItem | Avatar | null;

interface BrandStudioContextType {
  // Edit state
  editMode: EditMode;
  selectedItem: SelectedEditItem;
  openEdit: (mode: EditMode, item?: SelectedEditItem) => void;
  closeSheet: () => void;

  // Smart Fill state
  isSmartFillOpen: boolean;
  smartFillMode: "initial" | "update";
  openSmartFill: (mode: "initial" | "update") => void;
  closeSmartFill: () => void;

  // Empty state
  hasDismissedEmptyState: boolean;
  dismissEmptyState: () => void;
}

const BrandStudioContext = createContext<BrandStudioContextType | null>(null);

export function BrandStudioProvider({ children }: { children: ReactNode }) {
  const [editMode, setEditMode] = useState<EditMode>("none");
  const [selectedItem, setSelectedItem] = useState<SelectedEditItem>(null);
  const [isSmartFillOpen, setIsSmartFillOpen] = useState(false);
  const [smartFillMode, setSmartFillMode] = useState<"initial" | "update">("initial");
  const [hasDismissedEmptyState, setHasDismissedEmptyState] = useState(false);

  const openEdit = useCallback((mode: EditMode, item?: SelectedEditItem) => {
    setSelectedItem(item || null);
    setEditMode(mode);
  }, []);

  const closeSheet = useCallback(() => {
    setEditMode("none");
    setSelectedItem(null);
  }, []);

  const openSmartFill = useCallback((mode: "initial" | "update") => {
    setSmartFillMode(mode);
    setIsSmartFillOpen(true);
  }, []);

  const closeSmartFill = useCallback(() => {
    setIsSmartFillOpen(false);
  }, []);

  const dismissEmptyState = useCallback(() => {
    setHasDismissedEmptyState(true);
  }, []);

  const value = useMemo<BrandStudioContextType>(
    () => ({
      editMode,
      selectedItem,
      openEdit,
      closeSheet,
      isSmartFillOpen,
      smartFillMode,
      openSmartFill,
      closeSmartFill,
      hasDismissedEmptyState,
      dismissEmptyState,
    }),
    [
      editMode,
      selectedItem,
      openEdit,
      closeSheet,
      isSmartFillOpen,
      smartFillMode,
      openSmartFill,
      closeSmartFill,
      hasDismissedEmptyState,
      dismissEmptyState,
    ],
  );

  return <BrandStudioContext.Provider value={value}>{children}</BrandStudioContext.Provider>;
}

export function useBrandStudio() {
  const ctx = useContext(BrandStudioContext);
  if (!ctx) {
    throw new Error("useBrandStudio must be used within BrandStudioProvider");
  }
  return ctx;
}
