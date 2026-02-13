"use client";

import { useState } from "react";
import { AuthorityItem } from "@/lib/api/brand";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Save, Loader2, Award } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";

interface AuthorityItemFormProps {
    initialData: AuthorityItem;
    onSave: (item: AuthorityItem) => void;
    isSaving?: boolean;
    embedded?: boolean;
}

export function AuthorityItemForm({ initialData, onSave, isSaving = false, embedded = false }: AuthorityItemFormProps) {
    const [currentItem, setCurrentItem] = useState<AuthorityItem>(initialData);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave(currentItem);
    };

    const FormContent = (
        <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">Entidad</Label>
                <Input 
                    value={currentItem.entity_name} 
                    onChange={(e) => setCurrentItem({...currentItem, entity_name: e.target.value})}
                    className="col-span-3" 
                    placeholder="Ej: Forbes"
                    required
                />
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
                <Input 
                    value={currentItem.context || ""} 
                    onChange={(e) => setCurrentItem({...currentItem, context: e.target.value})}
                    className="col-span-3" 
                    placeholder="Ej: Nombrada Top Agency 2024"
                />
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
        </div>
    );

    const SubmitButton = (
        <Button type="submit" disabled={isSaving || !currentItem.entity_name}>
            {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
            Guardar Respaldo
        </Button>
    );

    if (embedded) {
        return (
            <form onSubmit={handleSubmit} className="space-y-6">
                {FormContent}
                <div className="flex justify-end pt-4">
                    {SubmitButton}
                </div>
            </form>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Editar Respaldo Institucional</CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit}>
                    {FormContent}
                </form>
            </CardContent>
            <CardFooter className="flex justify-end">
                {SubmitButton}
            </CardFooter>
        </Card>
    );
}
