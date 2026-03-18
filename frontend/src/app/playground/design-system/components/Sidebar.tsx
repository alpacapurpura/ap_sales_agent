"use client";

import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { AtomicLevel, ComponentEntry } from "@/lib/design-system/types";

interface SidebarProps {
  components: ComponentEntry[];
  activeLevel: AtomicLevel | "all";
  onLevelChange: (level: AtomicLevel | "all") => void;
  onComponentClick: (name: string) => void;
}

const LEVELS: { key: AtomicLevel | "all"; label: string; icon: string; color: string }[] = [
  { key: "all", label: "All", icon: "***", color: "text-foreground" },
  { key: "token", label: "Tokens", icon: "~", color: "text-amber-500" },
  { key: "atom", label: "Atoms", icon: ".", color: "text-blue-500" },
  { key: "molecule", label: "Molecules", icon: "::", color: "text-green-500" },
  { key: "organism", label: "Organisms", icon: "[=]", color: "text-purple-500" },
];

export function Sidebar({ components, activeLevel, onLevelChange, onComponentClick }: SidebarProps) {
  const grouped: Record<AtomicLevel, ComponentEntry[]> = {
    token: [],
    atom: components.filter((c) => c.atomicLevel === "atom"),
    molecule: components.filter((c) => c.atomicLevel === "molecule"),
    organism: components.filter((c) => c.atomicLevel === "organism"),
  };

  return (
    <aside className="w-[250px] shrink-0 border-r bg-muted/30 sticky top-0 h-screen">
      <div className="p-4 border-b">
        <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
          Hierarchy
        </h2>
      </div>
      <ScrollArea className="h-[calc(100vh-57px)]">
        <nav className="p-2 space-y-1">
          {LEVELS.map((level) => (
            <div key={level.key}>
              <button
                onClick={() => onLevelChange(level.key)}
                className={cn(
                  "w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  "hover:bg-accent hover:text-accent-foreground",
                  activeLevel === level.key
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground"
                )}
              >
                <span className={cn("mr-2 font-mono text-xs", level.color)}>
                  {level.icon}
                </span>
                {level.label}
                {level.key !== "all" && level.key !== "token" && (
                  <span className="ml-auto text-xs text-muted-foreground float-right">
                    {grouped[level.key]?.length ?? 0}
                  </span>
                )}
              </button>

              {/* Show component names when this level is active */}
              {activeLevel === level.key &&
                level.key !== "all" &&
                level.key !== "token" &&
                grouped[level.key] && (
                  <div className="ml-6 mt-1 space-y-0.5">
                    {grouped[level.key].map((comp) => (
                      <button
                        key={comp.filePath}
                        onClick={() => onComponentClick(comp.name)}
                        className="w-full text-left px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-accent/50 rounded truncate"
                        title={comp.name}
                      >
                        {comp.name}
                      </button>
                    ))}
                  </div>
                )}
            </div>
          ))}
        </nav>
      </ScrollArea>
    </aside>
  );
}
