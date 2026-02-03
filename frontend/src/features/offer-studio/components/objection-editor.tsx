"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Plus, Trash2, GripVertical } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Objection } from "@/lib/api/offer";

export function ObjectionEditor() {
  const [objections, setObjections] = useState<Objection[]>([
    { id: "1", trigger: "Es muy caro", strategy: "Value Stack", script: "Entiendo, pero considera el costo de..." }
  ]);

  const addObjection = () => {
    setObjections([...objections, { id: crypto.randomUUID(), trigger: "", strategy: "", script: "" }]);
  };

  const removeObjection = (id: string) => {
    setObjections(objections.filter(o => o.id !== id));
  };

  const updateObjection = (id: string, field: keyof Objection, value: string) => {
    setObjections(objections.map(o => o.id === id ? { ...o, [field]: value } : o));
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Matriz de Objeciones</h3>
        <Button onClick={addObjection} size="sm" variant="outline">
          <Plus className="h-4 w-4 mr-2" /> Agregar Objeción
        </Button>
      </div>
      
      <div className="space-y-3">
        {objections.map((obj, index) => (
          <Card key={obj.id} className="relative group">
            <CardContent className="p-4 pt-4">
              <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
                {/* Drag Handle (Visual) */}
                <div className="hidden md:flex md:col-span-1 items-center justify-center text-muted-foreground cursor-grab">
                   <GripVertical className="h-5 w-5" />
                   <span className="sr-only">Mover</span>
                </div>

                {/* Content */}
                <div className="md:col-span-10 space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <Label className="text-xs text-muted-foreground">Frase Detonante (Trigger)</Label>
                      <Input 
                        placeholder="Ej: No tengo dinero" 
                        value={obj.trigger}
                        onChange={(e) => updateObjection(obj.id, "trigger", e.target.value)}
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs text-muted-foreground">Estrategia</Label>
                      <Input 
                        placeholder="Ej: Financiación / Downsell" 
                        value={obj.strategy}
                        onChange={(e) => updateObjection(obj.id, "strategy", e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">Script de Respuesta (IA)</Label>
                    <Textarea 
                      placeholder="Escribe cómo debería responder el agente..." 
                      className="min-h-[80px]"
                      value={obj.script}
                      onChange={(e) => updateObjection(obj.id, "script", e.target.value)}
                    />
                  </div>
                </div>

                {/* Actions */}
                <div className="md:col-span-1 flex items-start justify-end md:justify-center">
                   <Button 
                    variant="ghost" 
                    size="icon" 
                    className="text-muted-foreground hover:text-destructive"
                    onClick={() => removeObjection(obj.id)}
                   >
                     <Trash2 className="h-4 w-4" />
                   </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {objections.length === 0 && (
        <div className="text-center py-8 border-2 border-dashed rounded-lg text-muted-foreground">
          No hay objeciones definidas. Agrega una para entrenar al agente.
        </div>
      )}
    </div>
  );
}
