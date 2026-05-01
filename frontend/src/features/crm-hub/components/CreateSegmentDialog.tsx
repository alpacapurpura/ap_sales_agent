"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

import { createSegmentFormSchema } from "../../campaigns-lite/types";
import { useCreateSegmentMutation } from "../api/use-create-segment-mutation";

import type { CreateSegmentFormValues } from "../../campaigns-lite/types";

interface CreateSegmentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedLeadIds: string[];
  /** Called with the new segmentId and the user-entered name. */
  onSuccess: (segmentId: string, segmentName: string) => void;
}

/**
 * Dialog para crear un segmento STATIC a partir de contactos seleccionados.
 * Submit → POST /api/v1/segments/ con segment_type: STATIC + lead_ids.
 * Success → toast Sonner + callback onSuccess(segmentId).
 */
export function CreateSegmentDialog({
  open,
  onOpenChange,
  selectedLeadIds,
  onSuccess,
}: CreateSegmentDialogProps) {
  const mutation = useCreateSegmentMutation();

  const form = useForm<CreateSegmentFormValues>({
    resolver: zodResolver(createSegmentFormSchema),
    defaultValues: {
      name: "",
      description: "",
    },
  });

  // Reset form when dialog closes.
  // Why: form + mutation refs change cada render — incluirlos en deps causa loop infinito
  // (form.reset triggers re-render → useEffect re-runs → infinite). Solo `open` es trigger real.
  React.useEffect(() => {
    if (!open) {
      form.reset({ name: "", description: "" });
      mutation.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- form/mutation refs unstable; only `open` is the real trigger
  }, [open]);

  async function onSubmit(values: CreateSegmentFormValues) {
    try {
      const segment = await mutation.mutateAsync({
        name: values.name,
        description: values.description || undefined,
        segment_type: "STATIC",
        lead_ids: selectedLeadIds,
      });
      toast.success(`Segmento "${values.name}" creado con ${selectedLeadIds.length} contactos.`);
      onOpenChange(false);
      onSuccess(segment.id, values.name);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error al crear el segmento.";
      form.setError("root", { message });
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>Crear segmento</DialogTitle>
          <DialogDescription>
            Se creará un segmento con {selectedLeadIds.length}{" "}
            {selectedLeadIds.length === 1 ? "contacto" : "contactos"} seleccionados.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            noValidate
            aria-label="Formulario de creación de segmento"
          >
            <div className="flex flex-col gap-4 py-2">
              {/* Error global */}
              {form.formState.errors.root && (
                <div role="alert" className="text-sm text-destructive">
                  {form.formState.errors.root.message}
                </div>
              )}

              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Nombre del segmento <span aria-hidden="true">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        placeholder="Ej: Leads de abril con Telegram"
                        aria-required="true"
                        aria-invalid={!!form.formState.errors.name}
                        disabled={mutation.isPending}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Descripción (opcional)</FormLabel>
                    <FormControl>
                      <Textarea
                        {...field}
                        placeholder="Describe el criterio de este segmento…"
                        rows={3}
                        disabled={mutation.isPending}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter className="mt-4">
              <Button
                type="button"
                variant="ghost"
                onClick={() => onOpenChange(false)}
                disabled={mutation.isPending}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={mutation.isPending} aria-busy={mutation.isPending}>
                {mutation.isPending ? "Creando…" : "Crear segmento"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
