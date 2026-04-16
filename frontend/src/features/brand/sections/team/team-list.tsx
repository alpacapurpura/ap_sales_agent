"use client";

import NextImage from "next/image";
import { User, Edit2, Trash2 } from "lucide-react";
import { memo } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { config } from "@/lib/config";
import { cn } from "@/lib/utils";

import { validateTeamMember } from "../../utils/brand-validation";

import type { KeyFigure } from "@/features/brand/types";

interface TeamListProps {
  team: KeyFigure[];
  onEdit: (member: KeyFigure) => void;
  onDelete: (id: string) => void;
}

export const TeamList = memo(function TeamList({ team, onEdit, onDelete }: TeamListProps) {
  if (team.length === 0) {
    return (
      <div className="col-span-full text-center p-8 text-muted-foreground border-2 border-dashed rounded-lg bg-muted/10">
        <User className="h-10 w-10 mx-auto mb-2 opacity-50" />
        <p>No hay personas registradas.</p>
        <p className="text-sm">Agrega miembros para definir quiénes representan la marca.</p>
      </div>
    );
  }

  const apiUrl = config.api.baseUrl;

  return (
    <div className="grid gap-4">
      {team.map((member) => {
        const status = validateTeamMember(member);
        const isComplete = status.status === "complete";
        const imageUrl = member.headshot_url
          ? member.headshot_url.startsWith("http")
            ? member.headshot_url
            : `${apiUrl}${member.headshot_url}`
          : null;

        return (
          <Card
            key={member.id}
            className="group cursor-pointer border hover:border-primary transition-all bg-card shadow-sm hover:shadow-md relative overflow-hidden"
            onClick={() => onEdit(member)}
          >
            <CardContent className="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center space-x-4 overflow-hidden">
                <div className="h-12 w-12 rounded-full relative flex-shrink-0 bg-muted border overflow-hidden">
                  {imageUrl ? (
                    <NextImage
                      src={imageUrl}
                      alt={member.name}
                      fill
                      className="object-cover"
                      unoptimized
                    />
                  ) : (
                    <div className="h-full w-full flex items-center justify-center bg-primary/10">
                      <User className="h-6 w-6 text-primary" />
                    </div>
                  )}
                  {/* Status Dot */}
                  <div
                    className={cn(
                      "absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background",
                      isComplete ? "bg-green-500" : "bg-amber-500",
                    )}
                  />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="font-semibold truncate text-base">{member.name}</h4>
                    {isComplete && (
                      <Badge
                        variant="outline"
                        className="text-[10px] h-5 px-1.5 text-green-600 bg-green-50 border-green-200"
                      >
                        Listo
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground truncate">
                    {member.role || "Sin rol definido"}
                  </p>
                  {member.is_primary_voice && (
                    <Badge
                      variant="secondary"
                      className="mt-1 text-xs bg-blue-100 text-blue-700 hover:bg-blue-100 border-blue-200"
                    >
                      Voz Principal
                    </Badge>
                  )}
                </div>
              </div>

              <div
                className="flex items-center gap-2 self-end sm:self-center"
                onClick={(e) => e.stopPropagation()}
              >
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-9 w-9 text-muted-foreground hover:text-foreground"
                  onClick={(e) => {
                    e.stopPropagation();
                    onEdit(member);
                  }}
                >
                  <Edit2 className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-9 w-9 text-destructive/70 hover:text-destructive hover:bg-destructive/10"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(member.id);
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
});
