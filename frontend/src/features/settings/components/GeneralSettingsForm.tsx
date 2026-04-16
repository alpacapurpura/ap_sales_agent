"use client";

import { useAuth } from "@clerk/nextjs";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Settings as SettingsIcon } from "lucide-react";
import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import * as z from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CurrencySelector } from "@/components/ui/currency-selector";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { settingsApi } from "@/lib/api/settings";
import { DEFAULT_CURRENCY } from "@/lib/constants/currencies";

const formSchema = z.object({
  default_currency: z.string().min(3, "Select a currency"),
});

export function GeneralSettingsForm() {
  const { getToken } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      default_currency: DEFAULT_CURRENCY.code,
    },
  });

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const data = await settingsApi.getGeneralSettings(token);
        // Ensure values are not null/undefined to prevent controlled/uncontrolled warning or errors
        form.reset({
          default_currency: data?.default_currency || DEFAULT_CURRENCY.code,
        });
      } catch (error) {
        console.error(error);
        toast.error("Error al cargar la configuración general.");
      }
    };
    void loadSettings();
  }, [getToken, form]);

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setIsLoading(true);
    try {
      const token = await getToken();
      if (!token) return;

      await settingsApi.updateGeneralSettings(values, token);
      toast.success("Configuración actualizada", {
        description: "Tus preferencias generales se han guardado.",
      });
    } catch (error) {
      console.error(error);
      toast.error("Error al guardar", {
        description: "No se pudieron guardar los cambios.",
      });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <SettingsIcon className="h-5 w-5" />
          Configuración General
        </CardTitle>
        <CardDescription>
          Personaliza las preferencias globales del sistema para tu cuenta.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="default_currency"
              render={({ field }) => (
                <FormItem className="flex flex-col">
                  <FormLabel>Moneda Predeterminada</FormLabel>
                  <FormControl>
                    <CurrencySelector value={field.value} onValueChange={field.onChange} />
                  </FormControl>
                  <FormDescription>
                    Esta moneda se utilizará por defecto al crear nuevas ofertas y visualizar
                    reportes.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" disabled={isLoading}>
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Guardar Cambios
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
