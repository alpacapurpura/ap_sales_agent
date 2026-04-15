"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import * as z from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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

import type { BrandIdentity } from "@/features/brand/types";

const formSchema = z.object({
  legal_name: z.string().optional(),
  tax_id: z.string().optional(),
  fiscal_address: z.string().optional(),
  legal_representative: z.string().optional(),
  terms_url: z.string().url("URL inválida").optional().or(z.literal("")),
  privacy_url: z.string().url("URL inválida").optional().or(z.literal("")),
});

interface LegalFormProps {
  initialData: BrandIdentity;
  onSave: (data: BrandIdentity) => Promise<void>;
  isSaving: boolean;
}

export function LegalForm({ initialData, onSave, isSaving }: LegalFormProps) {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      legal_name: initialData.legal_name || "",
      tax_id: initialData.tax_id || "",
      fiscal_address: initialData.fiscal_address || "",
      legal_representative: initialData.legal_representative || "",
      terms_url: initialData.terms_url || "",
      privacy_url: initialData.privacy_url || "",
    },
  });

  useEffect(() => {
    form.reset({
      legal_name: initialData.legal_name || "",
      tax_id: initialData.tax_id || "",
      fiscal_address: initialData.fiscal_address || "",
      legal_representative: initialData.legal_representative || "",
      terms_url: initialData.terms_url || "",
      privacy_url: initialData.privacy_url || "",
    });
  }, [initialData, form]);

  function onSubmit(values: z.infer<typeof formSchema>) {
    // Merge with existing identity data to avoid data loss on other fields
    const finalData = {
      ...initialData,
      ...values,
    };
    void onSave(finalData);
  }

  return (
    <Card className="border-none shadow-none">
      <CardHeader className="px-0 pt-0">
        <CardTitle>Datos Legales</CardTitle>
        <CardDescription>
          Información para facturación, contratos y cumplimiento normativo.
        </CardDescription>
      </CardHeader>
      <CardContent className="px-0">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="legal_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Razón Social</FormLabel>
                    <FormControl>
                      <Input placeholder="Ej: Visionarias LLC" {...field} />
                    </FormControl>
                    <FormDescription>Nombre legal de la empresa.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="tax_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Identificación Fiscal (RUC/NIT)</FormLabel>
                    <FormControl>
                      <Input placeholder="Ej: 20601234567" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="fiscal_address"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Dirección Fiscal</FormLabel>
                  <FormControl>
                    <Input placeholder="Dirección registrada en sunat/hacienda" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="legal_representative"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Representante Legal</FormLabel>
                  <FormControl>
                    <Input placeholder="Nombre Completo" {...field} />
                  </FormControl>
                  <FormDescription>Persona con poderes de firma.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="terms_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Link Términos y Condiciones</FormLabel>
                    <FormControl>
                      <Input placeholder="https://.../terminos" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="privacy_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Link Política de Privacidad</FormLabel>
                    <FormControl>
                      <Input placeholder="https://.../privacidad" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Button type="submit" disabled={isSaving} className="w-full">
              {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Guardar Datos Legales
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
