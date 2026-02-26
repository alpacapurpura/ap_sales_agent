"use client";

import { useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { KeyFigure } from "@/features/brand/types";
import { useBrandSettings } from "../../hooks/useBrandSettings";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Users } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { TeamList } from "./team-list";
import { TeamMemberForm } from "./team-member-form";
import { toast } from "sonner";

export function TeamManager() {
    const { settings, updateTeam, saving } = useBrandSettings();
    const team = settings?.team || [];

    // Team Modal State
    const [isTeamModalOpen, setIsTeamModalOpen] = useState(false);
    const [currentMember, setCurrentMember] = useState<KeyFigure | null>(null);

    // --- Handlers ---
    const openTeamModal = (member?: KeyFigure) => {
        if (member) {
            setCurrentMember(member);
        } else {
            setCurrentMember({
                id: uuidv4(),
                name: "",
                role: "",
                is_primary_voice: false,
                bio: "",
                gender: "Masculino",
                communication_style: "Directo/Al Grano",
                personal_website: "",
                personal_linkedin: "",
                personal_instagram: "",
                personal_tiktok: "",
                personal_facebook: "",
                work_whatsapp: "",
                gallery: []
            });
        }
        setIsTeamModalOpen(true);
    };

    const handleSaveMember = async (member: KeyFigure) => {
        let newTeam = [...team];
        
        // Handle Primary Voice exclusivity
        if (member.is_primary_voice) {
            newTeam = newTeam.map(m => ({ ...m, is_primary_voice: false }));
        }

        const index = newTeam.findIndex(m => m.id === member.id);
        if (index >= 0) {
            newTeam[index] = member;
        } else {
            newTeam.push(member);
        }
        
        await updateTeam(newTeam);
        setIsTeamModalOpen(false);
    };

    const handleDeleteMember = async (id: string) => {
        const newTeam = team.filter(m => m.id !== id);
        await updateTeam(newTeam);
        toast.success("Miembro eliminado.");
    };

    return (
        <div className="space-y-8">
            <Card className="w-full min-h-[600px]">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-6">
                    <div className="space-y-1">
                        <CardTitle className="flex items-center gap-2">
                            <Users className="h-6 w-6" />
                            Personas Clave (Key Figures)
                        </CardTitle>
                        <CardDescription className="mt-1.5">
                            Personas que representan la autoridad de la marca.
                        </CardDescription>
                    </div>
                    <Button onClick={() => openTeamModal()} className="gap-2">
                        <Plus className="mr-2 h-4 w-4" />
                        Agregar Persona
                    </Button>
                </CardHeader>
                <CardContent>
                    <TeamList 
                        team={team} 
                        onEdit={openTeamModal} 
                        onDelete={handleDeleteMember} 
                    />
                </CardContent>
            </Card>

            {/* --- TEAM MODAL --- */}
            <Dialog open={isTeamModalOpen} onOpenChange={setIsTeamModalOpen}>
                <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>{currentMember?.name ? "Editar Persona" : "Agregar Persona"}</DialogTitle>
                    </DialogHeader>
                    {currentMember && (
                        <TeamMemberForm 
                            initialData={currentMember}
                            onSave={handleSaveMember}
                            onCancel={() => setIsTeamModalOpen(false)}
                            isSaving={saving}
                            embedded={true}
                        />
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}
