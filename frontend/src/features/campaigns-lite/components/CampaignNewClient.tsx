"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

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
import { SmartDateTimePicker } from "@/components/ui/smart-datetime-picker";
import { Textarea } from "@/components/ui/textarea";

import { useAddCampaignStepMutation } from "../api/use-add-campaign-step-mutation";
import { useCreateCampaignMutation } from "../api/use-create-campaign-mutation";
import { useScheduleCampaignMutation } from "../api/use-schedule-campaign-mutation";
import { createCampaignFormSchema } from "../types";

import type { CreateCampaignFormValues } from "../types";

interface CampaignNewClientProps {
  segmentId: string | null;
}

const DEFAULT_TIMEZONE = "America/Lima";

/**
 * Formulario de creación de campaña (lite — S4 PI-1).
 * Pipeline: POST /api/v1/campaigns/ → POST /api/v1/campaigns/{id}/steps/ → (opt) POST /api/v1/campaigns/{id}/schedule
 * Tras éxito → router.push("/sales/campanas/{id}")
 */
export function CampaignNewClient({ segmentId }: CampaignNewClientProps) {
  const router = useRouter();
  const params = useParams<{ tenantId: string }>();

  const createCampaign = useCreateCampaignMutation();
  const addStep = useAddCampaignStepMutation();
  const scheduleCampaign = useScheduleCampaignMutation();

  const form = useForm<CreateCampaignFormValues>({
    resolver: zodResolver(createCampaignFormSchema),
    defaultValues: {
      name: "",
      description: "",
      scheduled_for: "",
    },
  });

  const isSubmitting = createCampaign.isPending || addStep.isPending || scheduleCampaign.isPending;

  // Guard: no segment → show warning
  if (!segmentId) {
    return (
      <div className="flex flex-col items-center gap-4 py-12 text-center">
        <p className="text-muted-foreground">
          Debes seleccionar un segmento para crear una campaña.
        </p>
        <Button type="button" variant="ghost" onClick={() => router.back()} className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Volver a contactos
        </Button>
      </div>
    );
  }

  async function onSubmit(values: CreateCampaignFormValues) {
    if (segmentId === null) return; // unreachable: guarded by null-segmentId early return above
    try {
      // Step 1: Create campaign
      const campaign = await createCampaign.mutateAsync({
        name: values.name,
        description: values.description ?? undefined,
        campaign_type: "AGENT_CONVERSATION",
        segment_id: segmentId,
        channel_priority: ["telegram"],
        created_by_source: "manual",
      });

      // Step 2: Add CALL_SUBAGENT_BRIEF step (campaignId per-call payload)
      await addStep.mutateAsync({
        campaignId: campaign.id,
        step_type: "CALL_SUBAGENT_BRIEF",
        step_index: 0,
        step_config: {},
      });

      // Step 3 (optional): Schedule
      if (values.scheduled_for) {
        await scheduleCampaign.mutateAsync({
          campaignId: campaign.id,
          scheduled_for: values.scheduled_for,
        });
      }

      toast.success(`Campaña "${values.name}" creada correctamente.`);
      router.push(`/${params.tenantId}/sales/campanas/${campaign.id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error al crear la campaña.";
      form.setError("root", { message });
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => router.back()}
            className="gap-1 px-2 -ml-2"
            aria-label="Volver"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-xl font-semibold">Nueva campaña Telegram</h1>
        </div>
        <p className="text-sm text-muted-foreground pl-8">
          Segmento seleccionado: <span className="font-mono text-xs">{segmentId}</span>
        </p>
      </div>

      {/* Form */}
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          noValidate
          aria-label="Formulario de nueva campaña"
          className="flex flex-col gap-5"
        >
          {/* Root error */}
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
                  Nombre de la campaña <span aria-hidden="true">*</span>
                </FormLabel>
                <FormControl>
                  <Input
                    {...field}
                    placeholder="Ej: Campaña Telegram — Leads abril"
                    aria-required="true"
                    aria-invalid={!!form.formState.errors.name}
                    disabled={isSubmitting}
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
                    placeholder="Describe el objetivo de esta campaña…"
                    rows={3}
                    disabled={isSubmitting}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="scheduled_for"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Programar envío (opcional)</FormLabel>
                <FormDescription>
                  Si no programas una fecha, la campaña se guardará como borrador.
                </FormDescription>
                <FormControl>
                  <SmartDateTimePicker
                    value={field.value}
                    onChange={field.onChange}
                    timezone={DEFAULT_TIMEZONE}
                    placeholder="Seleccionar fecha y hora de envío"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => router.back()}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting} aria-busy={isSubmitting}>
              {isSubmitting ? "Creando…" : "Crear campaña"}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
