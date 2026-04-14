import { useFieldArray, Control } from "react-hook-form";
import { OfferFormValues } from "@/features/offer-studio/types/schema";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Plus, Trash2, Sparkles, RefreshCw, AlertTriangle } from "lucide-react";
import TextareaAutosize from "react-textarea-autosize";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { AIAssistButton } from "../ai-assist-button";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface OfferPsychologyCardProps {
  control: Control<OfferFormValues>;
  onGenerate: () => Promise<void>;
  avatarSelected: boolean;
  isGenerating?: boolean; // Added this prop to handle loading state from parent if needed, though AIAssistButton handles it internally mostly
}

export function OfferPsychologyCard({
  control,
  onGenerate,
  avatarSelected,
  isGenerating = false,
}: OfferPsychologyCardProps) {
  const {
    fields: painPoints,
    append: addPainPoint,
    remove: removePainPoint,
  } = useFieldArray({
    control,
    name: "marketing_pain_points" as never,
  });

  const {
    fields: desires,
    append: addDesire,
    remove: removeDesire,
  } = useFieldArray({
    control,
    name: "marketing_desires" as never,
  });

  const hasContent = painPoints.length > 0 || desires.length > 0;

  return (
    <Card className="border-dashed shadow-sm overflow-hidden">
      <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0 bg-slate-50/50 dark:bg-slate-900/20 border-b">
        <CardTitle className="text-base font-medium flex items-center gap-2">
          🧠 Psicología de Ventas
        </CardTitle>

        {/* Smart AI Button Logic */}
        {hasContent && avatarSelected && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onGenerate}
                  className="h-8 w-8 text-muted-foreground hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20"
                >
                  <RefreshCw className={cn("h-4 w-4", isGenerating && "animate-spin")} />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="left">
                <p>Regenerar con IA (Sobrescribirá cambios)</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </CardHeader>

      <CardContent className="p-0">
        {/* Empty State / Prominent AI Call to Action */}
        {!hasContent && (
          <div className="flex flex-col items-center justify-center py-12 px-6 text-center space-y-4 bg-slate-50/30 dark:bg-slate-900/10">
            <div className="p-3 bg-indigo-100 dark:bg-indigo-900/30 rounded-full">
              <Sparkles className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div className="space-y-1 max-w-sm">
              <h3 className="font-semibold text-sm">Sin Psicología Definida</h3>
              <p className="text-xs text-muted-foreground">
                Define los dolores y deseos de tu avatar para que la IA pueda redactar mejores
                ofertas.
              </p>
            </div>
            <AIAssistButton
              onGenerate={onGenerate}
              isDisabled={!avatarSelected}
              disabledReason="Selecciona un Avatar primero"
              label="Generar con IA"
              className="w-full max-w-[200px]"
            />
          </div>
        )}

        {/* Content Tabs */}
        {hasContent && (
          <Tabs defaultValue="pains" className="w-full">
            <div className="border-b px-4 bg-slate-50/30 dark:bg-slate-900/10">
              <TabsList className="h-10 bg-transparent p-0 w-full justify-start gap-6">
                <TabsTrigger
                  value="pains"
                  className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-0 pb-2 h-full bg-transparent font-medium"
                >
                  Puntos de Dolor
                  <Badge
                    variant="secondary"
                    className="ml-2 text-[10px] h-5 px-1.5 min-w-[20px] justify-center"
                  >
                    {painPoints.length}
                  </Badge>
                </TabsTrigger>
                <TabsTrigger
                  value="desires"
                  className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-emerald-500 rounded-none px-0 pb-2 h-full bg-transparent font-medium"
                >
                  Deseos
                  <Badge
                    variant="secondary"
                    className="ml-2 text-[10px] h-5 px-1.5 min-w-[20px] justify-center bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                  >
                    {desires.length}
                  </Badge>
                </TabsTrigger>
              </TabsList>
            </div>

            {/* Pains Content */}
            <TabsContent
              value="pains"
              className="p-4 m-0 space-y-3 animate-in fade-in slide-in-from-left-2 duration-300"
            >
              <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                {painPoints.map((field, index) => (
                  <div key={field.id} className="flex gap-2 items-start group relative">
                    <div className="flex-1">
                      <TextareaAutosize
                        {...control.register(`marketing_pain_points.${index}`)}
                        placeholder="Describe un dolor o miedo..."
                        className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 resize-none transition-all hover:border-primary/50"
                        minRows={1}
                      />
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removePainPoint(index)}
                      className="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity absolute right-1 top-1 bg-background/80 backdrop-blur-sm"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                ))}
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="w-full text-xs h-8 border border-dashed border-muted-foreground/30 hover:bg-muted/50 text-muted-foreground"
                onClick={() => addPainPoint("")}
              >
                <Plus className="h-3 w-3 mr-1" /> Agregar Dolor Manualmente
              </Button>
            </TabsContent>

            {/* Desires Content */}
            <TabsContent
              value="desires"
              className="p-4 m-0 space-y-3 animate-in fade-in slide-in-from-right-2 duration-300"
            >
              <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                {desires.map((field, index) => (
                  <div key={field.id} className="flex gap-2 items-start group relative">
                    <div className="flex-1">
                      <TextareaAutosize
                        {...control.register(`marketing_desires.${index}`)}
                        placeholder="Describe un deseo o aspiración..."
                        className="flex w-full rounded-md border border-emerald-100 dark:border-emerald-900/50 bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-emerald-500 disabled:cursor-not-allowed disabled:opacity-50 resize-none transition-all hover:border-emerald-500/50"
                        minRows={1}
                      />
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removeDesire(index)}
                      className="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity absolute right-1 top-1 bg-background/80 backdrop-blur-sm"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                ))}
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="w-full text-xs h-8 border border-dashed border-emerald-200 dark:border-emerald-900/50 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400"
                onClick={() => addDesire("")}
              >
                <Plus className="h-3 w-3 mr-1" /> Agregar Deseo Manualmente
              </Button>
            </TabsContent>
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
}
