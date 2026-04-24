"use client";

import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { contactSchema } from "@/features/brand-studio/schemas/contact.schema";
import { SectionPage } from "@/lib/studio-section-page";

import type { ContactData } from "@/features/brand-studio/types";

export function ContactPage() {
  const hook = useBrandSettings();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("contact");

  return (
    <SectionPage<ContactData>
      sectionSlug="contact"
      schema={contactSchema}
      values={hook.settings?.contact ?? undefined}
      onSave={async (next) => {
        await hook.updateContact(next);
      }}
      isLoading={hook.loading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
    />
  );
}
