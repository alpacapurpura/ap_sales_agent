"use client";

import { useForm } from "react-hook-form";
import { useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import type { BrandVisuals } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Loader2, Plus, Trash2, ChevronDown } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
const formSchema = z.object({
  // Colors (core)
  primary_color: z.string().min(1, "El color primario es requerido"),
  secondary_color: z.string().optional(),
  accent_color: z.string().min(1, "El color de acento es requerido"),
  background_color: z.string().optional(),
  surface_color: z.string().optional(),
  text_primary_color: z.string().optional(),
  text_secondary_color: z.string().optional(),
  text_on_primary: z.string().optional(),
  text_on_secondary: z.string().optional(),
  // Colors (extended)
  color_palette: z.array(z.string()).optional(),
  neutral_colors: z.array(z.string()).optional(),
  semantic_colors: z.object({
    success: z.string().optional(),
    error: z.string().optional(),
    warning: z.string().optional(),
    info: z.string().optional(),
  }).optional(),
  gradient_definitions: z.array(z.string()).optional(),
  color_usage_rules: z.string().optional(),
  // Typography
  font_heading: z.string().optional(),
  font_body: z.string().optional(),
  font_accent: z.string().optional(),
  // Design System
  border_radius_style: z.string().optional(),
  shadow_style: z.string().optional(),
  spacing_base: z.string().optional(),
  visual_density: z.string().optional(),
  // Visual Personality
  brand_mood: z.object({
    adjectives: z.array(z.string()).optional(),
    energy: z.string().optional(),
  }).optional(),
  design_style: z.string().optional(),
  visual_references: z.string().optional(),
  photography_style: z.string().optional(),
  icon_style: z.string().optional(),
  // Guidelines
  usage_guidelines: z.array(z.string()).optional(),
});

interface VisualsFormProps {
  initialData: BrandVisuals;
  onSave: (data: BrandVisuals) => Promise<void>;
  isSaving: boolean;
}

// Helper for color inputs
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ColorInput({ label, name, desc, control }: { label: string; name: any; desc?: string; control: any }) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{label}</FormLabel>
          <div className="flex gap-2 items-center">
            <div
              className="w-10 h-10 rounded border overflow-hidden shrink-0 shadow-sm"
              style={{ backgroundColor: field.value || "#ffffff" }}
            >
              <input
                type="color"
                className="w-[150%] h-[150%] -m-[25%] cursor-pointer opacity-0"
                value={field.value || "#ffffff"}
                onChange={field.onChange}
              />
            </div>
            <FormControl>
              <Input placeholder="#000000" {...field} value={field.value || ""} className="font-mono" />
            </FormControl>
          </div>
          {desc && <FormDescription>{desc}</FormDescription>}
          <FormMessage />
        </FormItem>
      )}
    />
  );
}

export function VisualsForm({ initialData, onSave, isSaving }: VisualsFormProps) {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: getDefaults(initialData),
  });

  useEffect(() => {
    form.reset(getDefaults(initialData));
  }, [initialData, form]);

  const guidelines = form.watch("usage_guidelines") || [];
  const colorPalette = form.watch("color_palette") || [];
  const neutralColors = form.watch("neutral_colors") || [];
  const gradients = form.watch("gradient_definitions") || [];
  const moodAdjectives = form.watch("brand_mood.adjectives") || [];

  // --- List helpers ---
  const addToList = (field: "usage_guidelines" | "color_palette" | "neutral_colors" | "gradient_definitions", defaultVal = "") => {
    const current = form.getValues(field) || [];
    form.setValue(field, [...current, defaultVal]);
  };

  const removeFromList = (field: "usage_guidelines" | "color_palette" | "neutral_colors" | "gradient_definitions", index: number) => {
    const current = form.getValues(field) || [];
    form.setValue(field, current.filter((_, i) => i !== index));
  };

  const updateInList = (field: "usage_guidelines" | "color_palette" | "neutral_colors" | "gradient_definitions", index: number, value: string) => {
    const current = form.getValues(field) || [];
    const updated = [...current];
    updated[index] = value;
    form.setValue(field, updated);
  };

  const addMoodAdjective = () => {
    const current = form.getValues("brand_mood.adjectives") || [];
    form.setValue("brand_mood.adjectives", [...current, ""]);
  };

  const removeMoodAdjective = (index: number) => {
    const current = form.getValues("brand_mood.adjectives") || [];
    form.setValue("brand_mood.adjectives", current.filter((_, i) => i !== index));
  };

  const updateMoodAdjective = (index: number, value: string) => {
    const current = form.getValues("brand_mood.adjectives") || [];
    const updated = [...current];
    updated[index] = value;
    form.setValue("brand_mood.adjectives", updated);
  };


  function onSubmit(values: z.infer<typeof formSchema>) {
    const fullData: BrandVisuals = {
      ...initialData,
      ...values,
      usage_guidelines: values.usage_guidelines?.filter(g => g.trim() !== "") || [],
      color_palette: values.color_palette?.filter(c => c.trim() !== "") || [],
      neutral_colors: values.neutral_colors?.filter(c => c.trim() !== "") || [],
      gradient_definitions: values.gradient_definitions?.filter(g => g.trim() !== "") || [],
      brand_mood: {
        adjectives: values.brand_mood?.adjectives?.filter(a => a.trim() !== "") || [],
        energy: (values.brand_mood?.energy as "low" | "medium" | "high") || undefined,
      },
    };
    onSave(fullData);
  }

  // Collapsible section wrapper
  const CollapsibleSection = ({ title, children, defaultOpen = false }: { title: string, children: React.ReactNode, defaultOpen?: boolean }) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);
    return (
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger className="flex items-center gap-2 w-full py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
          <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? '' : '-rotate-90'}`} />
          {title}
        </CollapsibleTrigger>
        <CollapsibleContent className="pt-2 space-y-4">
          {children}
        </CollapsibleContent>
      </Collapsible>
    );
  };

  return (
    <Card className="border-none shadow-none bg-background">
      <CardContent className="p-0">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">

            {/* 1. Colors Section */}
            <div className="space-y-4">
                <div className="flex items-center gap-2 mb-2">
                    <div className="h-4 w-1 bg-primary rounded-full" />
                    <h3 className="font-semibold text-sm uppercase tracking-wider text-foreground">Paleta Cromatica</h3>
                </div>

                <div className="space-y-6 pl-3 border-l-2 border-muted ml-1.5">
                    {/* Main brand colors */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <ColorInput label="Primario" name="primary_color" desc="Color principal de marca." control={form.control} />
                        <ColorInput label="Secundario" name="secondary_color" desc="2do color de marca." control={form.control} />
                        <ColorInput label="Acento" name="accent_color" desc="Highlights y CTAs." control={form.control} />
                    </div>

                    {/* Background colors */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <ColorInput label="Fondo" name="background_color" desc="Fondo principal." control={form.control} />
                        <ColorInput label="Superficie" name="surface_color" desc="Cards y modales." control={form.control} />
                    </div>

                    {/* Text colors */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <ColorInput label="Texto Principal" name="text_primary_color" desc="Parrafos." control={form.control} />
                        <ColorInput label="Texto Secundario" name="text_secondary_color" desc="Subtitulos." control={form.control} />
                        <ColorInput label="Texto sobre Primario" name="text_on_primary" desc="Texto en botones primarios." control={form.control} />
                        <ColorInput label="Texto sobre Secundario" name="text_on_secondary" desc="Texto sobre secondary." control={form.control} />
                    </div>

                    {/* Extended Palette (collapsible) */}
                    <CollapsibleSection title="Paleta Extendida">
                        <div className="space-y-3">
                            <div className="flex justify-between items-center">
                                <Label className="text-xs text-muted-foreground">Colores adicionales de marca (HEX)</Label>
                                <Button type="button" variant="outline" size="sm" onClick={() => addToList("color_palette", "#")} className="h-7 text-xs">
                                    <Plus className="w-3 h-3 mr-1" /> Color
                                </Button>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {colorPalette.map((color, i) => (
                                    <div key={i} className="flex items-center gap-1 border rounded-md p-1">
                                        <div className="w-6 h-6 rounded border" style={{ backgroundColor: color }} />
                                        <Input
                                            value={color}
                                            onChange={(e) => updateInList("color_palette", i, e.target.value)}
                                            className="w-24 h-7 text-xs font-mono"
                                        />
                                        <button type="button" onClick={() => removeFromList("color_palette", i)} className="text-muted-foreground hover:text-destructive">
                                            <Trash2 className="w-3 h-3" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="space-y-3">
                            <div className="flex justify-between items-center">
                                <Label className="text-xs text-muted-foreground">Neutros (grises, borders)</Label>
                                <Button type="button" variant="outline" size="sm" onClick={() => addToList("neutral_colors", "#")} className="h-7 text-xs">
                                    <Plus className="w-3 h-3 mr-1" /> Neutro
                                </Button>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {neutralColors.map((color, i) => (
                                    <div key={i} className="flex items-center gap-1 border rounded-md p-1">
                                        <div className="w-6 h-6 rounded border" style={{ backgroundColor: color }} />
                                        <Input
                                            value={color}
                                            onChange={(e) => updateInList("neutral_colors", i, e.target.value)}
                                            className="w-24 h-7 text-xs font-mono"
                                        />
                                        <button type="button" onClick={() => removeFromList("neutral_colors", i)} className="text-muted-foreground hover:text-destructive">
                                            <Trash2 className="w-3 h-3" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </CollapsibleSection>

                    {/* Semantic Colors (collapsible) */}
                    <CollapsibleSection title="Colores Semanticos">
                        <div className="grid grid-cols-2 gap-4">
                            <ColorInput label="Success" name="semantic_colors.success" control={form.control} />
                            <ColorInput label="Error" name="semantic_colors.error" control={form.control} />
                            <ColorInput label="Warning" name="semantic_colors.warning" control={form.control} />
                            <ColorInput label="Info" name="semantic_colors.info" control={form.control} />
                        </div>
                    </CollapsibleSection>

                    {/* Gradients (collapsible) */}
                    <CollapsibleSection title="Gradientes">
                        <div className="space-y-3">
                            <div className="flex justify-between items-center">
                                <Label className="text-xs text-muted-foreground">Definiciones CSS de gradientes</Label>
                                <Button type="button" variant="outline" size="sm" onClick={() => addToList("gradient_definitions")} className="h-7 text-xs">
                                    <Plus className="w-3 h-3 mr-1" /> Gradiente
                                </Button>
                            </div>
                            {gradients.map((grad, i) => (
                                <div key={i} className="flex gap-2 items-start group">
                                    <div className="w-12 h-8 rounded border shrink-0" style={{ background: grad || "transparent" }} />
                                    <Input
                                        value={grad}
                                        onChange={(e) => updateInList("gradient_definitions", i, e.target.value)}
                                        placeholder="linear-gradient(135deg, #6B73FF, #000DFF)"
                                        className="text-xs font-mono"
                                    />
                                    <button type="button" onClick={() => removeFromList("gradient_definitions", i)} className="text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </CollapsibleSection>

                    {/* Color Usage Rules */}
                    <FormField
                        control={form.control}
                        name="color_usage_rules"
                        render={({ field }) => (
                        <FormItem>
                            <FormLabel>Reglas de Uso de Color</FormLabel>
                            <FormControl>
                                <Textarea placeholder="Ej: 60% fondo blanco, 30% purpura en headers, 10% naranja en CTAs..." {...field} value={field.value || ""} className="min-h-[3rem] text-sm" />
                            </FormControl>
                            <FormDescription>Distribucion 60-30-10 observada.</FormDescription>
                            <FormMessage />
                        </FormItem>
                        )}
                    />
                </div>
            </div>

            <div className="h-px bg-border" />

            {/* 2. Typography Section */}
            <div className="space-y-4">
                <div className="flex items-center gap-2 mb-2">
                    <div className="h-4 w-1 bg-primary rounded-full" />
                    <h3 className="font-semibold text-sm uppercase tracking-wider text-foreground">Tipografia</h3>
                </div>

                <div className="space-y-4 pl-3 border-l-2 border-muted ml-1.5">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <FormField
                            control={form.control}
                            name="font_heading"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Titulos</FormLabel>
                                <FormControl>
                                <Input placeholder="Ej: Inter, Playfair Display..." {...field} />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="font_body"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Cuerpo</FormLabel>
                                <FormControl>
                                <Input placeholder="Ej: Lato, Roboto..." {...field} />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="font_accent"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Decorativa</FormLabel>
                                <FormControl>
                                <Input placeholder="Font display/accent..." {...field} value={field.value || ""} />
                                </FormControl>
                                <FormDescription>Solo si difiere de titulos.</FormDescription>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                    </div>
                </div>
            </div>

            <div className="h-px bg-border" />

            {/* 3. Design System */}
            <div className="space-y-4">
                <div className="flex items-center gap-2 mb-2">
                    <div className="h-4 w-1 bg-primary rounded-full" />
                    <h3 className="font-semibold text-sm uppercase tracking-wider text-foreground">Sistema de Diseno</h3>
                </div>

                <div className="space-y-4 pl-3 border-l-2 border-muted ml-1.5">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <FormField
                            control={form.control}
                            name="border_radius_style"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Estilo de Bordes</FormLabel>
                                <Select onValueChange={field.onChange} value={field.value || ""}>
                                    <FormControl>
                                        <SelectTrigger><SelectValue placeholder="Seleccionar..." /></SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                        <SelectItem value="sharp">Sharp (0-2px)</SelectItem>
                                        <SelectItem value="rounded">Rounded (4-8px)</SelectItem>
                                        <SelectItem value="pill">Pill (16px+)</SelectItem>
                                        <SelectItem value="mixed">Mixed</SelectItem>
                                    </SelectContent>
                                </Select>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="shadow_style"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Estilo de Sombras</FormLabel>
                                <Select onValueChange={field.onChange} value={field.value || ""}>
                                    <FormControl>
                                        <SelectTrigger><SelectValue placeholder="Seleccionar..." /></SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                        <SelectItem value="none">Sin sombras</SelectItem>
                                        <SelectItem value="subtle">Sutiles</SelectItem>
                                        <SelectItem value="moderate">Moderadas</SelectItem>
                                        <SelectItem value="prominent">Prominentes</SelectItem>
                                    </SelectContent>
                                </Select>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="spacing_base"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Spacing Base</FormLabel>
                                <FormControl>
                                    <Input placeholder="8px" {...field} value={field.value || ""} />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="visual_density"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Densidad Visual</FormLabel>
                                <Select onValueChange={field.onChange} value={field.value || ""}>
                                    <FormControl>
                                        <SelectTrigger><SelectValue placeholder="Seleccionar..." /></SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                        <SelectItem value="compact">Compacto</SelectItem>
                                        <SelectItem value="comfortable">Comodo</SelectItem>
                                        <SelectItem value="spacious">Espacioso</SelectItem>
                                    </SelectContent>
                                </Select>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                    </div>
                </div>
            </div>

            <div className="h-px bg-border" />

            {/* 4. Visual Personality */}
            <div className="space-y-4">
                <div className="flex items-center gap-2 mb-2">
                    <div className="h-4 w-1 bg-primary rounded-full" />
                    <h3 className="font-semibold text-sm uppercase tracking-wider text-foreground">Personalidad Visual</h3>
                </div>

                <div className="space-y-4 pl-3 border-l-2 border-muted ml-1.5">
                    {/* Brand Mood */}
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <Label>Adjetivos de Marca</Label>
                            <Button type="button" variant="outline" size="sm" onClick={addMoodAdjective} className="h-7 text-xs">
                                <Plus className="w-3 h-3 mr-1" /> Adjetivo
                            </Button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {moodAdjectives.map((adj, i) => (
                                <div key={i} className="flex items-center gap-1 border rounded-full px-2 py-1">
                                    <Input
                                        value={adj}
                                        onChange={(e) => updateMoodAdjective(i, e.target.value)}
                                        className="w-28 h-6 text-xs border-none shadow-none p-0 focus-visible:ring-0"
                                        placeholder="audaz..."
                                    />
                                    <button type="button" onClick={() => removeMoodAdjective(i)} className="text-muted-foreground hover:text-destructive">
                                        <Trash2 className="w-3 h-3" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <FormField
                            control={form.control}
                            name="brand_mood.energy"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Energia</FormLabel>
                                <Select onValueChange={field.onChange} value={field.value || ""}>
                                    <FormControl>
                                        <SelectTrigger><SelectValue placeholder="Seleccionar..." /></SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                        <SelectItem value="low">Baja (sereno/minimalista)</SelectItem>
                                        <SelectItem value="medium">Media (profesional)</SelectItem>
                                        <SelectItem value="high">Alta (energetico)</SelectItem>
                                    </SelectContent>
                                </Select>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="design_style"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Estilo de Diseno</FormLabel>
                                <FormControl>
                                <Input placeholder="Ej: Minimalista, Corporativo..." {...field} />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="photography_style"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Estilo Fotografico</FormLabel>
                                <Select onValueChange={field.onChange} value={field.value || ""}>
                                    <FormControl>
                                        <SelectTrigger><SelectValue placeholder="Seleccionar..." /></SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                        <SelectItem value="lifestyle">Lifestyle</SelectItem>
                                        <SelectItem value="product">Producto</SelectItem>
                                        <SelectItem value="abstract">Abstracto</SelectItem>
                                        <SelectItem value="minimal">Minimal</SelectItem>
                                        <SelectItem value="editorial">Editorial</SelectItem>
                                    </SelectContent>
                                </Select>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="icon_style"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Estilo de Iconos</FormLabel>
                                <Select onValueChange={field.onChange} value={field.value || ""}>
                                    <FormControl>
                                        <SelectTrigger><SelectValue placeholder="Seleccionar..." /></SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                        <SelectItem value="outlined">Outlined</SelectItem>
                                        <SelectItem value="filled">Filled</SelectItem>
                                        <SelectItem value="duotone">Duotone</SelectItem>
                                    </SelectContent>
                                </Select>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                    </div>

                    <FormField
                        control={form.control}
                        name="visual_references"
                        render={({ field }) => (
                        <FormItem>
                            <FormLabel>Referencias Visuales</FormLabel>
                            <FormControl>
                                <Textarea placeholder="Ej: Similar a Apple en minimalismo + Stripe en gradientes..." {...field} value={field.value || ""} className="min-h-[3rem] text-sm" />
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                        )}
                    />
                </div>
            </div>

            <div className="h-px bg-border" />

            {/* 5. Usage Guidelines */}
            <div className="space-y-6">
                <div className="flex items-center gap-2 mb-2">
                    <div className="h-4 w-1 bg-primary rounded-full" />
                    <h3 className="font-semibold text-sm uppercase tracking-wider text-foreground">Reglas de Uso</h3>
                </div>

                <div className="pl-3 border-l-2 border-muted ml-1.5 space-y-3">
                    <div className="flex justify-between items-center">
                        <Label>Guias de Uso (Detectadas por IA)</Label>
                        <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => addToList("usage_guidelines")}
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
                                    onChange={(e) => updateInList("usage_guidelines", index, e.target.value)}
                                    className="min-h-[2.5rem] py-2 resize-none text-sm"
                                    placeholder="Escribe una regla de uso..."
                                />
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => removeFromList("usage_guidelines", index)}
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

function getDefaults(data: BrandVisuals) {
  return {
    primary_color: data.primary_color || "#000000",
    secondary_color: data.secondary_color || "",
    accent_color: data.accent_color || "#ffffff",
    background_color: data.background_color || "#ffffff",
    surface_color: data.surface_color || "",
    text_primary_color: data.text_primary_color || "#000000",
    text_secondary_color: data.text_secondary_color || "",
    text_on_primary: data.text_on_primary || "#ffffff",
    text_on_secondary: data.text_on_secondary || "",
    color_palette: data.color_palette || [],
    neutral_colors: data.neutral_colors || [],
    semantic_colors: data.semantic_colors || { success: "", error: "", warning: "", info: "" },
    gradient_definitions: data.gradient_definitions || [],
    color_usage_rules: data.color_usage_rules || "",
    font_heading: data.font_heading || "",
    font_body: data.font_body || "",
    font_accent: data.font_accent || "",
    border_radius_style: data.border_radius_style || "",
    shadow_style: data.shadow_style || "",
    spacing_base: data.spacing_base || "",
    visual_density: data.visual_density || "",
    brand_mood: {
      adjectives: data.brand_mood?.adjectives || [],
      energy: data.brand_mood?.energy || "",
    },
    design_style: data.design_style || "",
    visual_references: data.visual_references || "",
    photography_style: data.photography_style || "",
    icon_style: data.icon_style || "",
    usage_guidelines: data.usage_guidelines || [],
  };
}
