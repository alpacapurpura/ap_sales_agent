"use client";

import { zodResolver } from "@hookform/resolvers/zod";

import { Card, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { WithCopilot } from "@/features/copilot/components/WithCopilot";
import { useCopilotFieldSync } from "@/features/copilot/hooks/use-copilot-field-sync";

import type { BrandIdentity } from "@/features/brand/types";
import type { UseFormSetValue } from "react-hook-form";

const formSchema = z.object({
  brand_name: z.string().min(1, "El nombre de marca es requerido"),
  tagline: z.string().optional(),
  description: z.string().optional(),
  founding_year: z.string().optional(),
  website: z.string().url("Debe ser una URL válida").optional().or(z.literal("")),
  industry: z.string().optional(),
  logo_url: z.string().optional(),
  timezone: z.string().optional(),
  language: z.string().optional(),
});

interface IdentityFormProps {
  initialData: BrandIdentity;
  onSave: (data: BrandIdentity) => Promise<void>;
  isSaving: boolean;
}

export function IdentityForm({ initialData, onSave, isSaving }: IdentityFormProps) {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      brand_name: initialData.brand_name || "",
      tagline: initialData.tagline || "",
      description: initialData.description || "",
      founding_year: initialData.founding_year || "",
      website: initialData.website || "",
      industry: initialData.industry || "",
      logo_url: initialData.logo_url || "",
      timezone: initialData.timezone || "America/Lima",
      language: initialData.language || "Español",
    },
  });

  useEffect(() => {
    form.reset({
      brand_name: initialData.brand_name || "",
      tagline: initialData.tagline || "",
      description: initialData.description || "",
      founding_year: initialData.founding_year || "",
      website: initialData.website || "",
      industry: initialData.industry || "",
      logo_url: initialData.logo_url || "",
      timezone: initialData.timezone || "America/Lima",
      language: initialData.language || "Español",
    });
  }, [initialData, form]);

  // Sync copilot field updates with form
  useCopilotFieldSync(form.setValue as unknown as UseFormSetValue<Record<string, unknown>>);

  function onSubmit(values: z.infer<typeof formSchema>) {
    // Preserve existing legal fields that are not in this form
    const finalData = {
      ...initialData,
      ...values,
    };
    void onSave(finalData);
  }

  return (
    <Card className="border-none shadow-none bg-background">
      <CardContent className="px-0">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Core Identity */}
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="brand_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Nombre de Marca</FormLabel>
                      <WithCopilot
                        fieldId="brand_name"
                        fieldLabel="Nombre de Marca"
                        getValue={() => field.value || ""}
                      >
                        <FormControl>
                          <Input placeholder="Ej: Nicolify" {...field} />
                        </FormControl>
                      </WithCopilot>
                      <FormDescription>El nombre comercial público.</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="tagline"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Slogan / Tagline</FormLabel>
                      <WithCopilot
                        fieldId="tagline"
                        fieldLabel="Slogan / Tagline"
                        getValue={() => field.value || ""}
                      >
                        <FormControl>
                          <Input placeholder="Ej: Transformando el futuro..." {...field} />
                        </FormControl>
                      </WithCopilot>
                      <FormDescription>
                        La frase que va debajo de tu logo. Ej: Nike &rarr; &apos;Just Do It&apos;
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Bio de Marca</FormLabel>
                    <WithCopilot
                      fieldId="description"
                      fieldLabel="Bio de Marca"
                      getValue={() => field.value || ""}
                    >
                      <FormControl>
                        <Textarea
                          placeholder="Describe brevemente qué hace tu empresa y para quién..."
                          className="resize-none"
                          {...field}
                        />
                      </FormControl>
                    </WithCopilot>
                    <FormDescription>
                      Para perfiles de redes, SEO y presentaciones rapidas.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Context & Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="website"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Sitio Web Principal</FormLabel>
                    <WithCopilot
                      fieldId="website"
                      fieldLabel="Sitio Web Principal"
                      getValue={() => field.value || ""}
                    >
                      <FormControl>
                        <Input placeholder="https://..." {...field} />
                      </FormControl>
                    </WithCopilot>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="founding_year"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Año de Fundación</FormLabel>
                    <WithCopilot
                      fieldId="founding_year"
                      fieldLabel="Año de Fundación"
                      getValue={() => field.value || ""}
                    >
                      <FormControl>
                        <Input placeholder="Ej: 2023" {...field} />
                      </FormControl>
                    </WithCopilot>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="industry"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Industria / Nicho</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecciona una industria" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="Marketing & Agencias">Marketing & Agencias</SelectItem>
                        <SelectItem value="Coaching & Consultoría">
                          Coaching & Consultoría
                        </SelectItem>
                        <SelectItem value="Salud & Fitness">Salud & Fitness</SelectItem>
                        <SelectItem value="Inversiones & Finanzas">
                          Inversiones & Finanzas
                        </SelectItem>
                        <SelectItem value="Real Estate">Real Estate</SelectItem>
                        <SelectItem value="SaaS / Software">SaaS / Software</SelectItem>
                        <SelectItem value="E-learning / Educación">
                          E-learning / Educación
                        </SelectItem>
                        <SelectItem value="Otro">Otro</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="language"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Idioma Principal</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecciona un idioma" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="Español">Español</SelectItem>
                        <SelectItem value="Inglés">Inglés</SelectItem>
                        <SelectItem value="Portugués">Portugués</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="timezone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Zona Horaria Base</FormLabel>
                  <WithCopilot
                    fieldId="timezone"
                    fieldLabel="Zona Horaria Base"
                    getValue={() => field.value || ""}
                  >
                    <FormControl>
                      <Input placeholder="Ej: America/Lima" {...field} />
                    </FormControl>
                  </WithCopilot>
                  <FormDescription>Para saludos y agenda.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" disabled={isSaving} className="w-full">
              {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Guardar Identidad
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
