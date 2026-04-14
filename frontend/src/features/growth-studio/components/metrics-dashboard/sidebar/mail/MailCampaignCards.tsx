"use client";

import { cn } from "@/lib/utils";
import type { EmailCampaignSummary } from "../../../../types/mail-types";

interface MailCampaignCardsProps {
  bestCampaign: EmailCampaignSummary | null;
  worstCampaign: EmailCampaignSummary | null;
}

function formatSentCount(count: number): string {
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`;
  if (count >= 1_000) return `${(count / 1_000).toFixed(1)}k`;
  return count.toLocaleString("es-ES");
}

function formatDate(isoDate: string): string {
  try {
    return new Intl.DateTimeFormat("es-ES", {
      day: "numeric",
      month: "short",
    }).format(new Date(isoDate));
  } catch {
    return isoDate;
  }
}

interface CampaignCardProps {
  title: string;
  campaign: EmailCampaignSummary;
  borderColor: string;
}

function CampaignCard({ title, campaign, borderColor }: CampaignCardProps) {
  return (
    <div className={cn("rounded-lg border bg-card p-3 border-l-4", borderColor)}>
      <p className="text-[10px] text-muted-foreground uppercase tracking-widest mb-1.5">{title}</p>
      <p className="text-sm font-medium truncate" title={campaign.campaignName}>
        {campaign.campaignName}
      </p>
      <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Apertura</span>
          <span className="font-medium tabular-nums">{campaign.openRate}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">CTOR</span>
          <span className="font-medium tabular-nums">{campaign.clickToOpenRate}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Enviados</span>
          <span className="font-medium tabular-nums">
            {formatSentCount(campaign.sentCount)} env.
          </span>
        </div>
        {campaign.sentDate && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Fecha</span>
            <span className="font-medium">{formatDate(campaign.sentDate)}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export function MailCampaignCards({ bestCampaign, worstCampaign }: MailCampaignCardsProps) {
  if (!bestCampaign && !worstCampaign) return null;

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Campañas Destacadas
      </h4>
      <div className="space-y-2">
        {bestCampaign && (
          <CampaignCard
            title="Mejor Campaña"
            campaign={bestCampaign}
            borderColor="border-l-emerald-500"
          />
        )}
        {worstCampaign && (
          <CampaignCard
            title="Peor Campaña"
            campaign={worstCampaign}
            borderColor="border-l-red-500"
          />
        )}
      </div>
    </div>
  );
}
