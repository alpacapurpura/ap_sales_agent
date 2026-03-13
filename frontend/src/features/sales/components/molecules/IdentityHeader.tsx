import { Lead } from "../../types";
import { LeadAvatar } from "../atoms/LeadAvatar";
import { TemperatureBadge } from "../atoms/TemperatureBadge";
import { ScoreRing } from "../atoms/ScoreRing";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  ArrowLeft, 
  Linkedin, 
  Globe, 
  MapPin, 
  Calendar,
  MoreVertical,
  Edit
} from "lucide-react";
import { Separator } from "@/components/ui/separator";

interface IdentityHeaderProps {
  lead: Lead;
  onBack?: () => void;
}

export function IdentityHeader({ lead, onBack }: IdentityHeaderProps) {
  const customer = lead.customer;
  const fullName = customer?.full_name ?? lead.name ?? "Cliente";

  return (
    <div className="w-full bg-background border-b p-6">
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-4">
          {onBack && (
            <Button variant="ghost" size="icon" onClick={onBack} className="mr-2">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          )}
          <LeadAvatar
            src={customer?.avatar_url}
            initials={fullName.slice(0, 2).toUpperCase()}
            className="h-20 w-20 border-4 border-muted"
          />
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold tracking-tight">{fullName}</h1>
              <TemperatureBadge temperature={lead.temperature} />
            </div>
            <p className="text-muted-foreground text-lg flex items-center gap-2">
              {customer?.social_handle || "Cliente Potencial"}
            </p>
            <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
              {customer?.email && (
                <div className="flex items-center gap-1">
                  <span className="text-foreground/80">{customer.email}</span>
                </div>
              )}
              {customer?.phone && (
                <div className="flex items-center gap-1">
                  <span className="text-foreground/80">{customer.phone}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex flex-col items-end">
            <span className="text-sm font-medium text-muted-foreground mb-1">Lead Score</span>
            <ScoreRing score={lead.score} size={56} strokeWidth={4} />
          </div>
          <div className="flex gap-2">
             <Button variant="outline">
                <Edit className="h-4 w-4 mr-2" />
                Editar
             </Button>
             <Button variant="ghost" size="icon">
                <MoreVertical className="h-5 w-5" />
             </Button>
          </div>
        </div>
      </div>

      <Separator className="my-4" />

      <div className="flex items-center justify-between text-sm">
        <div className="flex gap-6">
           <div className="flex items-center gap-2 text-muted-foreground hover:text-foreground cursor-pointer transition-colors">
              <Linkedin className="h-4 w-4" />
              <span>LinkedIn Profile</span>
           </div>
           <div className="flex items-center gap-2 text-muted-foreground hover:text-foreground cursor-pointer transition-colors">
              <Globe className="h-4 w-4" />
              <span>Website</span>
           </div>
           <div className="flex items-center gap-2 text-muted-foreground">
              <MapPin className="h-4 w-4" />
              <span>Madrid, España</span>
           </div>
        </div>
        
        <div className="flex items-center gap-2 text-muted-foreground">
           <Calendar className="h-4 w-4" />
           <span>Creado: 12 Feb 2024</span>
        </div>
      </div>
    </div>
  );
}
