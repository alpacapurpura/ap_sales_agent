"use client";

import { useState } from "react";
import { Lead } from "@/features/sales/types";
import { PipelineBoard } from "@/features/sales/components/organisms/PipelineBoard";
import { LeadCommandCenter } from "@/features/sales/components/organisms/LeadCommandCenter";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { MOCK_LEADS } from "@/features/sales/mocks/leads";

export default function SalesMockPage() {
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  if (selectedLead) {
    return (
      <div className="h-[calc(100vh-4rem)] w-full bg-background animate-in fade-in slide-in-from-right-10 duration-300">
        <LeadCommandCenter 
          lead={selectedLead} 
          onBack={() => setSelectedLead(null)} 
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] w-full">
      <div className="flex items-center justify-between px-6 py-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Sales Pipeline</h1>
          <p className="text-muted-foreground text-sm">
            Gestiona tus oportunidades y leads en tiempo real.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Button>
            <Plus className="mr-2 h-4 w-4" /> Nuevo Lead
          </Button>
        </div>
      </div>
      
      <div className="flex-1 overflow-hidden p-6 bg-muted/10">
        <PipelineBoard 
          leads={MOCK_LEADS} 
          onLeadClick={(lead) => setSelectedLead(lead)} 
        />
      </div>
    </div>
  );
}
