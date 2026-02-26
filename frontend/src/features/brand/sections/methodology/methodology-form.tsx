"use client";

import { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { BrandStrategy, BrandMethodologyPillar } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Trash2, Save, Loader2, Lightbulb } from "lucide-react";

interface MethodologyFormProps {
    initialData: BrandStrategy;
    onSave: (data: BrandStrategy) => Promise<void>;
    isSaving?: boolean;
}

export function MethodologyForm({ initialData, onSave, isSaving = false }: MethodologyFormProps) {
    const [strategy, setStrategy] = useState<BrandStrategy>(initialData);

    useEffect(() => {
        setStrategy(initialData);
    }, [initialData]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave(strategy);
    };

    const addPillar = () => {
        setStrategy({
            ...strategy,
            methodology_pillars: [
                ...strategy.methodology_pillars,
                { id: uuidv4(), title: "", description: "" }
            ]
        });
    };

    const updatePillar = (id: string, field: keyof BrandMethodologyPillar, value: string) => {
        const updatedPillars = strategy.methodology_pillars.map(p => 
            p.id === id ? { ...p, [field]: value } : p
        );
        setStrategy({
            ...strategy,
            methodology_pillars: updatedPillars
        });
    };

    const removePillar = (id: string) => {
        setStrategy({
            ...strategy,
            methodology_pillars: strategy.methodology_pillars.filter(p => p.id !== id)
        });
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-8">
            <div className="space-y-4">
                <div className="flex items-center gap-2 pb-2 border-b text-primary">
                    <Lightbulb className="w-5 h-5" />
                    <h3 className="font-medium">Tu Método Único</h3>
                </div>
                <div className="space-y-2">
                    <Label htmlFor="methodology_name">Nombre de la Metodología</Label>
                    <Input 
                        id="methodology_name"
                        value={strategy.methodology_name || ""}
                        onChange={(e) => setStrategy({...strategy, methodology_name: e.target.value})}
                        placeholder="Ej: Método 3C, Sistema Growth..."
                    />
                    <p className="text-xs text-muted-foreground">Ponle nombre a tu proceso para aumentar su valor percibido.</p>
                </div>

                <div className="space-y-2">
                    <Label htmlFor="methodology_description">Descripción General</Label>
                    <Textarea 
                        id="methodology_description"
                        value={strategy.methodology_description || ""}
                        onChange={(e) => setStrategy({...strategy, methodology_description: e.target.value})}
                        placeholder="Describe en qué consiste tu metodología en líneas generales..."
                        className="h-24"
                    />
                </div>
            </div>

            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <Label className="text-base font-medium">Pilares del Método</Label>
                    <Button type="button" variant="outline" size="sm" onClick={addPillar}>
                        <Plus className="w-4 h-4 mr-2" />
                        Agregar Pilar
                    </Button>
                </div>

                <div className="space-y-4">
                    {strategy.methodology_pillars.map((pillar, index) => (
                        <div key={pillar.id} className="flex gap-4 items-start p-4 bg-muted/20 rounded-lg border relative">
                            <div className="flex items-center justify-center h-6 w-6 rounded-full bg-primary/10 text-primary text-xs font-bold mt-1">
                                {index + 1}
                            </div>
                            <div className="space-y-3 flex-1">
                                <div>
                                    <Label className="text-xs text-muted-foreground">Título del Pilar</Label>
                                    <Input 
                                        value={pillar.title}
                                        onChange={(e) => updatePillar(pillar.id, "title", e.target.value)}
                                        placeholder="Ej: Captación"
                                    />
                                </div>
                                <div>
                                    <Label className="text-xs text-muted-foreground">Descripción</Label>
                                    <Textarea 
                                        value={pillar.description || ""}
                                        onChange={(e) => updatePillar(pillar.id, "description", e.target.value)}
                                        placeholder="¿En qué consiste este paso?"
                                        className="h-20 text-sm"
                                    />
                                </div>
                            </div>
                            <Button 
                                type="button" 
                                variant="ghost" 
                                size="icon" 
                                className="text-muted-foreground hover:text-destructive absolute top-2 right-2"
                                onClick={() => removePillar(pillar.id)}
                            >
                                <Trash2 className="w-4 h-4" />
                            </Button>
                        </div>
                    ))}
                    {strategy.methodology_pillars.length === 0 && (
                        <div className="text-center py-8 border-2 border-dashed rounded-lg">
                            <p className="text-sm text-muted-foreground">
                                No has definido los pilares de tu metodología.
                            </p>
                        </div>
                    )}
                </div>
            </div>

            <div className="flex justify-end pt-4">
                <Button type="submit" disabled={isSaving}>
                    {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                    Guardar Metodología
                </Button>
            </div>
        </form>
    );
}
