"use client";

import { Loader2 } from "lucide-react";

import { useBrandSettings } from "@/features/brand/hooks/use-brand-settings";

import { ContactForm } from "./contact-form";

export function ContactManager() {
  const { settings, updateContact, loading, saving } = useBrandSettings();

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!settings) return null;

  return (
    <ContactForm initialData={settings.contact ?? {}} onSave={updateContact} isSaving={saving} />
  );
}
