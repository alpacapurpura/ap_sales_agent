"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { ContactData } from "@/lib/api/brand";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

const formSchema = z.object({
  support_email: z.string().email("Email inválido").optional().or(z.literal("")),
  phone: z.string().optional(),
  address: z.string().optional(),
  social_instagram: z.string().url("URL inválida").optional().or(z.literal("")),
  social_linkedin: z.string().url("URL inválida").optional().or(z.literal("")),
  social_youtube: z.string().url("URL inválida").optional().or(z.literal("")),
  testimonials_url: z.string().url("URL inválida").optional().or(z.literal("")),
});

interface ContactDataFormProps {
  initialData: ContactData;
  onSave: (data: ContactData) => Promise<void>;
  isSaving: boolean;
}

export function ContactDataForm({ initialData, onSave, isSaving }: ContactDataFormProps) {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      support_email: initialData.support_email || "",
      phone: initialData.phone || "",
      address: initialData.address || "",
      social_instagram: initialData.social_instagram || "",
      social_linkedin: initialData.social_linkedin || "",
      social_youtube: initialData.social_youtube || "",
      testimonials_url: initialData.testimonials_url || "",
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    onSave(values);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Datos de Contacto</CardTitle>
        <CardDescription>
          Dónde encontrarnos y cómo validar que somos reales.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="support_email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email de Soporte</FormLabel>
                    <FormControl>
                      <Input placeholder="soporte@visionarias.ai" {...field} />
                    </FormControl>
                    <FormDescription>Para problemas técnicos.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="phone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Teléfono Oficial (Opcional)</FormLabel>
                    <FormControl>
                      <Input placeholder="+1 ..." {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
                control={form.control}
                name="address"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Dirección Física / Sede</FormLabel>
                    <FormControl>
                      <Input placeholder="Ciudad, País" {...field} />
                    </FormControl>
                    <FormDescription>Da confianza, aunque sea un negocio digital.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <FormField
                    control={form.control}
                    name="social_instagram"
                    render={({ field }) => (
                    <FormItem>
                        <FormLabel>Instagram URL</FormLabel>
                        <FormControl>
                        <Input placeholder="https://instagram.com/..." {...field} />
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="social_linkedin"
                    render={({ field }) => (
                    <FormItem>
                        <FormLabel>LinkedIn URL</FormLabel>
                        <FormControl>
                        <Input placeholder="https://linkedin.com/in/..." {...field} />
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="social_youtube"
                    render={({ field }) => (
                    <FormItem>
                        <FormLabel>YouTube URL</FormLabel>
                        <FormControl>
                        <Input placeholder="https://youtube.com/..." {...field} />
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                    )}
                />
            </div>

            <FormField
                control={form.control}
                name="testimonials_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Link Global de Testimonios</FormLabel>
                    <FormControl>
                      <Input placeholder="Trustpilot, Google Reviews..." {...field} />
                    </FormControl>
                    <FormDescription>Si el cliente pide pruebas generales, la IA manda esto.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

            <Button type="submit" disabled={isSaving}>
              {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Guardar Contacto
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
