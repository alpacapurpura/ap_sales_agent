import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Lead } from "../../types";
import { LeadAvatar } from "../atoms/LeadAvatar";
import { ScoreRing } from "../atoms/ScoreRing";
import { TemperatureBadge } from "../atoms/TemperatureBadge";
import { ActionIcon } from "../atoms/ActionIcon";
import { MessageCircle, Phone, Mail, MoreHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";

interface LeadCardProps {
  lead: Lead;
  className?: string;
  onClick?: () => void;
}

export function LeadCard({ lead, className, onClick }: LeadCardProps) {
  const customer = lead.customer;
  const fullName = customer?.full_name ?? lead.name ?? "Cliente";

  return (
    <Card
      className={cn(
        "hover:shadow-md transition-shadow cursor-pointer group border-l-4",
        lead.temperature === 'hot' ? 'border-l-red-500' :
        lead.temperature === 'warm' ? 'border-l-orange-400' : 'border-l-blue-400',
        className
      )}
      onClick={onClick}
    >
      <CardHeader className="p-4 flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-3">
          <LeadAvatar
            src={customer?.avatar_url}
            initials={fullName.slice(0, 2).toUpperCase()}
            alt={fullName}
          />
          <div className="flex flex-col">
            <h4 className="text-sm font-semibold leading-none truncate max-w-[140px]" title={fullName}>
              {fullName}
            </h4>
            <span className="text-xs text-muted-foreground truncate max-w-[140px]">
              {customer?.social_handle || "Cliente Potencial"}
            </span>
          </div>
        </div>
        <ScoreRing score={lead.score} size={36} strokeWidth={3} />
      </CardHeader>

      <CardContent className="p-4 pt-2 pb-3">
        <div className="flex justify-between items-center text-xs text-muted-foreground mb-3">
          <TemperatureBadge temperature={lead.temperature} />
          <span>{"Reciente"}</span>
        </div>
      </CardContent>

      <CardFooter className="p-2 bg-muted/20 flex justify-between items-center opacity-0 group-hover:opacity-100 transition-opacity">
        <div className="flex gap-1">
          {customer?.phone && <ActionIcon icon={MessageCircle} label="WhatsApp" className="h-7 w-7" />}
          {customer?.phone && <ActionIcon icon={Phone} label="Llamar" className="h-7 w-7" />}
          {customer?.email && <ActionIcon icon={Mail} label="Email" className="h-7 w-7" />}
        </div>
        <ActionIcon icon={MoreHorizontal} label="Más opciones" className="h-7 w-7" />
      </CardFooter>
    </Card>
  );
}
