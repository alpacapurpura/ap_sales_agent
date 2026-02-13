"use client";

import { useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { TestimonialItem } from "@/lib/api/brand";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Trash2, Edit2, MessageSquareQuote, Video, AlignLeft, User } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

interface TestimonialsFormProps {
    initialData: TestimonialItem[];
    onSave: (items: TestimonialItem[]) => Promise<void>;
    isSaving: boolean;
}

export function TestimonialsForm({ initialData, onSave, isSaving }: TestimonialsFormProps) {
    const [items, setItems] = useState<TestimonialItem[]>(initialData || []);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [currentItem, setCurrentItem] = useState<TestimonialItem | null>(null);

    const openModal = (item?: TestimonialItem) => {
        if (item) {
            setCurrentItem(item);
        } else {
            setCurrentItem({
                id: uuidv4(),
                type: "text",
                content: "",
                author_name: "",
                author_role: "",
                rating: 5,
                author_avatar: ""
            });
        }
        setIsModalOpen(true);
    };

    const saveItem = () => {
        if (!currentItem) return;
        
        let newItems = [...items];
        const index = newItems.findIndex(m => m.id === currentItem.id);
        
        if (index >= 0) {
            newItems[index] = currentItem;
        } else {
            newItems.push(currentItem);
        }
        
        setItems(newItems);
        setIsModalOpen(false);
        onSave(newItems);
    };

    const deleteItem = (id: string) => {
        const newItems = items.filter(m => m.id !== id);
        setItems(newItems);
        onSave(newItems);
    };

    return (
        <div className="space-y-8">
            <Card className="w-full min-h-[600px]">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-6">
                    <div className="space-y-1">
                        <CardTitle className="flex items-center gap-2">
                            <MessageSquareQuote className="h-6 w-6" />
                            Testimonios & Social Proof
                        </CardTitle>
                        <CardDescription className="mt-1.5">Lo que dicen tus clientes para generar confianza.</CardDescription>
                    </div>
                    <Button onClick={() => openModal()} className="gap-2">
                        <Plus className="mr-2 h-4 w-4" />
                        Agregar Testimonio
                    </Button>
                </CardHeader>
                <CardContent className="grid gap-4">
                    {items.map(item => (
                        <Card 
                            key={item.id} 
                            className="group cursor-pointer border hover:border-primary transition-all bg-background shadow-sm hover:shadow-md relative"
                            onClick={() => openModal(item)}
                        >
                            <CardContent className="p-6 flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                                <div className="flex items-start space-x-4 flex-1">
                                    <div className="p-2 bg-primary/10 rounded-full flex-shrink-0">
                                        {item.type === 'video' ? <Video className="h-5 w-5 text-primary" /> : <AlignLeft className="h-5 w-5 text-primary" />}
                                    </div>
                                    <div className="space-y-1 flex-1">
                                        <div className="flex items-center gap-2">
                                            <h4 className="font-semibold">{item.author_name}</h4>
                                            <Badge variant="outline" className="text-[10px] h-5 px-1.5">
                                                {item.type === 'video' ? 'Video' : 'Texto'}
                                            </Badge>
                                        </div>
                                        <p className="text-sm text-muted-foreground">{item.author_role}</p>
                                        <p className="text-xs text-muted-foreground mt-2 line-clamp-2 italic border-l-2 pl-2 border-primary/20">
                                            {item.content}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center border rounded-md bg-background flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                                    <Button 
                                        variant="ghost" 
                                        size="icon" 
                                        className="h-8 w-8 rounded-none border-r" 
                                        onClick={() => openModal(item)}
                                    >
                                        <Edit2 className="h-4 w-4" />
                                    </Button>
                                    <Button 
                                        variant="ghost" 
                                        size="icon" 
                                        className="h-8 w-8 rounded-none text-destructive hover:text-destructive" 
                                        onClick={() => deleteItem(item.id)}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                    {items.length === 0 && (
                        <div className="col-span-full text-center p-10 text-muted-foreground border-2 border-dashed rounded-lg bg-muted/10">
                            No hay testimonios registrados.
                        </div>
                    )}
                </CardContent>
            </Card>

            <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                <DialogContent className="sm:max-w-[600px]">
                    <DialogHeader>
                        <DialogTitle>{currentItem?.author_name ? "Editar Testimonio" : "Nuevo Testimonio"}</DialogTitle>
                    </DialogHeader>
                    {currentItem && (
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
                        </div>
                    )}
                    <DialogFooter>
                        <Button onClick={saveItem} disabled={isSaving}>
                            {isSaving ? "Guardando..." : "Guardar"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
