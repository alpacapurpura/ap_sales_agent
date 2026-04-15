import React, { createContext, useContext } from "react";

import type { LandingPageTheme } from "@/features/offer-studio/components/landing/types/schema";

const LandingThemeContext = createContext<LandingPageTheme | null>(null);

export function LandingThemeProvider({
  children,
  theme,
}: {
  children: React.ReactNode;
  theme: LandingPageTheme;
}) {
  return <LandingThemeContext.Provider value={theme}>{children}</LandingThemeContext.Provider>;
}

export function useLandingTheme() {
  const context = useContext(LandingThemeContext);
  if (!context) {
    throw new Error("useLandingTheme must be used within a LandingThemeProvider");
  }
  return context;
}
