"use client";

import { AuthorityItem } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Award, ExternalLink, Edit2, Trash2 } from "lucide-react";

interface AuthorityListProps {
    items: AuthorityItem[];
    onEdit: (item: AuthorityItem) => void;
    onDelete: (id: string) => void;
}

export function AuthorityList({ items, onEdit, onDelete }: AuthorityListProps) {
    if (!items || items.length === 0) {
        return (
            <div className="col-span-full text-center p-8 text-muted-foreground border-2 border-dashed rounded-lg">
                No hay respaldos registrados.
            </div>
        );
    }

    return (
        <div className="grid gap-4">
            {items.map((item) => (
                <Card 
                    key={item.id} 
                    className="group cursor-pointer border hover:border-primary transition-all bg-background shadow-sm hover:shadow-md"
                    onClick={() => onEdit(item)}
                >
                    <CardContent className="p-6 flex flex-col sm:flex-row sm:items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <div className="p-2 bg-amber-500/10 rounded-full">
                                {item.logo_url ? (
                                    <img src={item.logo_url} alt={item.entity_name} className="h-6 w-6 object-contain" />
                                ) : (
                                    <Award className="h-6 w-6 text-amber-600" />
                                )}
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
                                onClick={() => onEdit(item)}
                            >
                                <Edit2 className="h-4 w-4" />
                            </Button>
                            <Button 
                                variant="ghost" 
                                size="icon" 
                                className="h-8 w-8 rounded-none text-destructive hover:text-destructive" 
                                onClick={() => onDelete(item.id)}
                            >
                                <Trash2 className="h-4 w-4" />
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
}
