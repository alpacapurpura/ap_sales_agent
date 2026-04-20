import { Check, AlertCircle, Circle, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import React, { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";
import { SECTION_REGISTRY } from "@/features/offer-studio/config/offer-builder-config";
import { useSectionsForArchetype } from "@/features/offer-studio/hooks/use-sections-for-archetype";
import { getOfferHealth } from "@/features/offer-studio/utils/offer-health";
import { cn } from "@/lib/utils";

import type { Offer } from "@/features/offer-studio/types";

interface OfferNavRailProps {
  offer: Offer;
  activeSection: string;
  onNavigate: (sectionId: string) => void;
  className?: string;
}

function StatusDot({ isComplete, hasError }: { isComplete: boolean; hasError: boolean }) {
  if (isComplete)
    return <div className="h-2 w-2 bg-green-500 rounded-full ring-1 ring-background" />;
  if (hasError) return <div className="h-2 w-2 bg-amber-500 rounded-full ring-1 ring-background" />;
  return null;
}

function StatusIcon({ isComplete, hasError }: { isComplete: boolean; hasError: boolean }) {
  if (isComplete) return <Check className="h-4 w-4 text-green-500" />;
  if (hasError) return <AlertCircle className="h-4 w-4 text-amber-500" />;
  return <Circle className="h-3 w-3 text-muted-foreground/30" />;
}

interface NavSectionItemProps {
  sectionId: string;
  health: ReturnType<typeof getOfferHealth>;
  activeSection: string;
  isCollapsed: boolean;
  onNavigate: (sectionId: string) => void;
}

function NavSectionItem({
  sectionId,
  health,
  activeSection,
  isCollapsed,
  onNavigate,
}: NavSectionItemProps) {
  const config = SECTION_REGISTRY[sectionId];
  if (!config) return null;

  const Icon = config.icon;
  const sectionHealth = health.sections[sectionId];
  const isComplete = sectionHealth?.status === "complete";
  const isActive = activeSection === sectionId;
  const hasError = sectionHealth?.status === "incomplete";

  return (
    <TooltipProvider>
      <Tooltip delayDuration={300}>
        <TooltipTrigger asChild>
          <Button
            variant={isActive ? "secondary" : "ghost"}
            className={cn(
              "w-full h-10 mb-1 font-normal transition-all",
              isActive && "bg-secondary font-medium text-foreground",
              !isActive && "text-muted-foreground hover:text-foreground hover:bg-muted/50",
              isCollapsed ? "justify-center px-0" : "justify-start pl-10 relative",
            )}
            onClick={() => onNavigate(sectionId)}
          >
            {isCollapsed ? (
              <div className="relative">
                <Icon className="h-5 w-5" />
                <div className="absolute -top-1 -right-1">
                  <StatusDot isComplete={isComplete} hasError={hasError} />
                </div>
              </div>
            ) : (
              <>
                <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center justify-center">
                  <StatusIcon isComplete={isComplete} hasError={hasError} />
                </div>
                <div className="flex items-center gap-2 truncate">
                  <span className="truncate">{config.title}</span>
                </div>
                {isActive && (
                  <div className="absolute right-0 top-0 bottom-0 w-1 bg-primary rounded-l-md" />
                )}
              </>
            )}
          </Button>
        </TooltipTrigger>
        {(isCollapsed || hasError) && (
          <TooltipContent side="right" className="text-xs max-w-[200px] flex flex-col gap-1">
            <p className="font-semibold">{config.title}</p>
            {hasError && sectionHealth.message && (
              <p className="text-amber-500">{sectionHealth.message}</p>
            )}
          </TooltipContent>
        )}
      </Tooltip>
    </TooltipProvider>
  );
}

export function OfferNavRail({ offer, activeSection, onNavigate, className }: OfferNavRailProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const sectionsMeta = useSectionsForArchetype(offer.archetype);
  const sections = useMemo(() => sectionsMeta?.map((s) => s.key) ?? [], [sectionsMeta]);
  const health = useMemo(() => getOfferHealth(offer, sections), [offer, sections]);

  const handleNavigate = (sectionId: string) => {
    onNavigate(sectionId);
    // Scroll to section logic
    const element = document.getElementById(sectionId);
    if (element) {
      // Find the main scroll container
      const container = document.getElementById("offer-editor-main");
      if (container) {
        const top = element.offsetTop - 20; // 20px padding
        container.scrollTo({ top, behavior: "smooth" });
      } else {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  };

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-muted/10 border-r transition-all duration-300 ease-in-out",
        isCollapsed ? "w-[60px]" : "w-[280px]",
        className,
      )}
    >
      {/* Header with Health Score */}
      <div
        className={cn(
          "border-b bg-background/50 backdrop-blur-sm sticky top-0 z-10 flex flex-col justify-center",
          isCollapsed ? "p-2 items-center h-16" : "p-4",
        )}
      >
        {!isCollapsed ? (
          <>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Progreso
              </span>
              <span
                className={cn(
                  "text-sm font-bold tabular-nums",
                  health.completionPercentage === 100 ? "text-green-600" : "text-primary",
                )}
              >
                {health.completionPercentage}%
              </span>
            </div>
            <div className="h-2 w-full bg-secondary/50 rounded-full overflow-hidden">
              <div
                className={cn(
                  "h-full transition-all duration-500 ease-in-out",
                  health.completionPercentage === 100 ? "bg-green-500" : "bg-primary",
                )}
                style={{ width: `${health.completionPercentage}%` }}
              />
            </div>
          </>
        ) : (
          <div className="relative h-10 w-10 flex items-center justify-center">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-secondary"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className={health.completionPercentage === 100 ? "text-green-500" : "text-primary"}
                strokeDasharray={`${health.completionPercentage}, 100`}
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="currentColor"
                strokeWidth="4"
              />
            </svg>
            <span className="absolute text-[10px] font-bold">{health.completionPercentage}%</span>
          </div>
        )}
      </div>

      <ScrollArea className="flex-1 py-4">
        <div className={cn("space-y-1", isCollapsed ? "px-2" : "px-3")}>
          {sections.map((sectionId) => (
            <NavSectionItem
              key={sectionId}
              sectionId={sectionId}
              health={health}
              activeSection={activeSection}
              isCollapsed={isCollapsed}
              onNavigate={handleNavigate}
            />
          ))}
        </div>
      </ScrollArea>

      <div className="p-2 border-t bg-background/50 flex justify-center">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          {isCollapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}
