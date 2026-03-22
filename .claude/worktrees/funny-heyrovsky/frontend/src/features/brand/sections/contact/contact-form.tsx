"use client";

import { useForm } from "react-hook-form";
import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { ContactData } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2 } from "lucide-react";

const formSchema = z.object({
  support_email: z.string().email("Email inválido").optional().or(z.literal("")),
  sales_email: z.string().email("Email inválido").optional().or(z.literal("")),
  phone: z.string().optional(),
  whatsapp: z.string().optional(),
  address: z.string().optional(),
  social_instagram: z.string().url("URL inválida").optional().or(z.literal("")),
  social_linkedin: z.string().url("URL inválida").optional().or(z.literal("")),
  social_youtube: z.string().url("URL inválida").optional().or(z.literal("")),
  social_tiktok: z.string().url("URL inválida").optional().or(z.literal("")),
  social_facebook: z.string().url("URL inválida").optional().or(z.literal("")),
  social_twitter: z.string().url("URL inválida").optional().or(z.literal("")),
  testimonials_url: z.string().url("URL inválida").optional().or(z.literal("")),
});

interface ContactFormProps {
  initialData: ContactData;
  onSave: (data: ContactData) => Promise<void>;
  isSaving: boolean;
}

export function ContactForm({ initialData, onSave, isSaving }: ContactFormProps) {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      support_email: initialData.support_email || "",
      sales_email: initialData.sales_email || "",
      phone: initialData.phone || "",
      whatsapp: initialData.whatsapp || "",
      address: initialData.address || "",
      social_instagram: initialData.social_instagram || "",
      social_linkedin: initialData.social_linkedin || "",
      social_youtube: initialData.social_youtube || "",
      social_tiktok: initialData.social_tiktok || "",
      social_facebook: initialData.social_facebook || "",
      social_twitter: initialData.social_twitter || "",
      testimonials_url: initialData.testimonials_url || "",
    },
  });

  useEffect(() => {
    form.reset({
      support_email: initialData.support_email || "",
      sales_email: initialData.sales_email || "",
      phone: initialData.phone || "",
      whatsapp: initialData.whatsapp || "",
      address: initialData.address || "",
      social_instagram: initialData.social_instagram || "",
      social_linkedin: initialData.social_linkedin || "",
      social_youtube: initialData.social_youtube || "",
      social_tiktok: initialData.social_tiktok || "",
      social_facebook: initialData.social_facebook || "",
      social_twitter: initialData.social_twitter || "",
      testimonials_url: initialData.testimonials_url || "",
    });
  }, [initialData, form]);

  function onSubmit(values: z.infer<typeof formSchema>) {
    onSave(values);
  }

  return (
    <Card className="border-none shadow-none">
      <CardHeader className="px-0 pt-0">
        <CardTitle>Canales de Contacto</CardTitle>
        <CardDescription>
          Configura cómo te encuentran los clientes y el soporte.
        </CardDescription>
      </CardHeader>
      <CardContent className="px-0">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            
            <Tabs defaultValue="direct" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="direct">Contacto Directo</TabsTrigger>
                    <TabsTrigger value="social">Redes Sociales</TabsTrigger>
                </TabsList>
                
                <TabsContent value="direct" className="space-y-4 pt-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <FormField
                            control={form.control}
                            name="support_email"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Email de Soporte</FormLabel>
                                <FormControl>
                                <Input placeholder="soporte@..." {...field} />
                                </FormControl>
                                <FormDescription>Para dudas técnicas o clientes.</FormDescription>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="sales_email"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Email de Ventas</FormLabel>
                                <FormControl>
                                <Input placeholder="ventas@..." {...field} />
                                </FormControl>
                                <FormDescription>Para leads y nuevos negocios.</FormDescription>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <FormField
                            control={form.control}
                            name="phone"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Teléfono Oficial</FormLabel>
                                <FormControl>
                                <Input placeholder="+51 999..." {...field} />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="whatsapp"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>WhatsApp Business</FormLabel>
                                <FormControl>
                                <Input placeholder="https://wa.me/..." {...field} />
                                </FormControl>
                                <FormDescription>Enlace directo a chat.</FormDescription>
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
                            <Input placeholder="Av. Principal 123, Ciudad" {...field} />
                            </FormControl>
                            <FormDescription>Útil para Google Maps y confianza.</FormDescription>
                            <FormMessage />
                        </FormItem>
                        )}
                    />
                </TabsContent>

                <TabsContent value="social" className="space-y-4 pt-4">
                     <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <FormField
                            control={form.control}
                            name="social_instagram"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Instagram</FormLabel>
                                <FormControl>
                                <Input placeholder="https://instagram.com/..." {...field} />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="social_tiktok"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>TikTok</FormLabel>
                                <FormControl>
                                <Input placeholder="https://tiktok.com/@..." {...field} />
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
                                <FormLabel>LinkedIn</FormLabel>
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
                                <FormLabel>YouTube</FormLabel>
                                <FormControl>
                                <Input placeholder="https://youtube.com/..." {...field} />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="social_facebook"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>Facebook</FormLabel>
                                <FormControl>
                                <Input placeholder="https://facebook.com/..." {...field} />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                            )}
                        />
                         <FormField
                            control={form.control}
                            name="social_twitter"
                            render={({ field }) => (
                            <FormItem>
                                <FormLabel>X (Twitter)</FormLabel>
                                <FormControl>
                                <Input placeholder="https://x.com/..." {...field} />
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
                            <FormDescription>Repositorio externo de prueba social.</FormDescription>
                            <FormMessage />
                        </FormItem>
                        )}
                    />
                </TabsContent>
            </Tabs>

            <Button type="submit" disabled={isSaving} className="w-full">
              {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Guardar Contacto
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
