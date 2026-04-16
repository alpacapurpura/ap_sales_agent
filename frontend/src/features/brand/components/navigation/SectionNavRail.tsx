"use client";

import { ChevronRight, type LucideIcon } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";

import type { ValidationStatus } from "../../utils/brand-validation";

export interface SectionNavItem {
  id: string;
  label: string;
  icon: LucideIcon;
  scrollTo: string;
  score: number;
  status: ValidationStatus;
  missingFields: string[];
}

interface SectionNavRailProps {
  title: string;
  subtitle: string;
  items: SectionNavItem[];
  activeSection: string;
  onNavigate: (scrollTo: string) => void;
  className?: string;
}

export function SectionNavRail({
  title,
  subtitle,
  items,
  activeSection,
  onNavigate,
  className,
}: SectionNavRailProps) {
  const [isHovered, setIsHovered] = useState(false);

  const overallScore =
    items.length > 0 ? Math.round(items.reduce((a, i) => a + i.score, 0) / items.length) : 0;

  return (
    <div
      className={cn(
        "hidden md:flex flex-col h-full border-r bg-background transition-all duration-300 ease-in-out group overflow-hidden sticky top-0",
        isHovered ? "w-64 shadow-xl" : "w-16",
        className,
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* HEADER: Section Health Ring */}
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
                overallScore === 100 ? "text-green-500" : "text-primary",
              )}
              strokeDasharray={`${overallScore}, 100`}
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="currentColor"
              strokeWidth="4"
            />
          </svg>
          <span className="absolute text-[10px] font-bold">{overallScore}</span>
        </div>

        <div
          className={cn(
            "absolute left-16 right-0 px-4 transition-opacity duration-300",
            isHovered ? "opacity-100 delay-100" : "opacity-0 pointer-events-none",
          )}
        >
          <p className="text-sm font-bold truncate">{title}</p>
          <p className="text-xs text-muted-foreground truncate">{subtitle}</p>
        </div>
      </div>

      {/* BODY: Navigation Items */}
      <nav className="flex-1 py-4 flex flex-col gap-1 overflow-y-auto overflow-x-hidden scrollbar-hide">
        {items.map((item) => {
          const isActive = activeSection === item.scrollTo;
          const isComplete = item.status === "complete";
          const isEmpty = item.status === "empty";

          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.scrollTo)}
              className={cn(
                "relative flex items-center h-10 w-full transition-all group/item px-4",
                isActive
                  ? "bg-primary/5 text-primary"
                  : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
              )}
            >
              {isActive && (
                <div className="absolute left-0 top-2 bottom-2 w-1 bg-primary rounded-r-full" />
              )}

              <div className="relative shrink-0 flex items-center justify-center w-8 h-8">
                <item.icon
                  className={cn(
                    "h-4 w-4 transition-transform group-hover/item:scale-110",
                    isActive && "text-primary",
                  )}
                />
                <div
                  className={cn(
                    "absolute top-1 right-1 h-1.5 w-1.5 rounded-full border border-background ring-1 ring-background",
                    isComplete
                      ? "bg-green-500"
                      : isEmpty
                        ? "bg-muted-foreground/30"
                        : "bg-amber-500",
                  )}
                />
              </div>

              <div
                className={cn(
                  "ml-4 flex-1 text-left transition-opacity duration-300 flex items-center justify-between",
                  isHovered ? "opacity-100 delay-75" : "opacity-0 w-0 overflow-hidden",
                )}
              >
                <span className="font-medium text-sm whitespace-nowrap">{item.label}</span>
                <span
                  className={cn(
                    "text-[10px] px-1.5 rounded-full shrink-0 ml-2 font-medium",
                    isComplete
                      ? "bg-green-100 text-green-700"
                      : isEmpty
                        ? "bg-muted text-muted-foreground"
                        : "bg-amber-100 text-amber-700",
                  )}
                >
                  {item.score}%
                </span>
              </div>
            </button>
          );
        })}
      </nav>

      {/* FOOTER: Collapse Hint */}
      <div className="h-12 border-t flex items-center justify-center text-muted-foreground shrink-0">
        <ChevronRight
          className={cn(
            "h-4 w-4 transition-transform duration-300",
            isHovered ? "rotate-180" : "rotate-0",
          )}
        />
      </div>
    </div>
  );
}
