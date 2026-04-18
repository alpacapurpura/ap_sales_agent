"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useCallback, useEffect } from "react";
import { useForm } from "react-hook-form";
import * as z from "zod";

import { useFormRuntime } from "@/components/form-runtime";
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

import type { BrandIdentity } from "@/features/brand-studio/types";
import type { ActionComponentProps } from "@/lib/form-runtime/actions";

const legalFormSchema = z.object({
  legal_name: z.string().optional(),
  tax_id: z.string().optional(),
  fiscal_address: z.string().optional(),
  legal_representative: z.string().optional(),
  terms_url: z.string().url("URL inválida").optional().or(z.literal("")),
  privacy_url: z.string().url("URL inválida").optional().or(z.literal("")),
});

type LegalFormValues = z.infer<typeof legalFormSchema>;

const LEGAL_FIELD_KEYS = [
  "legal_name",
  "tax_id",
  "fiscal_address",
  "legal_representative",
  "terms_url",
  "privacy_url",
] as const satisfies readonly (keyof LegalFormValues)[];

function buildDefaults(identity: BrandIdentity): LegalFormValues {
  return {
    legal_name: identity.legal_name ?? "",
    tax_id: identity.tax_id ?? "",
    fiscal_address: identity.fiscal_address ?? "",
    legal_representative: identity.legal_representative ?? "",
    terms_url: identity.terms_url ?? "",
    privacy_url: identity.privacy_url ?? "",
  };
}

/**
 * LegalAction — six legal / compliance fields nested under BrandIdentity.
 * Uses react-hook-form + zod for structured validation (URL format on
 * terms/privacy), then dispatches each legal field via
 * `useFormRuntime().setFieldValue` so the runtime's autosave picks it up
 * as a single composed patch (debounce absorbs the 6 rapid writes).
 *
 * Schema links this action via `path: "legal_name"` on the identity section;
 * the `value` prop is legal_name's current string but the action reads the
 * full identity slice from context so it can edit all six fields in one shot.
 */
export function LegalAction(_props: ActionComponentProps<string>) {
  const { values, setFieldValue } = useFormRuntime();
  const identity = values as unknown as BrandIdentity;

  const form = useForm<LegalFormValues>({
    resolver: zodResolver(legalFormSchema),
    defaultValues: buildDefaults(identity),
  });
  const { formState, reset, handleSubmit, control } = form;

  useEffect(() => {
    reset(buildDefaults(identity));
  }, [identity, reset]);

  const onSubmit = useCallback(
    (next: LegalFormValues) => {
      for (const key of LEGAL_FIELD_KEYS) {
        setFieldValue(key, next[key] ?? "");
      }
    },
    [setFieldValue],
  );

  return (
    <Card className="border-none shadow-none">
      <CardHeader className="px-0 pt-0">
        <CardTitle>Datos legales</CardTitle>
        <CardDescription>
          Información para facturación, contratos y cumplimiento normativo.
        </CardDescription>
      </CardHeader>
      <CardContent className="px-0">
        <Form {...form}>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FormField
                control={control}
                name="legal_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Razón social</FormLabel>
                    <FormControl>
                      <Input placeholder="Ej: Visionarias LLC" {...field} />
                    </FormControl>
                    <FormDescription>Nombre legal de la empresa.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={control}
                name="tax_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Identificación fiscal (RUC/NIT)</FormLabel>
                    <FormControl>
                      <Input placeholder="Ej: 20601234567" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={control}
              name="fiscal_address"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Dirección fiscal</FormLabel>
                  <FormControl>
                    <Input placeholder="Dirección registrada ante sunat/hacienda" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={control}
              name="legal_representative"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Representante legal</FormLabel>
                  <FormControl>
                    <Input placeholder="Nombre completo" {...field} />
                  </FormControl>
                  <FormDescription>Persona con poderes de firma.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FormField
                control={control}
                name="terms_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Términos y condiciones</FormLabel>
                    <FormControl>
                      <Input placeholder="https://.../terminos" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={control}
                name="privacy_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Política de privacidad</FormLabel>
                    <FormControl>
                      <Input placeholder="https://.../privacidad" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Button type="submit" disabled={formState.isSubmitting} className="w-full">
              {formState.isSubmitting && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />
              )}
              Guardar datos legales
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
