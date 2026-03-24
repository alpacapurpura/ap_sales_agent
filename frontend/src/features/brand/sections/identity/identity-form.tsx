"use client";

import { useForm } from "react-hook-form";
import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { BrandIdentity } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

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

  function onSubmit(values: z.infer<typeof formSchema>) {
    // Preserve existing legal fields that are not in this form
    const finalData = {
        ...initialData,
        ...values
    };
    onSave(finalData);
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
                            <FormControl>
                            <Input placeholder="Ej: Visionarias AI" {...field} />
                            </FormControl>
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
                            <FormControl>
                            <Input placeholder="Ej: Transformando el futuro..." {...field} />
                            </FormControl>
                            <FormDescription>La frase que va debajo de tu logo. Ej: Nike &rarr; &apos;Just Do It&apos;</FormDescription>
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
                        <FormControl>
                        <Textarea 
                            placeholder="Describe brevemente qué hace tu empresa y para quién..." 
                            className="resize-none"
                            {...field} 
                        />
                        </FormControl>
                        <FormDescription>Para perfiles de redes, SEO y presentaciones rapidas.</FormDescription>
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
                    <FormControl>
                      <Input placeholder="https://..." {...field} />
                    </FormControl>
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
                    <FormControl>
                      <Input placeholder="Ej: 2023" {...field} />
                    </FormControl>
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
                            <SelectItem value="Coaching & Consultoría">Coaching & Consultoría</SelectItem>
                            <SelectItem value="Salud & Fitness">Salud & Fitness</SelectItem>
                            <SelectItem value="Inversiones & Finanzas">Inversiones & Finanzas</SelectItem>
                            <SelectItem value="Real Estate">Real Estate</SelectItem>
                            <SelectItem value="SaaS / Software">SaaS / Software</SelectItem>
                            <SelectItem value="E-learning / Educación">E-learning / Educación</SelectItem>
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
                    <FormControl>
                    <Input placeholder="Ej: America/Lima" {...field} />
                    </FormControl>
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
