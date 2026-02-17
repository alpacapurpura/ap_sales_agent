"use client";

import { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { AuthorityItem } from "@/lib/api/brand";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Trash2, Edit2, Award, ExternalLink, User } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface AuthorityVaultFormProps {
    initialData: AuthorityItem[];
    onSave: (vault: AuthorityItem[]) => Promise<void>;
    isSaving: boolean;
}

export function AuthorityVaultForm({ initialData, onSave, isSaving }: AuthorityVaultFormProps) {
    const [vault, setVault] = useState<AuthorityItem[]>(initialData);

    // Vault Modal State
    const [isVaultModalOpen, setIsVaultModalOpen] = useState(false);
    const [currentItem, setCurrentItem] = useState<AuthorityItem | null>(null);

    // --- Vault Handlers ---
    const openVaultModal = (item?: AuthorityItem) => {
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
        setIsVaultModalOpen(true);
    };

    const saveVaultItem = () => {
        if (!currentItem) return;
        
        const newVault = [...vault];
        const index = newVault.findIndex(i => i.id === currentItem.id);
        
        if (index >= 0) {
            newVault[index] = currentItem;
        } else {
            newVault.push(currentItem);
        }
        
        setVault(newVault);
        setIsVaultModalOpen(false);
        onSave(newVault);
    };

    const deleteVaultItem = (id: string) => {
        const newVault = vault.filter(i => i.id !== id);
        setVault(newVault);
        onSave(newVault);
    };

    return (
        <div className="space-y-8">
            {/* --- VAULT SECTION --- */}
            <Card className="w-full min-h-[600px]">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-6">
                    <div className="space-y-1">
                    <CardTitle className="flex items-center gap-2">
                        <Award className="h-6 w-6" />
                        Respaldo Institucional (Authority Vault)
                    </CardTitle>
                    <CardDescription className="mt-1.5">Credenciales externas que validan la empresa (Prensa, Premios, etc.).</CardDescription>
                    </div>
                    <Button onClick={() => openVaultModal()} className="gap-2">
                        <Plus className="mr-2 h-4 w-4" />
                        Agregar Respaldo
                    </Button>
                </CardHeader>
                <CardContent className="grid gap-4">
                    {vault.map(item => (
                        <Card 
                            key={item.id} 
                            className="group cursor-pointer border hover:border-primary transition-all bg-background shadow-sm hover:shadow-md"
                            onClick={() => openVaultModal(item)}
                        >
                            <CardContent className="p-6 flex flex-col sm:flex-row sm:items-center justify-between">
                                <div className="flex items-center space-x-4">
                                    <div className="p-2 bg-amber-500/10 rounded-full">
                                        <Award className="h-6 w-6 text-amber-600" />
                                    </div>
                                    <div>
                                        <h4 className="font-semibold">{item.entity_name}</h4>
                                        <p className="text-sm text-muted-foreground">{item.type}</p>
                                        <p className="text-xs text-muted-foreground mt-1 line-clamp-1">{item.context}</p>
                                    </div>
                                </div>
                                <div className="flex items-center border rounded-md bg-background mt-4 sm:mt-0" onClick={(e) => e.stopPropagation()}>
                                    {item.proof_url && (
                                        <Button 
                                            variant="ghost" 
                                            size="icon" 
                                            className="h-8 w-8 rounded-none border-r" 
                                            title="Ver Prueba"
                                            onClick={() => window.open(item.proof_url, '_blank')}
                                        >
                                            <ExternalLink className="h-4 w-4" />
                                        </Button>
                                    )}
                                    <Button 
                                        variant="ghost" 
                                        size="icon" 
                                        className="h-8 w-8 rounded-none border-r" 
                                        onClick={() => openVaultModal(item)}
                                    >
                                        <Edit2 className="h-4 w-4" />
                                    </Button>
                                    <Button 
                                        variant="ghost" 
                                        size="icon" 
                                        className="h-8 w-8 rounded-none text-destructive hover:text-destructive" 
                                        onClick={() => deleteVaultItem(item.id)}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                    {vault.length === 0 && (
                        <div className="col-span-full text-center p-8 text-muted-foreground border-2 border-dashed rounded-lg">
                            No hay respaldos registrados.
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* --- VAULT MODAL --- */}
            <Dialog open={isVaultModalOpen} onOpenChange={setIsVaultModalOpen}>
                <DialogContent className="sm:max-w-[500px]">
                    <DialogHeader>
                        <DialogTitle>{currentItem?.entity_name ? "Editar Respaldo" : "Agregar Respaldo"}</DialogTitle>
                    </DialogHeader>
                    {currentItem && (
                        <div className="grid gap-4 py-4">
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label className="text-right">Entidad</Label>
                                <Input 
                                    value={currentItem.entity_name} 
                                    onChange={(e) => setCurrentItem({...currentItem, entity_name: e.target.value})}
                                    className="col-span-3" 
                                    placeholder="Ej: Forbes"
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
                    )}
                    <DialogFooter>
                        <Button onClick={saveVaultItem} disabled={isSaving}>
                            {isSaving ? "Guardando..." : "Guardar"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
