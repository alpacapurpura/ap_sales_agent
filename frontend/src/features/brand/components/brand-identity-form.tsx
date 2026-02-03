"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { BrandIdentity } from "@/lib/api/brand";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

const formSchema = z.object({
  brand_name: z.string().min(1, "El nombre de marca es requerido"),
  legal_name: z.string().optional(),
  website: z.string().url("Debe ser una URL válida").optional().or(z.literal("")),
  industry: z.string().optional(),
  logo_url: z.string().optional(), // File upload simulated as URL for now
  timezone: z.string().optional(),
  language: z.string().optional(),
});

interface BrandIdentityFormProps {
  initialData: BrandIdentity;
  onSave: (data: BrandIdentity) => Promise<void>;
  isSaving: boolean;
}

export function BrandIdentityForm({ initialData, onSave, isSaving }: BrandIdentityFormProps) {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      brand_name: initialData.brand_name || "",
      legal_name: initialData.legal_name || "",
      website: initialData.website || "",
      industry: initialData.industry || "",
      logo_url: initialData.logo_url || "",
      timezone: initialData.timezone || "America/Lima", // Default or fetch
      language: initialData.language || "Español",
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    onSave(values);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Identidad Corporativa</CardTitle>
        <CardDescription>
          Datos duros que dan legalidad y estructura a la empresa.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
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
                name="legal_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Razón Social / Legal</FormLabel>
                    <FormControl>
                      <Input placeholder="Ej: Visionarias LLC" {...field} />
                    </FormControl>
                    <FormDescription>Para facturas o contratos.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

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
                    <FormDescription>La &quot;Home&quot; del negocio.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
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
                    <FormDescription>Ayuda a calibrar el vocabulario.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

            <Button type="submit" disabled={isSaving}>
              {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Guardar Cambios
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
