"use client";

import { useState } from "react";
import { AuthorityItem } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Save, Loader2 } from "lucide-react";
import { WithCopilot } from "@/features/copilot/components/WithCopilot";

interface AuthorityItemFormProps {
    initialData: AuthorityItem;
    onSave: (item: AuthorityItem) => void;
    onCancel?: () => void;
    isSaving?: boolean;
}

export function AuthorityItemForm({ initialData, onSave, onCancel, isSaving = false }: AuthorityItemFormProps) {
    const [currentItem, setCurrentItem] = useState<AuthorityItem>(initialData);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave(currentItem);
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                    <Label className="text-right">Entidad</Label>
                    <WithCopilot fieldId="authority_entity" fieldLabel="Entidad de Autoridad" getValue={() => currentItem.entity_name || ""}>
                      <Input
                          value={currentItem.entity_name}
                          onChange={(e) => setCurrentItem({...currentItem, entity_name: e.target.value})}
                          className="col-span-3"
                          placeholder="Ej: Forbes"
                          required
                      />
                    </WithCopilot>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                    <Label className="text-right">Tipo</Label>
                    <Select 
                        value={currentItem.type} 
                        onValueChange={(val) => setCurrentItem({...currentItem, type: val})}
                    >
                        <SelectTrigger className="col-span-3">
                            <SelectValue placeholder="Seleccione" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="Prensa / Media">Prensa / Media</SelectItem>
                            <SelectItem value="Certificación Oficial">Certificación Oficial</SelectItem>
                            <SelectItem value="Partner Tecnológico">Partner Tecnológico</SelectItem>
                            <SelectItem value="Premio / Award">Premio / Award</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                    <Label className="text-right">Contexto</Label>
                    <WithCopilot fieldId="authority_context" fieldLabel="Contexto de Autoridad" getValue={() => currentItem.context || ""}>
                      <Input
                          value={currentItem.context || ""}
                          onChange={(e) => setCurrentItem({...currentItem, context: e.target.value})}
                          className="col-span-3"
                          placeholder="Ej: Nombrada Top Agency 2024"
                      />
                    </WithCopilot>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                    <Label className="text-right">URL Prueba</Label>
                    <Input 
                        value={currentItem.proof_url || ""} 
                        onChange={(e) => setCurrentItem({...currentItem, proof_url: e.target.value})}
                        className="col-span-3" 
                        placeholder="https://..."
                    />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                    <Label className="text-right">URL Logo</Label>
                    <Input 
                        value={currentItem.logo_url || ""} 
                        onChange={(e) => setCurrentItem({...currentItem, logo_url: e.target.value})}
                        className="col-span-3" 
                        placeholder="https://..."
                    />
                </div>
            </div>
            
            <div className="flex justify-end gap-2 pt-4">
                {onCancel && (
                    <Button type="button" variant="outline" onClick={onCancel} disabled={isSaving}>
                        Cancelar
                    </Button>
                )}
                <Button type="submit" disabled={isSaving || !currentItem.entity_name}>
                    {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                    Guardar
                </Button>
            </div>
        </form>
    );
}
