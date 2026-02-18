"use client";

import { useForm, useFieldArray } from "react-hook-form";
import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import type { BrandVisuals } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Plus, Trash2, GripVertical } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { LogoKit } from "./logo-kit";

const formSchema = z.object({
  logos: z.object({
      primary: z.string().optional(),
      secondary: z.string().optional(),
      dark_mode: z.string().optional(),
      light_mode: z.string().optional(),
  }).optional(),
  primary_color: z.string().min(1, "El color primario es requerido"),
  accent_color: z.string().min(1, "El color de acento es requerido"),
  background_color: z.string().optional(),
  text_primary_color: z.string().optional(),
  text_on_primary: z.string().optional(),
  font_heading: z.string().optional(),
  font_body: z.string().optional(),
  design_style: z.string().optional(),
  usage_guidelines: z.array(z.string()).optional(),
});

interface BrandVisualsFormProps {
  initialData: BrandVisuals;
  onSave: (data: BrandVisuals) => Promise<void>;
  isSaving: boolean;
}

export function BrandVisualsForm({ initialData, onSave, isSaving }: BrandVisualsFormProps) {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      logos: initialData.logos || {},
      primary_color: initialData.primary_color || "#000000",
      accent_color: initialData.accent_color || "#ffffff",
      background_color: initialData.background_color || "#ffffff",
      text_primary_color: initialData.text_primary_color || "#000000",
      text_on_primary: initialData.text_on_primary || "#ffffff",
      font_heading: initialData.font_heading || "",
      font_body: initialData.font_body || "",
      design_style: initialData.design_style || "",
      usage_guidelines: initialData.usage_guidelines || [],
    },
  });

  useEffect(() => {
    form.reset({
      logos: initialData.logos || {},
      primary_color: initialData.primary_color || "#000000",
      accent_color: initialData.accent_color || "#ffffff",
      background_color: initialData.background_color || "#ffffff",
      text_primary_color: initialData.text_primary_color || "#000000",
      text_on_primary: initialData.text_on_primary || "#ffffff",
      font_heading: initialData.font_heading || "",
      font_body: initialData.font_body || "",
      design_style: initialData.design_style || "",
      usage_guidelines: initialData.usage_guidelines || [],
    });
  }, [initialData, form]);

  // Dynamic fields for guidelines
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    // @ts-ignore - usage_guidelines is simple array of strings, but react-hook-form wants objects. 
    // We will handle the mapping in render or schema if needed.
    // Actually simpler approach for string array: use an object wrapper in schema or just map manual inputs?
    // Let's stick to simple field array if possible, but RHF usually needs objects {id, value}.
    // For string array, RHF is tricky. Let's use a wrapper component or map manually if array is small.
    // Better: RHF expects objects. Let's define schema as array of objects { text: string } and map back/forth.
    // Wait, let's keep it simple. If we change schema, we break type.
    // Let's try to just map the form values.
    name: "usage_guidelines" as any, 
  });
  
  // NOTE: react-hook-form useFieldArray with primitive arrays is tricky.
  // Standard workaround: map data to { value: string } objects for form, then map back on submit.
  // BUT to avoid complex refactor now, let's just use a simple state or controlled inputs if array is small.
  // Actually, let's use the 'fields' from useFieldArray but since we passed simple strings, 
  // RHF wraps them in objects internally { id, ... }.
  // Let's adjust the schema slightly to be robust? No, schema must match API.
  // Let's use a separate component for the list to keep this clean.
  
  // Actually, for speed and reliability given the "string[]" type:
  // Let's just render the array from form.watch() and use setValue to update.
  const guidelines = form.watch("usage_guidelines") || [];

  const addGuideline = () => {
    const current = form.getValues("usage_guidelines") || [];
    form.setValue("usage_guidelines", [...current, ""]);
  };

  const removeGuideline = (index: number) => {
    const current = form.getValues("usage_guidelines") || [];
    const updated = current.filter((_, i) => i !== index);
    form.setValue("usage_guidelines", updated);
  };

  const updateGuideline = (index: number, value: string) => {
    const current = form.getValues("usage_guidelines") || [];
    const updated = [...current];
    updated[index] = value;
    form.setValue("usage_guidelines", updated);
  };


  function onSubmit(values: z.infer<typeof formSchema>) {
    // Merge logos to ensure we don't lose existing ones if form state is partial
    const mergedLogos = {
        ...(initialData.logos || {}),
        ...(values.logos || {})
    };

    const fullData: BrandVisuals = {
      ...initialData,
      ...values,
      logos: mergedLogos,
      background_color: values.background_color || "#ffffff",
      text_primary_color: values.text_primary_color || "#000000",
      text_on_primary: values.text_on_primary || "#ffffff",
      font_heading: values.font_heading || "",
      font_body: values.font_body || "",
      design_style: values.design_style || "",
      // filter empty strings
      usage_guidelines: values.usage_guidelines?.filter(g => g.trim() !== "") || [],
    };
    onSave(fullData);
  }

  // Helper for color inputs
  const ColorInput = ({ label, name, desc }: { label: string, name: "primary_color" | "accent_color" | "background_color" | "text_primary_color" | "text_on_primary", desc?: string }) => (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{label}</FormLabel>
          <div className="flex gap-2 items-center">
            <div 
                className="w-10 h-10 rounded border overflow-hidden shrink-0 shadow-sm"
                style={{ backgroundColor: field.value }}
            >
                <input 
                    type="color" 
                    className="w-[150%] h-[150%] -m-[25%] cursor-pointer opacity-0"
                    {...field}
                />
            </div>
            <FormControl>
              <Input placeholder="#000000" {...field} className="font-mono" />
            </FormControl>
          </div>
          {desc && <FormDescription>{desc}</FormDescription>}
          <FormMessage />
        </FormItem>
      )}
    />
  );

  return (
    <Card className="border-none shadow-none bg-background">
      <CardContent className="p-0">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            
            {/* 0. Logo Kit */}
            <div className="space-y-4">
                <div className="flex items-center gap-2 mb-2">
                    <div className="h-4 w-1 bg-primary rounded-full" />
                    <h3 className="font-semibold text-sm uppercase tracking-wider text-foreground">Identidad de Marca</h3>
                </div>
                
                <div className="pl-3 border-l-2 border-muted ml-1.5">
                    <FormField
                        control={form.control}
                        name="logos"
                        render={({ field }) => (
                            <FormItem>
                                <FormControl>
                                    <LogoKit 
                                        logos={field.value || {}} 
                                        onChange={field.onChange} 
                                    />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                        )}
                    />
                </div>
            </div>

            <div className="h-px bg-border" />

            {/* 1. Colors Section */}
            <div className="space-y-4">
                <div className="flex items-center gap-2 mb-2">
                    <div className="h-4 w-1 bg-primary rounded-full" />
                    <h3 className="font-semibold text-sm uppercase tracking-wider text-foreground">Paleta Cromática</h3>
                </div>
                
                <div className="grid grid-cols-1 gap-6 pl-3 border-l-2 border-muted ml-1.5">
                    <ColorInput 
                        label="Color Primario" 
                        name="primary_color" 
                        desc="El color principal de tu marca." 
                    />
                    <ColorInput 
                        label="Color de Acento" 
                        name="accent_color" 
                        desc="Para botones y destacados." 
                    />
                    <ColorInput 
                        label="Color de Fondo" 
                        name="background_color" 
                        desc="Generalmente blanco o neutro." 
                    />
                    <ColorInput 
                        label="Texto Principal" 
                        name="text_primary_color" 
                        desc="Color para lectura (párrafos)." 
                    />
                    <ColorInput 
                        label="Texto sobre Primario" 
                        name="text_on_primary" 
                        desc="Color del texto dentro de botones primarios." 
                    />
                </div>
            </div>

            <div className="h-px bg-border" />

            {/* 2. Typography Section */}
            <div className="space-y-4">
                <div className="flex items-center gap-2 mb-2">
                    <div className="h-4 w-1 bg-primary rounded-full" />
                    <h3 className="font-semibold text-sm uppercase tracking-wider text-foreground">Tipografía</h3>
                </div>
                
                <div className="grid grid-cols-1 gap-4 pl-3 border-l-2 border-muted ml-1.5">
                    <FormField
                        control={form.control}
                        name="font_heading"
                        render={({ field }) => (
                        <FormItem>
                            <FormLabel>Fuente de Títulos</FormLabel>
                            <FormControl>
                            <Input placeholder="Ej: Inter, Playfair Display..." {...field} />
                            </FormControl>
                            <FormDescription>Nombre exacto de Google Fonts.</FormDescription>
                            <FormMessage />
                        </FormItem>
                        )}
                    />
                    <FormField
                        control={form.control}
                        name="font_body"
                        render={({ field }) => (
                        <FormItem>
                            <FormLabel>Fuente de Cuerpo</FormLabel>
                            <FormControl>
                            <Input placeholder="Ej: Lato, Roboto..." {...field} />
                            </FormControl>
                            <FormDescription>Debe ser legible en párrafos largos.</FormDescription>
                            <FormMessage />
                        </FormItem>
                        )}
                    />
                </div>
            </div>

            <div className="h-px bg-border" />

            {/* 3. Context & Guidelines */}
            <div className="space-y-6">
                <div className="flex items-center gap-2 mb-2">
                    <div className="h-4 w-1 bg-primary rounded-full" />
                    <h3 className="font-semibold text-sm uppercase tracking-wider text-foreground">Contexto & Reglas</h3>
                </div>

                <div className="pl-3 border-l-2 border-muted ml-1.5 space-y-6">
                    <FormField
                        control={form.control}
                        name="design_style"
                        render={({ field }) => (
                        <FormItem>
                            <FormLabel>Estilo de Diseño</FormLabel>
                            <FormControl>
                            <Input placeholder="Ej: Minimalista, Corporativo, Disruptivo..." {...field} />
                            </FormControl>
                            <FormDescription>Describe la vibra general de tu marca.</FormDescription>
                            <FormMessage />
                        </FormItem>
                        )}
                    />

                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <Label>Guías de Uso (Detectadas por IA)</Label>
                            <Button  
                                type="button" 
                                variant="outline" 
                                size="sm" 
                                onClick={addGuideline}
                                className="h-8 text-xs"
                            >
                                <Plus className="w-3 h-3 mr-1" /> Agregar Regla
                            </Button>
                        </div>
                        
                        <div className="space-y-2">
                            {guidelines.map((rule, index) => (
                                <div key={index} className="flex gap-2 items-start group">
                                    <div className="mt-3 w-1.5 h-1.5 rounded-full bg-primary/40 shrink-0" />
                                    <Textarea 
                                        value={rule} 
                                        onChange={(e) => updateGuideline(index, e.target.value)}
                                        className="min-h-[2.5rem] py-2 resize-none text-sm"
                                        placeholder="Escribe una regla de uso..."
                                    />
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => removeGuideline(index)}
                                        className="h-9 w-9 text-muted-foreground hover:text-destructive shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>
                            ))}
                            {guidelines.length === 0 && (
                                <p className="text-sm text-muted-foreground italic py-2">
                                    No hay reglas definidas. Agrega una manual o extrae desde la web.
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            <Button type="submit" disabled={isSaving} className="w-full">
              {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Guardar Identidad Visual
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
