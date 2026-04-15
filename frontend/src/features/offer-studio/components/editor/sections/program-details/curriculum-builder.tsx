"use client";

import type { UseFormReturn } from "react-hook-form";

interface CurriculumModule {
  title: string;
  description?: string | null;
  topics: string[];
}
import { Plus, Trash2, GripVertical, Sparkles, BookOpen } from "lucide-react";
import { useState } from "react";
import { useFieldArray } from "react-hook-form";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
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
import { Button } from "@/components/ui/button";
import { FormField, FormItem, FormLabel, FormControl } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import { ImportCurriculumDialog } from "./import-curriculum-dialog";

import type { OfferFormValues } from "../../../../types/schema";

export function CurriculumBuilder({ form }: { form: UseFormReturn<OfferFormValues> }) {
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "specific_details.curriculum",
  });

  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);

  const handleImport = (modules: CurriculumModule[]) => {
    modules.forEach((m) => append(m));
  };

  const hasContent = fields.length > 0;

  return (
    <div className="space-y-6">
      <ImportCurriculumDialog
        open={isImportDialogOpen}
        onOpenChange={setIsImportDialogOpen}
        onImport={handleImport}
      />

      {/* HEADER SECTION */}
      <div className="flex items-center justify-between pb-2 border-b border-indigo-100 dark:border-indigo-900/30">
        <div>
          <h3 className="flex items-center gap-2 text-lg font-semibold text-indigo-900 dark:text-indigo-300">
            <BookOpen className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
            Currículo del Programa
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            Diseña la estructura educativa módulo a módulo.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Smart Import Action */}
          {hasContent ? (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setIsImportDialogOpen(true)}
                    className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
                  >
                    <Sparkles className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Importar más contenido con IA</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ) : (
            <Button
              variant="outline"
              size="sm"
              className="hidden md:flex gap-2 text-indigo-600 border-indigo-200 bg-white hover:bg-indigo-50"
              onClick={() => setIsImportDialogOpen(true)}
            >
              <Sparkles className="w-4 h-4" /> Importar con IA
            </Button>
          )}

          <Button
            type="button"
            size="sm"
            onClick={() =>
              append({ title: `Módulo ${fields.length + 1}`, description: "", topics: [] })
            }
            className={cn(!hasContent && "bg-indigo-600 hover:bg-indigo-700 text-white")}
            variant={hasContent ? "default" : "secondary"}
          >
            <Plus className="w-4 h-4 mr-2" />
            {hasContent ? "Agregar" : "Nuevo Módulo"}
          </Button>
        </div>
      </div>

      {/* CONTENT BUILDER */}
      {fields.length === 0 ? (
        <div
          className="flex flex-col items-center justify-center py-12 text-muted-foreground border border-dashed rounded-lg bg-slate-50/50 dark:bg-slate-900/20 hover:bg-slate-50 transition-colors cursor-pointer group"
          onClick={() => append({ title: "Módulo 1", description: "", topics: [] })}
        >
          <div className="bg-indigo-50 dark:bg-indigo-900/20 p-3 rounded-full mb-3 group-hover:scale-110 transition-transform">
            <Plus className="h-6 w-6 text-indigo-400" />
          </div>
          <p className="font-medium text-slate-900 dark:text-slate-200">Comienza tu estructura</p>
          <p className="text-sm mt-1">Agrega un módulo manual o importa con IA</p>
          <Button
            variant="link"
            onClick={(e) => {
              e.stopPropagation();
              setIsImportDialogOpen(true);
            }}
            className="mt-2 text-indigo-600"
          >
            Probar importación mágica <Sparkles className="w-3 h-3 ml-1" />
          </Button>
        </div>
      ) : (
        <Accordion
          type="single"
          collapsible
          className="w-full space-y-0 border rounded-lg divide-y bg-white dark:bg-slate-950"
        >
          {fields.map((field, index) => (
            <CurriculumModuleItem key={field.id} index={index} form={form} remove={remove} />
          ))}
        </Accordion>
      )}
    </div>
  );
}

function CurriculumModuleItem({
  index,
  form,
  remove,
}: {
  index: number;
  form: UseFormReturn<OfferFormValues>;
  remove: (index: number) => void;
}) {
  const topics = form.watch(`specific_details.curriculum.${index}.topics`) || [];

  const addTopic = (e: React.MouseEvent) => {
    e.preventDefault();
    const current = form.getValues(`specific_details.curriculum.${index}.topics`) || [];
    form.setValue(`specific_details.curriculum.${index}.topics`, [...current, ""]);
  };

  const removeTopic = (tIndex: number) => {
    const current = form.getValues(`specific_details.curriculum.${index}.topics`) || [];
    form.setValue(
      `specific_details.curriculum.${index}.topics`,
      current.filter((_: unknown, i: number) => i !== tIndex),
    );
  };

  return (
    <AccordionItem value={`item-${index}`} className="border-b-0 px-0">
      <div className="flex items-center gap-3 py-2 px-4 hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors group/item">
        <GripVertical className="h-4 w-4 text-slate-300 cursor-move" />

        <div className="flex-1">
          <FormField
            control={form.control}
            name={`specific_details.curriculum.${index}.title`}
            render={({ field }) => (
              <FormItem className="space-y-0">
                <FormControl>
                  <Input
                    {...field}
                    className="font-medium text-sm border-transparent bg-transparent hover:bg-accent/50 hover:border-input focus-visible:bg-accent/50 px-2 h-8 transition-all"
                    placeholder="Título del Módulo"
                    onClick={(e) => e.stopPropagation()}
                  />
                </FormControl>
              </FormItem>
            )}
          />
        </div>

        <div className="flex items-center gap-1 opacity-0 group-hover/item:opacity-100 focus-within:opacity-100 transition-opacity">
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>¿Eliminar módulo?</AlertDialogTitle>
                <AlertDialogDescription>
                  Se perderán todas las lecciones de este módulo.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancelar</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => remove(index)}
                  className="bg-destructive hover:bg-destructive/90"
                >
                  Eliminar
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>

        <AccordionTrigger className="py-0 pr-2 hover:no-underline w-6 flex justify-center" />
      </div>

      <AccordionContent className="pt-0 pb-4 px-4 pl-11">
        <div className="space-y-4 pt-2">
          {/* Description */}
          <FormField
            control={form.control}
            name={`specific_details.curriculum.${index}.description`}
            render={({ field }) => (
              <FormItem className="space-y-0">
                <FormControl>
                  <div className="relative">
                    <Input
                      {...field}
                      placeholder="Objetivo principal (ej. Aprender fundamentos)"
                      className="h-8 text-xs bg-slate-50/50 dark:bg-slate-900/20 border-slate-200"
                    />
                  </div>
                </FormControl>
              </FormItem>
            )}
          />

          {/* Topics List */}
          <div className="space-y-1">
            <div className="flex items-center justify-between mb-2">
              <Label className="text-[10px] uppercase font-bold text-muted-foreground/70 tracking-wider">
                Lecciones
              </Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={addTopic}
                className="h-5 text-[10px] px-2 text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
              >
                <Plus className="w-3 h-3 mr-1" /> Agregar
              </Button>
            </div>

            <div className="space-y-1">
              {topics.map((_: unknown, tIndex: number) => (
                <div key={tIndex} className="group/topic flex items-center gap-2">
                  <div className="h-1 w-1 rounded-full bg-indigo-300" />
                  <FormField
                    control={form.control}
                    name={`specific_details.curriculum.${index}.topics.${tIndex}`}
                    render={({ field }) => (
                      <Input
                        {...field}
                        className="h-7 text-sm bg-transparent border-transparent hover:border-input focus-visible:bg-accent/50 transition-all px-2"
                        placeholder={`Lección ${tIndex + 1}`}
                      />
                    )}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeTopic(tIndex)}
                    className="h-6 w-6 opacity-0 group-hover/topic:opacity-100 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              ))}
              {topics.length === 0 && (
                <div
                  onClick={addTopic}
                  className="text-xs text-muted-foreground/50 italic py-2 px-2 border border-dashed rounded cursor-pointer hover:bg-slate-50 text-center"
                >
                  + Clic para agregar primera lección
                </div>
              )}
            </div>
          </div>
        </div>
      </AccordionContent>
    </AccordionItem>
  );
}
