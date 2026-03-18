"use client";

import { useState } from "react";
import { COMPONENT_REGISTRY, DESIGN_TOKENS, getStats } from "@/lib/design-system/registry";
import type { AtomicLevel } from "@/lib/design-system/types";
import { Sidebar } from "./components/Sidebar";
import { RegistryBrowser } from "./components/RegistryBrowser";
import { TokenShowcase } from "./components/TokenShowcase";

export default function DesignSystemPlayground() {
  const [activeLevel, setActiveLevel] = useState<AtomicLevel | "all">("all");
  const [highlightedComponent, setHighlightedComponent] = useState<string | null>(null);

  const stats = getStats();

  const handleComponentClick = (name: string) => {
    setHighlightedComponent(name);
    // Scroll to the component
    const el = document.getElementById(`component-${name}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    // Clear highlight after 2 seconds
    setTimeout(() => setHighlightedComponent(null), 2000);
  };

  const showTokens = activeLevel === "all" || activeLevel === "token";
  const showComponents = activeLevel !== "token";

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b px-6 py-4">
        <h1 className="text-2xl font-bold">Design System Playground</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {stats.total} components | {stats.atoms} atoms | {stats.molecules} molecules |{" "}
          {stats.organisms} organisms | {stats.withIssues} with issues
        </p>
      </div>

      {/* Main layout */}
      <div className="flex">
        <Sidebar
          components={COMPONENT_REGISTRY}
          activeLevel={activeLevel}
          onLevelChange={setActiveLevel}
          onComponentClick={handleComponentClick}
        />

        <main className="flex-1 min-w-0">
          {showTokens && (
            <div className="p-6 border-b">
              <TokenShowcase tokens={DESIGN_TOKENS} />
            </div>
          )}

          {showComponents && (
            <RegistryBrowser
              components={COMPONENT_REGISTRY}
              activeLevel={activeLevel}
              onLevelChange={setActiveLevel}
              highlightedComponent={highlightedComponent}
            />
          )}
        </main>
      </div>
    </div>
  );
}
