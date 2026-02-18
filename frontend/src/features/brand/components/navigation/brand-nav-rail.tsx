"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { 
  Building2, Target, BookOpen, Palette, Users, Award, MessageSquare, Contact, CheckCircle2, AlertCircle, Circle, ChevronRight, Image as ImageIcon, MessageSquareQuote, Scale
} from "lucide-react";
import { BrandSettings } from "@/features/brand/types";
import { 
  validateIdentity, 
  validateStrategy, 
  validateStory, 
  validateVisuals, 
  validateTeam, 
  validateAuthority,
  validateContact,
  getBrandHealth,
  ValidationStatus
} from "../../utils/brand-validation";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface BrandNavRailProps {
  settings: BrandSettings;
  activeSection: string;
  onNavigate: (sectionId: string) => void;
  className?: string;
}

export function BrandNavRail({ settings, activeSection, onNavigate, className }: BrandNavRailProps) {
  const [isHovered, setIsHovered] = useState(false);
  const health = getBrandHealth(settings);

  // Grouped Navigation Items
  const navGroups = [
    {
      title: "I. ADN de Marca",
      items: [
        { id: "identity", label: "Identidad", icon: Building2, status: validateIdentity(settings.identity) },
        { id: "strategy", label: "Estrategia", icon: Target, status: validateStrategy(settings.strategy) },
        { id: "story", label: "Historia", icon: BookOpen, status: validateStory(settings.story) },
      ]
    },
    {
      title: "II. Universo Visual",
      items: [
        { id: "visuals", label: "Visuales", icon: Palette, status: validateVisuals(settings.visuals) },
        { id: "gallery", label: "Galería", icon: ImageIcon, status: { status: "optional", message: "Opcional" } as any }, // TODO: Add validator
      ]
    },
    {
      title: "III. Validación Social",
      items: [
        { id: "team", label: "Equipo", icon: Users, status: validateTeam(settings.team) },
        { id: "testimonials", label: "Testimonios", icon: MessageSquareQuote, status: { status: "optional", message: "Opcional" } as any }, // TODO: Add validator
        { id: "authority", label: "Autoridad", icon: Award, status: validateAuthority(settings.authority_vault) },
      ]
    },
    {
      title: "Operaciones",
      items: [
        { id: "contact", label: "Contacto", icon: Contact, status: validateContact(settings.contact) },
        { id: "legal", label: "Legales", icon: Scale, status: { status: "optional", message: "Revisar" } as any }
      ]
    }
  ];

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
        <div className="h-20 flex items-center justify-center border-b relative shrink-0">
            {/* ... same SVG code ... */}
            <div className="relative flex items-center justify-center w-10 h-10">
            {/* SVG Circle Progress */}
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
        
        {/* Expanded Header Info */}
        <div className={cn(
            "absolute left-16 right-0 px-4 transition-opacity duration-300",
            isHovered ? "opacity-100 delay-100" : "opacity-0 pointer-events-none"
        )}>
            <p className="text-sm font-bold truncate">Brand Health</p>
            <p className="text-xs text-muted-foreground">{health}% Completado</p>
        </div>
      </div>

      {/* BODY: Navigation Items */}
      <nav className="flex-1 py-4 flex flex-col gap-6 overflow-y-auto overflow-x-hidden scrollbar-hide">
        <TooltipProvider delayDuration={0}>
          {navGroups.map((group, groupIdx) => (
            <div key={groupIdx} className="flex flex-col gap-1">
              {/* Group Title (Only visible when expanded) */}
              <div className={cn(
                  "px-4 py-1 text-xs font-semibold text-muted-foreground/50 uppercase tracking-wider transition-opacity duration-300",
                  isHovered ? "opacity-100 delay-75" : "opacity-0 w-0 h-0 overflow-hidden"
              )}>
                {group.title}
              </div>

              {group.items.map((item) => {
                const isActive = activeSection === item.id;
                const isComplete = item.status.status === "complete";
                const isEmpty = item.status.status === "empty";
                
                return (
                  <Tooltip key={item.id}>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => onNavigate(item.id)}
                        className={cn(
                          "relative flex items-center h-10 w-full transition-all group/item px-4",
                          isActive ? "bg-primary/5 text-primary" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                        )}
                      >
                        {/* Active Indicator Line */}
                        {isActive && (
                          <div className="absolute left-0 top-2 bottom-2 w-1 bg-primary rounded-r-full" />
                        )}

                        {/* Icon Container */}
                        <div className="relative shrink-0 flex items-center justify-center w-8 h-8">
                            <item.icon className={cn("h-4 w-4 transition-transform group-hover/item:scale-110", isActive && "text-primary")} />
                            
                            {/* Status Dot */}
                            <div className={cn(
                                "absolute top-1 right-1 h-1.5 w-1.5 rounded-full border border-background ring-1 ring-background",
                                isComplete ? "bg-green-500" : isEmpty ? "bg-muted-foreground/30" : "bg-amber-500"
                            )} />
                        </div>

                        {/* Label (Expanded) */}
                        <div className={cn(
                            "ml-4 flex-1 text-left transition-opacity duration-300 flex items-center justify-between",
                            isHovered ? "opacity-100 delay-75" : "opacity-0 w-0 overflow-hidden"
                        )}>
                            <span className="font-medium text-sm whitespace-nowrap">{item.label}</span>
                            {isComplete && <CheckCircle2 className="h-3 w-3 text-green-500 ml-2 shrink-0" />}
                        </div>
                      </button>
                    </TooltipTrigger>
                    {!isHovered && (
                        <TooltipContent side="right" className="flex items-center gap-2">
                            {item.label}
                            {isComplete ? (
                                 <span className="text-[10px] bg-green-100 text-green-700 px-1.5 rounded-full">Listo</span>
                            ) : (
                                 <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 rounded-full">Falta</span>
                            )}
                        </TooltipContent>
                    )}
                  </Tooltip>
                );
              })}
            </div>
          ))}
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
