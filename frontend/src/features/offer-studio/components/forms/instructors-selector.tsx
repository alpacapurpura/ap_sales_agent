"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { KeyFigure, brandApi } from "@/lib/api/brand";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Users, UserPlus, GraduationCap, Plus } from "lucide-react";
import { TeamForm } from "@/features/brand/components/forms/team-form";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface InstructorsSelectorProps {
    selectedInstructorIds: string[];
    onUpdate: (ids: string[]) => void;
}

export function InstructorsSelector({ selectedInstructorIds, onUpdate }: InstructorsSelectorProps) {
    const { getToken } = useAuth();
    const [team, setTeam] = useState<KeyFigure[]>([]);
    const [loading, setLoading] = useState(false);
    const [isGlobalManagerOpen, setIsGlobalManagerOpen] = useState(false);

    // Fetch Team Data
    const fetchTeam = async () => {
        setLoading(true);
        try {
            const token = await getToken();
            if (!token) return;
            const settings = await brandApi.getBrandSettings(token);
            setTeam(settings.team || []);
        } catch (error) {
            console.error("Error fetching team:", error);
            toast.error("Error al cargar el equipo");
        } finally {
            setLoading(false);
        }
    };

    // Also fetch on mount to show previews
    useEffect(() => {
        fetchTeam();
    }, []);

    const handleToggle = (id: string, checked: boolean) => {
        if (checked) {
            onUpdate([...selectedInstructorIds, id]);
        } else {
            onUpdate(selectedInstructorIds.filter(existingId => existingId !== id));
        }
    };

    const handleGlobalSave = async (newTeam: KeyFigure[]) => {
        try {
            const token = await getToken();
            if (!token) return;
            
            // We need to save the whole brand settings, so we fetch first
            const settings = await brandApi.getBrandSettings(token);
            await brandApi.updateBrandSettings({
                ...settings,
                team: newTeam
            }, token);
            
            setTeam(newTeam);
            toast.success("Equipo actualizado correctamente");
            setIsGlobalManagerOpen(false);
        } catch (error) {
            console.error(error);
            toast.error("Error al guardar cambios globales");
        }
    };

    if (loading && team.length === 0) {
        return <div className="flex justify-center p-4"><Loader2 className="animate-spin text-muted-foreground" /></div>;
    }

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="text-base flex items-center gap-2">
                            <GraduationCap className="w-4 h-4 text-primary" />
                            Claustro Académico (Mentores)
                        </CardTitle>
                        <CardDescription className="text-xs mt-1">
                            Selecciona quiénes dictarán o darán soporte en este programa.
                        </CardDescription>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => setIsGlobalManagerOpen(true)}>
                        <Plus className="w-3 h-3 mr-2" /> Nuevo Mentor
                    </Button>
                </div>
            </CardHeader>
            <CardContent>
                {team.length === 0 ? (
                    <div className="text-center py-6 text-muted-foreground border-2 border-dashed rounded-lg bg-muted/20">
                        <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">No hay mentores registrados.</p>
                        <Button variant="link" onClick={() => setIsGlobalManagerOpen(true)}>Agregar el primero</Button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {team.map(member => {
                            const isSelected = selectedInstructorIds.includes(member.id);
                            return (
                                <div 
                                    key={member.id} 
                                    className={cn(
                                        "flex items-start space-x-3 p-3 rounded-lg border transition-all cursor-pointer hover:shadow-sm",
                                        isSelected ? "bg-primary/5 border-primary/40 ring-1 ring-primary/20" : "bg-card hover:bg-accent/50"
                                    )}
                                    onClick={() => handleToggle(member.id, !isSelected)}
                                >
                                    <Checkbox 
                                        id={`mentor-${member.id}`} 
                                        checked={isSelected}
                                        onCheckedChange={(checked) => handleToggle(member.id, checked as boolean)}
                                        className="mt-1"
                                    />
                                    <div className="flex-1 flex gap-3">
                                        <Avatar className="h-10 w-10 border shadow-sm">
                                            <AvatarImage src={member.headshot_url} className="object-cover" />
                                            <AvatarFallback>{member.name.substring(0,2).toUpperCase()}</AvatarFallback>
                                        </Avatar>
                                        <div className="grid gap-0.5">
                                            <label 
                                                htmlFor={`mentor-${member.id}`}
                                                className="text-sm font-semibold leading-none cursor-pointer"
                                            >
                                                {member.name}
                                            </label>
                                            <p className="text-xs text-muted-foreground line-clamp-1">{member.role}</p>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </CardContent>

            {/* Global Team Manager Dialog */}
            <Dialog open={isGlobalManagerOpen} onOpenChange={setIsGlobalManagerOpen}>
                <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Gestión de Equipo (Marca)</DialogTitle>
                        <DialogDescription>
                            Estos cambios afectarán a todas las ofertas y al Brand Book.
                        </DialogDescription>
                    </DialogHeader>
                    <TeamForm 
                        initialData={team}
                        onSave={handleGlobalSave}
                        isSaving={false}
                    />
                </DialogContent>
            </Dialog>
        </Card>
    );
}
