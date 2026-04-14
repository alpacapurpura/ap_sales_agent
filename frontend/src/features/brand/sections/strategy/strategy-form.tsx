"use client";

import { useState, useEffect } from "react";
import { BrandStrategy } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Save, Loader2 } from "lucide-react";

interface StrategyFormProps {
  initialData: BrandStrategy;
  onSave: (data: BrandStrategy) => Promise<void>;
  isSaving?: boolean;
}

/**
 * @deprecated Use MethodologyManager instead. This form is kept for backward compatibility
 * but is no longer referenced in the edit sheet manager.
 */
export function StrategyForm({ initialData, onSave, isSaving = false }: StrategyFormProps) {
  const [strategy, setStrategy] = useState<BrandStrategy>(initialData);

  useEffect(() => {
    setStrategy(initialData);
  }, [initialData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(strategy);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="methodology_name">Nombre de Metodologia</Label>
          <Input
            id="methodology_name"
            value={strategy.methodology_name || ""}
            onChange={(e) => setStrategy({ ...strategy, methodology_name: e.target.value })}
            placeholder="Nombre de tu metodologia"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="methodology_description">Descripcion</Label>
          <Textarea
            id="methodology_description"
            value={strategy.methodology_description || ""}
            onChange={(e) => setStrategy({ ...strategy, methodology_description: e.target.value })}
            placeholder="Describe tu metodologia"
            className="min-h-[100px]"
          />
        </div>
      </div>

      <div className="flex justify-end pt-4">
        <Button type="submit" disabled={isSaving}>
          {isSaving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Guardar
        </Button>
      </div>
    </form>
  );
}
