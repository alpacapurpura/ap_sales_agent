"use client";

import { Search, Plus } from "lucide-react";
import { useState, useCallback, useDeferredValue } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { LadderProgressBar } from "@/features/offer-studio/components/dashboard/ladder-progress-bar";
import { OfferStudioDashboard } from "@/features/offer-studio/components/dashboard/offer-studio-dashboard";

import type { OfferValueLevel } from "@/features/offer-studio/types";

interface LadderData {
  filledGroups: Set<OfferValueLevel>;
  score: string;
  percentage: number;
}

export function OfferStudioView() {
  const [searchQuery, setSearchQuery] = useState("");
  const deferredQuery = useDeferredValue(searchQuery);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [ladderData, setLadderData] = useState<LadderData | null>(null);

  const handleLadderComputed = useCallback((data: LadderData) => {
    setLadderData((prev) => {
      if (
        prev?.percentage === data.percentage &&
        prev.score === data.score &&
        prev.filledGroups.size === data.filledGroups.size
      ) {
        return prev;
      }
      return data;
    });
  }, []);

  return (
    <div className="h-full flex flex-col gap-5 p-6 md:p-8">
      {/* Row 1: Title + Actions */}
      <div className="flex items-center justify-between gap-4 flex-none">
        <h2 className="text-2xl font-bold tracking-tight shrink-0">Offer Studio</h2>

        <div className="flex items-center gap-2.5">
          {/* Search */}
          <div className="relative w-full max-w-[280px]">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Buscar ofertas..."
              className="pl-9 h-9 bg-background/50 focus:bg-background transition-colors"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <Button
            variant="default"
            size="sm"
            className="bg-white text-black hover:bg-white/90 border border-input shadow-sm shrink-0 font-medium h-9"
            onClick={() => setIsCreateOpen(true)}
          >
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            Nueva Oferta
          </Button>
        </div>
      </div>

      {/* Row 2: Ladder Progress — full width, contextual */}
      {ladderData && !deferredQuery && (
        <LadderProgressBar
          filledGroups={ladderData.filledGroups}
          score={ladderData.score}
          percentage={ladderData.percentage}
        />
      )}

      <Separator className="flex-none" />

      {/* Content */}
      <div className="flex-1 overflow-auto pr-4 -mr-4 mt-4">
        <OfferStudioDashboard
          searchQuery={deferredQuery}
          externalCreateTrigger={isCreateOpen}
          onCreateTriggerHandled={() => setIsCreateOpen(false)}
          onLadderComputed={handleLadderComputed}
        />
      </div>
    </div>
  );
}
