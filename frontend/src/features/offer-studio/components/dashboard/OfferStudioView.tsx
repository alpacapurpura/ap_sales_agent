"use client";

import { useState, useCallback } from "react";
import { OfferStudioDashboard } from "@/features/offer-studio/components/dashboard/offer-studio-dashboard";
import { LadderProgressBar } from "@/features/offer-studio/components/dashboard/ladder-progress-bar";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Plus } from "lucide-react";
import { OfferValueLevel } from "@/features/offer-studio/types";

interface LadderData {
  filledGroups: Set<OfferValueLevel>;
  score: string;
  percentage: number;
}

export function OfferStudioView() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [ladderData, setLadderData] = useState<LadderData | null>(null);

  const handleLadderComputed = useCallback((data: LadderData) => {
    setLadderData(data);
  }, []);

  return (
    <div className="h-full flex flex-col space-y-6 p-8">
      {/* Header with Search and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 flex-none">
        <div className="space-y-0.5">
          <h2 className="text-2xl font-bold tracking-tight">Offer Studio</h2>
          <p className="text-muted-foreground hidden md:block">
            Centro de Comando de tu Escalera de Valor.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
           {/* Compact Ladder Progress in Header */}
           {ladderData && !searchQuery && (
             <LadderProgressBar
               filledGroups={ladderData.filledGroups}
               score={ladderData.score}
               percentage={ladderData.percentage}
               compact
             />
           )}

           {/* Search Bar */}
           <div className="relative w-full sm:w-[320px]">
             <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
             <Input
               type="search"
               placeholder="Buscar ofertas..."
               className="pl-9 bg-background/50 focus:bg-background transition-colors"
               value={searchQuery}
               onChange={(e) => setSearchQuery(e.target.value)}
             />
           </div>

           {/* New Offer Button - White Background as requested */}
           <Button
             variant="default"
             className="bg-white text-black hover:bg-white/90 border border-input shadow-sm shrink-0 font-medium"
             onClick={() => setIsCreateOpen(true)}
           >
             <Plus className="mr-2 h-4 w-4" />
             Nuevo Offer
           </Button>
        </div>
      </div>

      <Separator className="flex-none" />

      <div className="flex-1 overflow-auto pr-4 -mr-4">
         <OfferStudioDashboard
            searchQuery={searchQuery}
            externalCreateTrigger={isCreateOpen}
            onCreateTriggerHandled={() => setIsCreateOpen(false)}
            onLadderComputed={handleLadderComputed}
         />
      </div>
    </div>
  );
}
