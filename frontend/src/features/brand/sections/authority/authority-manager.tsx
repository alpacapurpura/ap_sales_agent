"use client";

import { useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";
import { AuthorityItem } from "@/features/brand/types";
import { AuthorityList } from "./authority-list";
import { AuthorityItemForm } from "./authority-item-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Award, Plus, Loader2 } from "lucide-react";

export function AuthorityManager() {
    const { settings, updateVault, saving } = useBrandSettings();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [currentItem, setCurrentItem] = useState<AuthorityItem | null>(null);

    if (!settings) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    const vault = settings.authority_vault || [];

    const handleOpenModal = (item?: AuthorityItem) => {
        if (item) {
            setCurrentItem(item);
        } else {
            setCurrentItem({
                id: uuidv4(),
                entity_name: "",
                type: "Prensa / Media",
                context: "",
                proof_url: "",
                logo_url: ""
            });
        }
        setIsModalOpen(true);
    };

    const handleSave = async (item: AuthorityItem) => {
        const newVault = [...vault];
        const index = newVault.findIndex(i => i.id === item.id);
        
        if (index >= 0) {
            newVault[index] = item;
        } else {
            newVault.push(item);
        }
        
        await updateVault(newVault);
        setIsModalOpen(false);
    };

    const handleDelete = async (id: string) => {
        const newVault = vault.filter(i => i.id !== id);
        await updateVault(newVault);
    };

    return (
        <Card className="w-full min-h-[600px]">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-6">
                <div className="space-y-1">
                    <CardTitle className="flex items-center gap-2">
                        <Award className="h-6 w-6" />
                        Respaldo Institucional (Authority Vault)
                    </CardTitle>
                    <CardDescription className="mt-1.5">
                        Credenciales externas que validan la empresa (Prensa, Premios, etc.).
                    </CardDescription>
                </div>
                <Button onClick={() => handleOpenModal()} className="gap-2">
                    <Plus className="mr-2 h-4 w-4" />
                    Agregar Respaldo
                </Button>
            </CardHeader>
            <CardContent>
                <AuthorityList 
                    items={vault} 
                    onEdit={handleOpenModal} 
                    onDelete={handleDelete} 
                />
            </CardContent>

            <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                <DialogContent className="sm:max-w-[500px]">
                    <DialogHeader>
                        <DialogTitle>{currentItem?.entity_name ? "Editar Respaldo" : "Agregar Respaldo"}</DialogTitle>
                    </DialogHeader>
                    {currentItem && (
                        <AuthorityItemForm 
                            initialData={currentItem} 
                            onSave={handleSave} 
                            onCancel={() => setIsModalOpen(false)}
                            isSaving={saving}
                        />
                    )}
                </DialogContent>
            </Dialog>
        </Card>
    );
}
