"use client";

import { UserCheck, Star, Plus, User } from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { config } from "@/lib/config";

import type { KeyFigure, BrandVisuals } from "@/features/brand/types";

interface TeamSectionProps {
  team: KeyFigure[];
  visuals: BrandVisuals;
  onEdit: (member?: KeyFigure) => void;
}

export function TeamSection({ team, visuals, onEdit }: TeamSectionProps) {
  const hasContent = team && team.length > 0;
  const apiUrl = config.api.baseUrl;

  return (
    <section className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40">
      {/* Header */}
      <div
        className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors cursor-pointer"
        onClick={() => onEdit()}
      >
        <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
          <UserCheck className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-semibold uppercase tracking-wider">Equipo & Figuras Clave</h3>
      </div>

      {!hasContent ? (
        <div className="pl-0 md:pl-14 cursor-pointer" onClick={() => onEdit()}>
          <p className="text-lg text-muted-foreground italic mb-2">
            &quot;Detrás de cada gran marca hay personas reales. ¿Quiénes son?&quot;
          </p>
          <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Añadir Miembros del Equipo
          </span>
        </div>
      ) : (
        <div className="pl-0 md:pl-14">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-8">
            {team.map((member) => (
              <div
                key={member.id}
                className="flex flex-col items-center text-center group/member cursor-pointer"
                onClick={() => onEdit(member)}
              >
                <div className="relative mb-3">
                  <Avatar className="h-20 w-20 border-2 border-transparent group-hover/member:border-primary transition-colors">
                    <AvatarImage
                      src={
                        member.headshot_url
                          ? member.headshot_url.startsWith("http")
                            ? member.headshot_url
                            : `${apiUrl}${member.headshot_url}`
                          : undefined
                      }
                      className="object-cover"
                    />
                    <AvatarFallback className="text-lg font-bold bg-muted">
                      {member.name.substring(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  {member.is_primary_voice && (
                    <div
                      className="absolute -top-1 -right-1 bg-background rounded-full p-1 shadow-sm border border-border"
                      title="Voz Principal"
                    >
                      <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                    </div>
                  )}
                </div>
                <h4 className="font-medium text-foreground text-sm truncate w-full px-2">
                  {member.name}
                </h4>
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                  {member.role || "Miembro"}
                </p>
              </div>
            ))}

            {/* Add New Trigger (Visual) */}
            <div
              className="flex flex-col items-center justify-center text-center group/add cursor-pointer"
              onClick={() => onEdit()}
            >
              <div className="h-20 w-20 rounded-full border-2 border-dashed border-muted-foreground/30 flex items-center justify-center mb-3 group-hover/add:border-primary/50 group-hover/add:bg-primary/5 transition-colors">
                <Plus className="w-6 h-6 text-muted-foreground group-hover/add:text-primary" />
              </div>
              <span className="text-sm text-muted-foreground group-hover/add:text-primary">
                Nuevo
              </span>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
