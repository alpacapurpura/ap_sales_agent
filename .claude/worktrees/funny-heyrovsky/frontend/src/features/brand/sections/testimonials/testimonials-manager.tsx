"use client";

import { useState } from "react";
import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";
import { TestimonialsList } from "./testimonials-list";
import { TestimonialItemForm } from "./testimonial-item-form";
import { TestimonialItem } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Plus, MessageSquareQuote, Loader2 } from "lucide-react";
import { v4 as uuidv4 } from "uuid";

export function TestimonialsManager() {
    const { settings, updateTestimonials, loading, saving } = useBrandSettings();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [currentItem, setCurrentItem] = useState<TestimonialItem | undefined>(undefined);

    const items = settings?.testimonials || [];

    const handleOpenModal = (item?: TestimonialItem) => {
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

    const handleSave = async (item: TestimonialItem) => {
        let newItems = [...items];
        const index = newItems.findIndex(m => m.id === item.id);
        
        if (index >= 0) {
            newItems[index] = item;
        } else {
            newItems.push(item);
        }
        
        await updateTestimonials(newItems);
        setIsModalOpen(false);
    };

    const handleDelete = async (id: string) => {
        const newItems = items.filter(m => m.id !== id);
        await updateTestimonials(newItems);
    };

    if (loading) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

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
                    <Button onClick={() => handleOpenModal()} className="gap-2">
                        <Plus className="mr-2 h-4 w-4" />
                        Agregar Testimonio
                    </Button>
                </CardHeader>
                <CardContent>
                    <TestimonialsList 
                        items={items} 
                        onEdit={handleOpenModal} 
                        onDelete={handleDelete} 
                    />
                </CardContent>
            </Card>

            <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                <DialogContent className="sm:max-w-[600px]">
                    <DialogHeader>
                        <DialogTitle>{currentItem?.author_name ? "Editar Testimonio" : "Nuevo Testimonio"}</DialogTitle>
                    </DialogHeader>
                    {currentItem && (
                        <TestimonialItemForm
                            initialData={currentItem}
                            onSave={handleSave}
                            onCancel={() => setIsModalOpen(false)}
                            isSaving={saving}
                        />
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}
