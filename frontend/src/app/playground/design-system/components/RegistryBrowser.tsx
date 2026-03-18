"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import type { AtomicLevel, ComponentEntry } from "@/lib/design-system/types";
import { ComponentCard } from "./ComponentCard";

interface RegistryBrowserProps {
  components: ComponentEntry[];
  activeLevel: AtomicLevel | "all";
  onLevelChange: (level: AtomicLevel | "all") => void;
  highlightedComponent: string | null;
}

const LEVEL_FILTERS: { key: AtomicLevel | "all"; label: string; color: string }[] = [
  { key: "all", label: "All", color: "" },
  { key: "atom", label: "Atoms", color: "data-[active=true]:bg-blue-100 data-[active=true]:text-blue-800 dark:data-[active=true]:bg-blue-900 dark:data-[active=true]:text-blue-200" },
  { key: "molecule", label: "Molecules", color: "data-[active=true]:bg-green-100 data-[active=true]:text-green-800 dark:data-[active=true]:bg-green-900 dark:data-[active=true]:text-green-200" },
  { key: "organism", label: "Organisms", color: "data-[active=true]:bg-purple-100 data-[active=true]:text-purple-800 dark:data-[active=true]:bg-purple-900 dark:data-[active=true]:text-purple-200" },
];

export function RegistryBrowser({
  components,
  activeLevel,
  onLevelChange,
  highlightedComponent,
}: RegistryBrowserProps) {
  const [search, setSearch] = useState("");

  const filtered = components.filter((c) => {
    const matchesLevel = activeLevel === "all" || c.atomicLevel === activeLevel;
    const matchesSearch =
      !search ||
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.description.toLowerCase().includes(search.toLowerCase()) ||
      (c.featureSlice && c.featureSlice.toLowerCase().includes(search.toLowerCase()));
    return matchesLevel && matchesSearch;
  });

  // Group by atomic level for display
  const grouped: { level: AtomicLevel; entries: ComponentEntry[] }[] = [];
  const levels: AtomicLevel[] = ["atom", "molecule", "organism"];
  for (const level of levels) {
    const entries = filtered.filter((c) => c.atomicLevel === level);
    if (entries.length > 0) {
      grouped.push({ level, entries });
    }
  }

  return (
    <div className="flex-1 min-w-0">
      {/* Filter bar */}
      <div className="sticky top-0 bg-background/95 backdrop-blur-sm z-10 border-b px-6 py-3">
        <div className="flex items-center gap-3">
          <Input
            placeholder="Search components..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-xs h-9"
          />
          <div className="flex gap-1">
            {LEVEL_FILTERS.map((f) => (
              <button
                key={f.key}
                data-active={activeLevel === f.key}
                onClick={() => onLevelChange(f.key)}
                className={cn(
                  "px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
                  "hover:bg-accent",
                  activeLevel === f.key
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground",
                  f.color
                )}
              >
                {f.label}
              </button>
            ))}
          </div>
          <span className="text-xs text-muted-foreground ml-auto">
            {filtered.length} component{filtered.length !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Component grid */}
      <div className="p-6 space-y-8">
        {grouped.map(({ level, entries }) => (
          <section key={level}>
            <h2 className="text-xl font-bold capitalize mb-4 flex items-center gap-2">
              <span
                className={cn(
                  "w-3 h-3 rounded-full",
                  level === "atom" && "bg-blue-500",
                  level === "molecule" && "bg-green-500",
                  level === "organism" && "bg-purple-500"
                )}
              />
              {level}s
              <span className="text-sm font-normal text-muted-foreground">
                ({entries.length})
              </span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {entries.map((comp) => (
                <div
                  key={comp.filePath}
                  id={`component-${comp.name}`}
                  className={cn(
                    "transition-all",
                    highlightedComponent === comp.name &&
                      "ring-2 ring-primary rounded-lg"
                  )}
                >
                  <ComponentCard component={comp} />
                </div>
              ))}
            </div>
          </section>
        ))}
        {grouped.length === 0 && (
          <div className="text-center py-20 text-muted-foreground">
            <p className="text-lg">No components found</p>
            <p className="text-sm mt-1">Try adjusting your search or filter</p>
          </div>
        )}
      </div>
    </div>
  );
}
