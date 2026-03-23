"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  Building2, Target, BookOpen, Palette, Award, MessageSquare, Contact,
  ChevronRight, UserSearch, Crosshair, Trophy,
} from "lucide-react";
import { BrandSettings } from "@/features/brand/types";
import {
  getChapterHealthMap,
  getBrandHealth,
  ChapterHealth,
} from "../../utils/brand-validation";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

const CHAPTER_ICONS: Record<string, typeof Building2> = {
  origen: Building2,
  diferenciacion: Trophy,
  mercado: Crosshair,
  personalidad: Target,
  historia: BookOpen,
  voz: MessageSquare,
  publico: UserSearch,
  imagen: Palette,
  credibilidad: Award,
  contacto: Contact,
};

interface BrandNavRailProps {
  settings: BrandSettings;
  activeSection: string;
  onNavigate: (sectionId: string) => void;
  className?: string;
}

export function BrandNavRail({ settings, activeSection, onNavigate, className }: BrandNavRailProps) {
  const [isHovered, setIsHovered] = useState(false);
  const health = getBrandHealth(settings);
  const chapters = getChapterHealthMap(settings);

  // Separate main chapters (first 9) and footer (contacto)
  const mainChapters = chapters.filter(c => c.id !== "contacto");
  const contactChapter = chapters.find(c => c.id === "contacto")!;

  const renderItem = (chapter: ChapterHealth) => {
    const Icon = CHAPTER_ICONS[chapter.id] ?? Building2;
    const isActive = activeSection === chapter.scrollTo;
    const isComplete = chapter.status === "complete";
    const isEmpty = chapter.status === "empty";

    return (
      <Tooltip key={chapter.id}>
        <TooltipTrigger asChild>
          <button
            onClick={() => onNavigate(chapter.scrollTo)}
            className={cn(
              "relative flex items-center h-10 w-full transition-all group/item px-4",
              isActive ? "bg-primary/5 text-primary" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
            )}
          >
            {isActive && (
              <div className="absolute left-0 top-2 bottom-2 w-1 bg-primary rounded-r-full" />
            )}

            <div className="relative shrink-0 flex items-center justify-center w-8 h-8">
              <Icon className={cn("h-4 w-4 transition-transform group-hover/item:scale-110", isActive && "text-primary")} />
              <div className={cn(
                "absolute top-1 right-1 h-1.5 w-1.5 rounded-full border border-background ring-1 ring-background",
                isComplete ? "bg-green-500" : isEmpty ? "bg-muted-foreground/30" : "bg-amber-500"
              )} />
            </div>

            <div className={cn(
              "ml-4 flex-1 text-left transition-opacity duration-300 flex items-center justify-between",
              isHovered ? "opacity-100 delay-75" : "opacity-0 w-0 overflow-hidden"
            )}>
              <span className="font-medium text-sm whitespace-nowrap">{chapter.label}</span>
              <span className={cn(
                "text-[10px] px-1.5 rounded-full shrink-0 ml-2 font-medium",
                isComplete ? "bg-green-100 text-green-700" :
                isEmpty ? "bg-muted text-muted-foreground" :
                "bg-amber-100 text-amber-700"
              )}>
                {chapter.score}%
              </span>
            </div>
          </button>
        </TooltipTrigger>
        {!isHovered && (
          <TooltipContent side="right" className="flex flex-col items-start gap-1 p-2 max-w-[200px]">
            <div className="flex items-center gap-2 w-full justify-between">
              <span className="font-semibold">{chapter.label}</span>
              <span className={cn(
                "text-[10px] px-1.5 rounded-full shrink-0",
                isComplete ? "bg-green-100 text-green-700" :
                isEmpty ? "bg-muted text-muted-foreground" :
                "bg-amber-100 text-amber-700"
              )}>
                {chapter.score}%
              </span>
            </div>
            {!isComplete && chapter.missingFields.length > 0 && (
              <ul className="text-[10px] text-muted-foreground list-disc pl-3 space-y-0.5 mt-1 w-full">
                {chapter.missingFields.slice(0, 4).map((field, i) => (
                  <li key={i} className="truncate">{field}</li>
                ))}
                {chapter.missingFields.length > 4 && (
                  <li className="list-none pt-0.5 text-[9px] opacity-70">
                    +{chapter.missingFields.length - 4} más...
                  </li>
                )}
              </ul>
            )}
          </TooltipContent>
        )}
      </Tooltip>
    );
  };

  return (
    <div
      className={cn(
        "hidden md:flex flex-col h-full border-r bg-background transition-all duration-300 ease-in-out group overflow-hidden sticky top-0",
        isHovered ? "w-64 shadow-xl" : "w-16",
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* HEADER: Health Ring */}
      <div className="h-20 flex items-center justify-start pl-3 border-b relative shrink-0">
        <div className="relative flex items-center justify-center w-10 h-10">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
            <path
              className="text-muted/20"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className={cn(
                "transition-all duration-1000 ease-out",
                health === 100 ? "text-green-500" : "text-primary"
              )}
              strokeDasharray={`${health}, 100`}
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="currentColor"
              strokeWidth="4"
            />
          </svg>
          <span className="absolute text-[10px] font-bold">{health}</span>
        </div>

        <div className={cn(
          "absolute left-16 right-0 px-4 transition-opacity duration-300",
          isHovered ? "opacity-100 delay-100" : "opacity-0 pointer-events-none"
        )}>
          <p className="text-sm font-bold truncate">Brand Health</p>
          <p className="text-xs text-muted-foreground">{health}% Completado</p>
        </div>
      </div>

      {/* BODY: Navigation Items */}
      <nav className="flex-1 py-4 flex flex-col gap-1 overflow-y-auto overflow-x-hidden scrollbar-hide">
        <TooltipProvider delayDuration={0}>
          {mainChapters.map(renderItem)}

          {/* Footer: Contacto */}
          <div className="border-t border-muted/20 pt-3 mt-auto">
            {renderItem(contactChapter)}
          </div>
        </TooltipProvider>
      </nav>

      {/* FOOTER: Collapse Hint */}
      <div className="h-12 border-t flex items-center justify-center text-muted-foreground shrink-0">
        <ChevronRight className={cn(
          "h-4 w-4 transition-transform duration-300",
          isHovered ? "rotate-180" : "rotate-0"
        )} />
      </div>
    </div>
  );
}
