"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

import { fetchCampaignAdSets } from "../../api/campaigns-api";

import { AdSetDetail } from "./AdSetDetail";

import type { Campaign, AdSet } from "../../types/campaigns";

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: "bg-green-500",
  PAUSED: "bg-yellow-500",
  DELETED: "bg-red-500",
  ARCHIVED: "bg-gray-400",
};

const OBJECTIVE_LABELS: Record<string, string> = {
  OUTCOME_SALES: "Ventas",
  OUTCOME_LEADS: "Leads",
  OUTCOME_TRAFFIC: "Tráfico",
  OUTCOME_AWARENESS: "Alcance",
  OUTCOME_ENGAGEMENT: "Interacción",
  OUTCOME_APP_PROMOTION: "App",
  CONVERSIONS: "Conversiones",
  MESSAGES: "Mensajes",
  LEAD_GENERATION: "Lead Gen",
};

interface CampaignCardProps {
  campaign: Campaign;
}

export function CampaignCard({ campaign }: CampaignCardProps) {
  const [expanded, setExpanded] = useState(false);
  const { getToken } = useAuth();

  const { data: adSets, isLoading: adSetsLoading } = useQuery<AdSet[]>({
    queryKey: ["campaigns", campaign.external_id, "adsets"],
    queryFn: async () => {
      const token = (await getToken()) ?? "";
      return fetchCampaignAdSets(token, campaign.external_id);
    },
    enabled: expanded,
  });

  const statusColor = STATUS_COLORS[campaign.effective_status ?? ""] ?? "bg-gray-400";
  const objectiveLabel = OBJECTIVE_LABELS[campaign.objective ?? ""] ?? campaign.objective ?? "—";

  const totalBudget = campaign.daily_budget ?? campaign.lifetime_budget ?? 0;
  const remaining = campaign.budget_remaining ?? 0;
  const budgetPercent = totalBudget > 0 ? Math.round((remaining / totalBudget) * 100) : 0;

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        <div
          className="flex items-center justify-between cursor-pointer"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-center gap-3 min-w-0">
            {expanded ? (
              <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
            )}
            <div className={cn("h-2.5 w-2.5 rounded-full shrink-0", statusColor)} />
            <span className="font-medium truncate">{campaign.name}</span>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Badge variant="secondary" className="text-xs">
              {objectiveLabel}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {campaign.ad_sets_count} conjuntos · {campaign.ads_count} anuncios
            </span>
          </div>
        </div>

        {/* Budget bar */}
        {totalBudget > 0 && (
          <div className="mt-2 ml-10">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
              <span>Presupuesto restante</span>
              <span>{budgetPercent}%</span>
            </div>
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full transition-all"
                style={{ width: `${Math.min(budgetPercent, 100)}%` }}
              />
            </div>
          </div>
        )}

        {/* Expanded: ad sets */}
        {expanded && (
          <div className="mt-4 ml-10 space-y-2">
            {adSetsLoading ? (
              <p className="text-sm text-muted-foreground">Cargando conjuntos...</p>
            ) : adSets && adSets.length > 0 ? (
              adSets.map((adSet) => <AdSetDetail key={adSet.external_id} adSet={adSet} />)
            ) : (
              <p className="text-sm text-muted-foreground">Sin conjuntos de anuncios</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
