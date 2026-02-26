"use client";

import { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { BrandStrategy, BrandCompetitor } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Trash2, Save, Loader2, Target, Swords } from "lucide-react";

interface StrategyFormProps {
    initialData: BrandStrategy;
    onSave: (data: BrandStrategy) => Promise<void>;
    isSaving?: boolean;
}

export function StrategyForm({ initialData, onSave, isSaving = false }: StrategyFormProps) {
    const [strategy, setStrategy] = useState<BrandStrategy>(initialData);

    useEffect(() => {
        setStrategy(initialData);
    }, [initialData]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave(strategy);
    };

    const addCompetitor = () => {
        setStrategy({
            ...strategy,
            competitors: [
                ...strategy.competitors,
                { id: uuidv4(), name: "", differentiation: "" }
            ]
        });
    };

    const updateCompetitor = (id: string, field: keyof BrandCompetitor, value: string) => {
        const updatedCompetitors = strategy.competitors.map(c => 
            c.id === id ? { ...c, [field]: value } : c
        );
        setStrategy({
            ...strategy,
            competitors: updatedCompetitors
        });
    };

    const removeCompetitor = (id: string) => {
        setStrategy({
            ...strategy,
            competitors: strategy.competitors.filter(c => c.id !== id)
        });
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-8">
            <div className="space-y-4">
                <div className="flex items-center gap-2 pb-2 border-b text-primary">
                    <Target className="w-5 h-5" />
                    <h3 className="font-medium">Propuesta de Valor</h3>
                </div>
                <div className="space-y-2">
                    <Label htmlFor="uvp">Unique Value Proposition (UVP)</Label>
                    <Textarea 
                        id="uvp"
                        value={strategy.unique_value_proposition || ""}
                        onChange={(e) => setStrategy({...strategy, unique_value_proposition: e.target.value})}
                        placeholder="¿Qué te hace único y diferente en el mercado?"
                        className="min-h-[100px]"
                    />
                </div>
            </div>

            <div className="space-y-4">
                <div className="flex items-center justify-between pb-2 border-b text-primary">
                    <div className="flex items-center gap-2">
                        <Swords className="w-5 h-5" />
                        <h3 className="font-medium">Competencia</h3>
                    </div>
                    <Button type="button" variant="outline" size="sm" onClick={addCompetitor}>
                        <Plus className="w-4 h-4 mr-2" />
                        Agregar
                    </Button>
                </div>

                <div className="space-y-3">
                    {strategy.competitors.map((competitor) => (
                        <div key={competitor.id} className="p-3 bg-muted/20 rounded-lg border space-y-3">
                            <div className="flex items-center gap-2">
                                <div className="flex-1">
                                    <Label className="text-xs text-muted-foreground">Nombre del Competidor</Label>
                                    <Input 
                                        value={competitor.name}
                                        onChange={(e) => updateCompetitor(competitor.id, "name", e.target.value)}
                                        placeholder="Ej: Competidor X"
                                    />
                                </div>
                                <Button 
                                    type="button" 
                                    variant="ghost" 
                                    size="icon" 
                                    className="text-muted-foreground hover:text-destructive mt-5"
                                    onClick={() => removeCompetitor(competitor.id)}
                                >
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                            </div>
                            <div>
                                <Label className="text-xs text-muted-foreground">Factor de Diferenciación (vs Nosotros)</Label>
                                <Textarea 
                                    value={competitor.differentiation || ""}
                                    onChange={(e) => updateCompetitor(competitor.id, "differentiation", e.target.value)}
                                    placeholder="¿En qué son diferentes? ¿Cuál es su debilidad?"
                                    className="h-16 text-sm"
                                />
                            </div>
                        </div>
                    ))}
                    {strategy.competitors.length === 0 && (
                        <p className="text-sm text-muted-foreground text-center py-4 italic">
                            No hay competidores registrados.
                        </p>
                    )}
                </div>
            </div>

            <div className="flex justify-end pt-4">
                <Button type="submit" disabled={isSaving}>
                    {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                    Guardar Estrategia
                </Button>
            </div>
        </form>
    );
}
