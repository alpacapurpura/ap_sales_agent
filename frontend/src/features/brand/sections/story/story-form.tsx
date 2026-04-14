"use client";

import { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { BrandStory, BrandStoryMilestone } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Trash2, Save, Loader2, Flag } from "lucide-react";
import { WithCopilot } from "@/features/copilot/components/WithCopilot";

interface StoryFormProps {
  initialData: BrandStory;
  onSave: (data: BrandStory) => Promise<void>;
  isSaving?: boolean;
}

export function StoryForm({ initialData, onSave, isSaving = false }: StoryFormProps) {
  const [story, setStory] = useState<BrandStory>(initialData);

  useEffect(() => {
    setStory(initialData);
  }, [initialData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(story);
  };

  const addMilestone = () => {
    setStory({
      ...story,
      milestones: [
        ...(story.milestones ?? []),
        { id: uuidv4(), year: new Date().getFullYear().toString(), title: "", description: "" },
      ],
    });
  };

  const updateMilestone = (id: string, field: keyof BrandStoryMilestone, value: string) => {
    const updatedMilestones = (story.milestones ?? []).map((m) =>
      m.id === id ? { ...m, [field]: value } : m,
    );
    setStory({
      ...story,
      milestones: updatedMilestones,
    });
  };

  const removeMilestone = (id: string) => {
    setStory({
      ...story,
      milestones: (story.milestones ?? []).filter((m) => m.id !== id),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="origin_story">Historia de Origen</Label>
          <WithCopilot
            fieldId="origin_story"
            fieldLabel="Historia de Origen"
            getValue={() => story.origin_story || ""}
          >
            <Textarea
              id="origin_story"
              value={story.origin_story || ""}
              onChange={(e) => setStory({ ...story, origin_story: e.target.value })}
              placeholder="Cuenta cómo nació tu marca..."
              className="min-h-[150px]"
            />
          </WithCopilot>
          <p className="text-xs text-muted-foreground">
            Una buena historia conecta emocionalmente con tu audiencia.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="mission">Mision</Label>
          <WithCopilot fieldId="mission" fieldLabel="Misión" getValue={() => story.mission || ""}>
            <Textarea
              id="mission"
              value={story.mission || ""}
              onChange={(e) => setStory({ ...story, mission: e.target.value })}
              placeholder="Para que existe tu marca? Ej: Existimos para empoderar a emprendedoras mediante IA para que vendan sin equipo."
              className="min-h-[100px]"
            />
          </WithCopilot>
          <p className="text-xs text-muted-foreground">
            El proposito actual de tu marca — por que existes hoy.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="vision">Vision</Label>
          <WithCopilot fieldId="vision" fieldLabel="Visión" getValue={() => story.vision || ""}>
            <Textarea
              id="vision"
              value={story.vision || ""}
              onChange={(e) => setStory({ ...story, vision: e.target.value })}
              placeholder="Que mundo quieres crear? Ej: Un mundo donde cualquier experto puede vivir de su conocimiento."
              className="min-h-[100px]"
            />
          </WithCopilot>
          <p className="text-xs text-muted-foreground">
            El futuro aspiracional — el mundo que tu marca quiere construir.
          </p>
        </div>

        <div className="space-y-4 pt-4 border-t">
          <div className="flex items-center justify-between">
            <Label className="text-base font-medium flex items-center gap-2">
              <Flag className="w-4 h-4" />
              Hitos Importantes
            </Label>
            <Button type="button" variant="outline" size="sm" onClick={addMilestone}>
              <Plus className="w-4 h-4 mr-2" />
              Agregar Hito
            </Button>
          </div>

          <div className="space-y-3">
            {(story.milestones ?? []).map((milestone) => (
              <div
                key={milestone.id}
                className="flex gap-3 items-start p-3 bg-muted/20 rounded-lg border"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex gap-2">
                    <Input
                      value={milestone.year}
                      onChange={(e) => updateMilestone(milestone.id, "year", e.target.value)}
                      placeholder="Año"
                      className="w-24"
                    />
                    <Input
                      value={milestone.title}
                      onChange={(e) => updateMilestone(milestone.id, "title", e.target.value)}
                      placeholder="Título del evento"
                      className="flex-1"
                    />
                  </div>
                  <Textarea
                    value={milestone.description || ""}
                    onChange={(e) => updateMilestone(milestone.id, "description", e.target.value)}
                    placeholder="Descripción breve..."
                    className="h-16 text-sm"
                  />
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-destructive h-8 w-8"
                  onClick={() => removeMilestone(milestone.id)}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ))}
            {(story.milestones ?? []).length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4 italic">
                No hay hitos registrados. Agrega momentos clave de tu historia.
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="flex justify-end pt-4">
        <Button type="submit" disabled={isSaving}>
          {isSaving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Guardar Historia
        </Button>
      </div>
    </form>
  );
}
