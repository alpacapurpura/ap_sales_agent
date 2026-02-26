"use client";

import { useState } from "react";
import { KeyFigure } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Users, Plus, GraduationCap } from "lucide-react";
import { TeamManager } from "@/features/brand/sections/team/team-manager";
import { cn } from "@/lib/utils";

interface InstructorsSelectorProps {
    selectedInstructorIds: string[];
    onUpdate: (ids: string[]) => void;
    availableInstructors: KeyFigure[];
    onRefresh?: () => void;
}

export function InstructorsSelector({ selectedInstructorIds, onUpdate, availableInstructors, onRefresh }: InstructorsSelectorProps) {
    const [isGlobalManagerOpen, setIsGlobalManagerOpen] = useState(false);

    const handleToggle = (id: string, checked: boolean) => {
        if (checked) {
            onUpdate([...selectedInstructorIds, id]);
        } else {
            onUpdate(selectedInstructorIds.filter(existingId => existingId !== id));
        }
    };

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
                {availableInstructors.length === 0 ? (
                    <div className="text-center py-6 text-muted-foreground border-2 border-dashed rounded-lg bg-muted/20">
                        <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">No hay mentores registrados.</p>
                        <Button variant="link" onClick={() => setIsGlobalManagerOpen(true)}>Agregar el primero</Button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {availableInstructors.map(member => {
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
            <Dialog open={isGlobalManagerOpen} onOpenChange={(open) => {
                setIsGlobalManagerOpen(open);
                if (!open && onRefresh) onRefresh();
            }}>
                <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Gestión de Equipo (Marca)</DialogTitle>
                        <DialogDescription>
                            Estos cambios afectarán a todas las ofertas y al Brand Book.
                        </DialogDescription>
                    </DialogHeader>
                    <TeamManager />
                </DialogContent>
            </Dialog>
        </Card>
    );
}
