"use client";

import { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { TestimonialItem } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { User } from "lucide-react";
import { DialogFooter } from "@/components/ui/dialog";

interface TestimonialItemFormProps {
    initialData?: TestimonialItem;
    onSave: (item: TestimonialItem) => void;
    onCancel: () => void;
    isSaving?: boolean;
}

export function TestimonialItemForm({ initialData, onSave, onCancel, isSaving = false }: TestimonialItemFormProps) {
    const [currentItem, setCurrentItem] = useState<TestimonialItem>({
        id: uuidv4(),
        type: "text",
        content: "",
        author_name: "",
        author_role: "",
        rating: 5,
        author_avatar: ""
    });

    useEffect(() => {
        if (initialData) {
            setCurrentItem(initialData);
        }
    }, [initialData]);

    const handleSubmit = () => {
        onSave(currentItem);
    };

    return (
        <div className="flex flex-col gap-6 py-4">
            {/* Type Selection */}
            <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                    <Label>Tipo de Testimonio</Label>
                    <Select 
                        value={currentItem.type} 
                        onValueChange={(val: "text" | "video") => setCurrentItem({...currentItem, type: val})}
                    >
                        <SelectTrigger>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="text">Texto (Cita)</SelectItem>
                            <SelectItem value="video">Video (YouTube)</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
                <div className="flex flex-col gap-2">
                    <Label>Calificación (Estrellas)</Label>
                    <Select 
                        value={currentItem.rating?.toString()} 
                        onValueChange={(val) => setCurrentItem({...currentItem, rating: parseInt(val)})}
                    >
                        <SelectTrigger>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="5">5 Estrellas</SelectItem>
                            <SelectItem value="4">4 Estrellas</SelectItem>
                            <SelectItem value="3">3 Estrellas</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            {/* Author Info */}
            <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                    <Label>Nombre del Autor</Label>
                    <Input 
                        value={currentItem.author_name} 
                        onChange={(e) => setCurrentItem({...currentItem, author_name: e.target.value})}
                        placeholder="Ej: María Pérez"
                    />
                </div>
                <div className="flex flex-col gap-2">
                    <Label>Rol / Empresa</Label>
                    <Input 
                        value={currentItem.author_role || ""} 
                        onChange={(e) => setCurrentItem({...currentItem, author_role: e.target.value})}
                        placeholder="CEO, Tech Solutions"
                    />
                </div>
            </div>

             {/* Avatar URL */}
             <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full overflow-hidden bg-muted border flex-shrink-0">
                    {currentItem.author_avatar ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={currentItem.author_avatar} alt="Preview" className="h-full w-full object-cover" />
                    ) : (
                        <div className="h-full w-full flex items-center justify-center text-muted-foreground">
                            <User className="h-6 w-6" />
                        </div>
                    )}
                </div>
                <div className="flex-1 flex flex-col gap-2">
                    <Label>Foto del Autor (URL)</Label>
                    <Input 
                        value={currentItem.author_avatar || ""} 
                        onChange={(e) => setCurrentItem({...currentItem, author_avatar: e.target.value})}
                        placeholder="https://..."
                    />
                </div>
            </div>

            {/* Content */}
            <div className="flex flex-col gap-2">
                <Label>
                    {currentItem.type === 'video' ? 'URL del Video (YouTube/Vimeo)' : 'Cita Textual'}
                </Label>
                {currentItem.type === 'video' ? (
                    <Input 
                        value={currentItem.content} 
                        onChange={(e) => setCurrentItem({...currentItem, content: e.target.value})}
                        placeholder="https://youtube.com/watch?v=..."
                    />
                ) : (
                    <Textarea 
                        value={currentItem.content} 
                        onChange={(e) => setCurrentItem({...currentItem, content: e.target.value})}
                        placeholder="Escribe lo que dijo el cliente..."
                        className="min-h-[100px]"
                    />
                )}
            </div>

            <DialogFooter>
                <Button variant="outline" onClick={onCancel} disabled={isSaving}>
                    Cancelar
                </Button>
                <Button onClick={handleSubmit} disabled={isSaving}>
                    {isSaving ? "Guardando..." : "Guardar"}
                </Button>
            </DialogFooter>
        </div>
    );
}
