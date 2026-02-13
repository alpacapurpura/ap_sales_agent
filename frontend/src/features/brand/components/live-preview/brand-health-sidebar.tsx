"use client";

import { BrandSettings } from "@/lib/api/brand";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, Circle, Trophy } from "lucide-react";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { avatarApi } from "@/lib/api/avatar";
import { galleryApi } from "@/lib/api/gallery";

interface BrandHealthSidebarProps {
  settings: BrandSettings;
}

export function BrandHealthSidebar({ settings }: BrandHealthSidebarProps) {
  const { getToken } = useAuth();

  // Fetch avatars for health check
  const { data: avatars } = useQuery({
    queryKey: ["avatars"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      return avatarApi.listAvatars(token, "GLOBAL");
    },
    initialData: [],
  });

  // Fetch gallery for health check
  const { data: galleryImages } = useQuery({
    queryKey: ["gallery"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      return galleryApi.list(token);
    },
    initialData: [],
  });

  // Groups Definition
  const corporateChecks = [
    { label: "Identidad Básica", valid: !!settings.identity.brand_name && !!settings.identity.industry, id: "section-identity" },
    { label: "El Origen (Historia)", valid: !!settings.story?.origin_story, id: "section-story" },
    { label: "Contacto & Legal", valid: !!settings.contact.support_email, id: "section-contact" },
  ];

  const brandbookChecks = [
    { label: "Estrategia (UVP)", valid: !!settings.strategy?.unique_value_proposition, id: "section-strategy" },
    { label: "Metodología", valid: (settings.strategy?.methodology_pillars?.length ?? 0) > 0, id: "section-methodology" },
    { label: "Avatares (Target)", valid: (avatars?.length ?? 0) > 0, id: "section-avatars" },
    { label: "Voz & Personalidad", valid: !!settings.identity.language && !!settings.identity.timezone, id: "section-voice" },
  ];

  const assetChecks = [
    { label: "Identidad Visual", valid: !!settings.identity.logo_url && !!settings.identity.website, id: "section-visuals" },
    { label: "Equipo (Key Figures)", valid: (settings.team?.length ?? 0) > 0, id: "section-team" },
    { label: "Autoridad (Vault)", valid: (settings.authority_vault?.length ?? 0) > 0, id: "section-authority" },
    { label: "Galería", valid: (galleryImages?.length ?? 0) > 0, id: "section-gallery" },
  ];

  // Calculate Global Score
  const allChecks = [...corporateChecks, ...brandbookChecks, ...assetChecks];
  const completed = allChecks.filter(c => c.valid).length;
  const total = allChecks.length;
  const progress = (completed / total) * 100;

  const handleScroll = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const NavItem = ({ item }: { item: { label: string; valid: boolean; id: string } }) => (
    <button 
        onClick={() => handleScroll(item.id)}
        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors hover:bg-muted/50 text-left group"
    >
        {item.valid ? (
            <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
        ) : (
            <Circle className="h-4 w-4 text-muted-foreground shrink-0 group-hover:text-primary transition-colors" />
        )}
        <span className={cn("transition-colors", item.valid ? "text-foreground font-medium" : "text-muted-foreground group-hover:text-foreground")}>
            {item.label}
        </span>
    </button>
  );

  return (
    <div className="space-y-8">
      {/* Score Card */}
      <div className="bg-card border rounded-xl p-6 text-card-foreground shadow-sm">
        <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-lg">Brand Health</h3>
            <Trophy className={cn("h-5 w-5", progress === 100 ? "text-yellow-400" : "text-muted-foreground")} />
        </div>
        
        <div className="mb-4">
            <div className="flex items-end gap-2 mb-2">
                <span className="text-4xl font-bold">{Math.round(progress)}%</span>
                <span className="text-muted-foreground text-sm mb-1">completado</span>
            </div>
            <Progress value={progress} className="h-2 bg-muted" indicatorClassName={progress === 100 ? "bg-green-500" : "bg-primary"} />
        </div>

        <p className="text-xs text-muted-foreground">
            {progress < 100 
                ? "Completa tu perfil para que la IA tenga más contexto." 
                : "¡Tu marca está lista para escalar!"}
        </p>
      </div>

      {/* Index Groups */}
      <div className="space-y-6">
        
        {/* Group 1: Corporate */}
        <div className="space-y-2">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2 flex items-center gap-2">
                Información Corporativa
            </h4>
            <nav className="space-y-1">
                {corporateChecks.map((check, i) => (
                    <NavItem key={i} item={check} />
                ))}
            </nav>
        </div>

        {/* Group 2: Brandbook */}
        <div className="space-y-2">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2 flex items-center gap-2">
                Brandbook
            </h4>
            <nav className="space-y-1">
                {brandbookChecks.map((check, i) => (
                    <NavItem key={i} item={check} />
                ))}
            </nav>
        </div>

        {/* Group 3: Assets */}
        <div className="space-y-2">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2 flex items-center gap-2">
                Activos de la Marca
            </h4>
            <nav className="space-y-1">
                {assetChecks.map((check, i) => (
                    <NavItem key={i} item={check} />
                ))}
            </nav>
        </div>

      </div>
    </div>
  );
}
