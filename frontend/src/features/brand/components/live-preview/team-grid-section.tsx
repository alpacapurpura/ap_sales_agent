import { KeyFigure, BrandVisuals } from "@/lib/api/brand";
import { Button } from "@/components/ui/button";
import { Edit2, Users, Linkedin, Instagram, Phone } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface TeamGridSectionProps {
  team: KeyFigure[];
  visuals: BrandVisuals;
  onEdit: () => void;
}

export function TeamGridSection({ team, visuals, onEdit }: TeamGridSectionProps) {
  return (
    <section className="space-y-6 py-8">
      <div className="flex items-center justify-between px-2">
         <h3 
            className="text-xl font-bold text-foreground flex items-center gap-2"
         >
            <Users className="h-5 w-5 text-primary" />
            Key Figures (El Equipo)
         </h3>
         <Button size="sm" variant="outline" onClick={onEdit}>
            <Edit2 className="h-3.5 w-3.5 mr-2" />
            Gestionar Equipo
         </Button>
      </div>

      {team.length === 0 ? (
          <div className="text-center py-10 bg-muted/20 rounded-xl border border-dashed border-border">
              <p className="text-muted-foreground">No has añadido miembros clave del equipo.</p>
          </div>
      ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {team.map((member) => (
                  <div key={member.id} className="group bg-card rounded-xl p-6 border border-border shadow-sm hover:shadow-md transition-all">
                      <div className="flex flex-col items-center text-center space-y-3">
                          <Avatar className="h-20 w-20 border-2 border-background shadow-sm">
                              <AvatarFallback className="bg-primary/10 text-primary text-xl font-bold">
                                  {member.name.charAt(0)}
                              </AvatarFallback>
                          </Avatar>
                          
                          <div>
                              <h4 className="font-bold text-foreground">{member.name}</h4>
                              <p className="text-sm text-primary font-medium">{member.role || "Miembro del Equipo"}</p>
                          </div>

                          {member.bio && (
                              <p className="text-xs text-muted-foreground line-clamp-3">
                                  {member.bio}
                              </p>
                          )}

                          <div className="flex items-center gap-3 pt-2">
                              {member.personal_linkedin && (
                                  <a href={member.personal_linkedin} className="text-muted-foreground hover:text-primary transition-colors">
                                      <Linkedin className="h-4 w-4" />
                                  </a>
                              )}
                              {member.personal_instagram && (
                                  <a href={member.personal_instagram} className="text-muted-foreground hover:text-primary transition-colors">
                                      <Instagram className="h-4 w-4" />
                                  </a>
                              )}
                              {member.work_whatsapp && (
                                  <a href={`https://wa.me/${member.work_whatsapp}`} className="text-muted-foreground hover:text-primary transition-colors">
                                      <Phone className="h-4 w-4" />
                                  </a>
                              )}
                          </div>
                          
                          {member.is_primary_voice && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-primary/10 text-primary mt-2">
                                  Voz Principal
                              </span>
                          )}
                      </div>
                  </div>
              ))}
          </div>
      )}
    </section>
  );
}
