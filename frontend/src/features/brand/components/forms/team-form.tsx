"use client";

import { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { KeyFigure } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Trash2, Edit2, User } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { validateTeamMember } from "../../utils/brand-validation";

interface TeamFormProps {
    initialData: KeyFigure[];
    onSave: (team: KeyFigure[]) => Promise<void>;
    isSaving: boolean;
}

export function TeamForm({ initialData, onSave, isSaving }: TeamFormProps) {
    const [team, setTeam] = useState<KeyFigure[]>(initialData);

    useEffect(() => {
        setTeam(initialData);
    }, [initialData]);

    // Team Modal State
    const [isTeamModalOpen, setIsTeamModalOpen] = useState(false);
    const [currentMember, setCurrentMember] = useState<KeyFigure | null>(null);

    // --- Team Handlers ---
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
                work_whatsapp: ""
            });
        }
        setIsTeamModalOpen(true);
    };

    const saveTeamMember = () => {
        if (!currentMember) return;
        
        let newTeam = [...team];
        const index = newTeam.findIndex(m => m.id === currentMember.id);
        
        if (currentMember.is_primary_voice) {
            // Ensure only one primary voice
            newTeam = newTeam.map(m => ({ ...m, is_primary_voice: false }));
        }

        if (index >= 0) {
            newTeam[index] = currentMember;
        } else {
            newTeam.push(currentMember);
        }
        
        setTeam(newTeam);
        setIsTeamModalOpen(false);
        onSave(newTeam);
    };

    const deleteTeamMember = (id: string) => {
        const newTeam = team.filter(m => m.id !== id);
        setTeam(newTeam);
        onSave(newTeam);
    };

    return (
        <div className="space-y-8">
            {/* --- TEAM SECTION --- */}
            <Card className="w-full min-h-[600px]">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-6">
                    <div className="space-y-1">
                    <CardTitle className="flex items-center gap-2">
                        <User className="h-6 w-6" />
                        Personas Clave (Key Figures)
                    </CardTitle>
                    <CardDescription className="mt-1.5">Personas que representan la autoridad de la marca.</CardDescription>
                    </div>
                    <Button onClick={() => openTeamModal()} className="gap-2">
                        <Plus className="mr-2 h-4 w-4" />
                        Agregar Persona
                    </Button>
                </CardHeader>
                <CardContent className="grid gap-4">
                    {team.map(member => {
                        const status = validateTeamMember(member);
                        const isComplete = status.status === "complete";

                        return (
                        <Card 
                            key={member.id} 
                            className="group cursor-pointer border hover:border-primary transition-all bg-background shadow-sm hover:shadow-md relative"
                            onClick={() => openTeamModal(member)}
                        >
                            <CardContent className="p-6 flex flex-col sm:flex-row sm:items-center justify-between">
                                <div className="flex items-center space-x-4">
                                    <div className="p-2 bg-primary/10 rounded-full relative">
                                        <User className="h-6 w-6 text-primary" />
                                        {/* Status Dot on Icon */}
                                        <div className={`absolute top-0 right-0 h-2.5 w-2.5 rounded-full border border-background ${isComplete ? 'bg-green-500' : 'bg-amber-500'}`} />
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h4 className="font-semibold">{member.name}</h4>
                                            {isComplete && <Badge variant="outline" className="text-[10px] h-5 px-1.5 text-green-600 bg-green-50 border-green-200">Listo</Badge>}
                                        </div>
                                        <p className="text-sm text-muted-foreground">{member.role}</p>
                                        {member.is_primary_voice && <Badge variant="secondary" className="mt-1 text-xs">Voz Principal</Badge>}
                                    </div>
                                </div>
                                <div className="flex items-center border rounded-md bg-background mt-4 sm:mt-0" onClick={(e) => e.stopPropagation()}>
                                    <Button 
                                        variant="ghost" 
                                        size="icon" 
                                        className="h-8 w-8 rounded-none border-r" 
                                        onClick={() => openTeamModal(member)}
                                    >
                                        <Edit2 className="h-4 w-4" />
                                    </Button>
                                    <Button 
                                        variant="ghost" 
                                        size="icon" 
                                        className="h-8 w-8 rounded-none text-destructive hover:text-destructive" 
                                        onClick={() => deleteTeamMember(member.id)}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                        );
                    })}
                    {team.length === 0 && (
                        <div className="col-span-full text-center p-8 text-muted-foreground border-2 border-dashed rounded-lg">
                            No hay personas registradas.
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* --- TEAM MODAL --- */}
            <Dialog open={isTeamModalOpen} onOpenChange={setIsTeamModalOpen}>
                <DialogContent className="sm:max-w-[700px] max-h-[85vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>{currentMember?.name ? "Editar Persona" : "Agregar Persona"}</DialogTitle>
                    </DialogHeader>
                    {currentMember && (
                        <div className="flex flex-col gap-6 py-4">
                            {/* Identity Section */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex flex-col gap-2">
                                    <Label>Nombre</Label>
                                    <Input 
                                        value={currentMember.name} 
                                        onChange={(e) => setCurrentMember({...currentMember, name: e.target.value})}
                                        placeholder="Nombre completo"
                                    />
                                </div>
                                <div className="flex flex-col gap-2">
                                    <Label>Rol / Título</Label>
                                    <Input 
                                        value={currentMember.role || ""} 
                                        onChange={(e) => setCurrentMember({...currentMember, role: e.target.value})}
                                        placeholder="Ej. Fundador, CEO"
                                    />
                                </div>
                            </div>

                            {/* Headshot URL */}
                            <div className="flex items-center gap-4">
                                <div className="h-16 w-16 rounded-full overflow-hidden bg-muted border flex-shrink-0">
                                    {currentMember.headshot_url ? (
                                        // eslint-disable-next-line @next/next/no-img-element
                                        <img src={currentMember.headshot_url} alt="Preview" className="h-full w-full object-cover" />
                                    ) : (
                                        <div className="h-full w-full flex items-center justify-center text-muted-foreground">
                                            <User className="h-8 w-8" />
                                        </div>
                                    )}
                                </div>
                                <div className="flex-1 flex flex-col gap-2">
                                    <Label>Foto de Perfil (URL)</Label>
                                    <Input 
                                        value={currentMember.headshot_url || ""} 
                                        onChange={(e) => setCurrentMember({...currentMember, headshot_url: e.target.value})}
                                        placeholder="https://..."
                                    />
                                    <p className="text-[10px] text-muted-foreground">Recomendado: Imagen cuadrada 400x400px.</p>
                                </div>
                            </div>

                            {/* Profile Section */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex flex-col gap-2">
                                    <Label>Género</Label>
                                    <Select 
                                        value={currentMember.gender} 
                                        onValueChange={(val: any) => setCurrentMember({...currentMember, gender: val})}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Seleccione" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="Masculino">Masculino</SelectItem>
                                            <SelectItem value="Femenino">Femenino</SelectItem>
                                            <SelectItem value="Neutro">Neutro</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="flex flex-col gap-2">
                                    <Label>Estilo de Comunicación</Label>
                                    <Select 
                                        value={currentMember.communication_style} 
                                        onValueChange={(val) => setCurrentMember({...currentMember, communication_style: val})}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Seleccione" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="Directo/Al Grano">Directo/Al Grano</SelectItem>
                                            <SelectItem value="Empático/Suave">Empático/Suave</SelectItem>
                                            <SelectItem value="Técnico/Analítico">Técnico/Analítico</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            {/* Bio Section */}
                            <div className="flex flex-col gap-2">
                                <Label>Bio Corta (Hook)</Label>
                                <Textarea 
                                    value={currentMember.bio || ""} 
                                    onChange={(e) => setCurrentMember({...currentMember, bio: e.target.value})}
                                    placeholder="Breve descripción para dar contexto a la IA..."
                                    className="min-h-[80px]"
                                />
                            </div>

                            {/* Voice Switch */}
                            <div className="flex items-center justify-between border p-3 rounded-lg bg-muted/20">
                                <div className="space-y-0.5">
                                    <Label className="text-base">Voz Principal</Label>
                                    <p className="text-sm text-muted-foreground">
                                        Si se activa, el bot adoptará esta personalidad al hablar.
                                    </p>
                                </div>
                                <Switch 
                                    checked={currentMember.is_primary_voice}
                                    onCheckedChange={(checked) => setCurrentMember({...currentMember, is_primary_voice: checked})}
                                />
                            </div>

                            {/* Social Media & Contact */}
                            <div className="space-y-4">
                                <h4 className="text-sm font-medium text-muted-foreground border-b pb-2">Redes y Contacto</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="flex flex-col gap-2">
                                        <Label>Website</Label>
                                        <Input 
                                            value={currentMember.personal_website || ""} 
                                            onChange={(e) => setCurrentMember({...currentMember, personal_website: e.target.value})}
                                            placeholder="https://..."
                                        />
                                    </div>
                                    <div className="flex flex-col gap-2">
                                        <Label>LinkedIn</Label>
                                        <Input 
                                            value={currentMember.personal_linkedin || ""} 
                                            onChange={(e) => setCurrentMember({...currentMember, personal_linkedin: e.target.value})}
                                            placeholder="https://linkedin.com/in/..."
                                        />
                                    </div>
                                    <div className="flex flex-col gap-2">
                                        <Label>Instagram</Label>
                                        <Input 
                                            value={currentMember.personal_instagram || ""} 
                                            onChange={(e) => setCurrentMember({...currentMember, personal_instagram: e.target.value})}
                                            placeholder="https://instagram.com/..."
                                        />
                                    </div>
                                    <div className="flex flex-col gap-2">
                                        <Label>TikTok</Label>
                                        <Input 
                                            value={currentMember.personal_tiktok || ""} 
                                            onChange={(e) => setCurrentMember({...currentMember, personal_tiktok: e.target.value})}
                                            placeholder="https://tiktok.com/@..."
                                        />
                                    </div>
                                    <div className="flex flex-col gap-2">
                                        <Label>Facebook</Label>
                                        <Input 
                                            value={currentMember.personal_facebook || ""} 
                                            onChange={(e) => setCurrentMember({...currentMember, personal_facebook: e.target.value})}
                                            placeholder="https://facebook.com/..."
                                        />
                                    </div>
                                    <div className="flex flex-col gap-2">
                                        <Label>WhatsApp (Trabajo)</Label>
                                        <Input 
                                            value={currentMember.work_whatsapp || ""} 
                                            onChange={(e) => setCurrentMember({...currentMember, work_whatsapp: e.target.value})}
                                            placeholder="+52..."
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                    <DialogFooter>
                        <Button onClick={saveTeamMember} disabled={isSaving}>
                            {isSaving ? "Guardando..." : "Guardar"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
