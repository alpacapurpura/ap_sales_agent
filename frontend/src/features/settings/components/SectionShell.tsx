"use client";

import { PageContainer } from "@/components/shared/layout/PageContainer";

import type { ReactNode } from "react";

interface SectionShellProps {
  title: string;
  description?: string;
  children: ReactNode;
}

/**
 * Content shell for each settings section. Delegates page padding to
 * `<PageContainer>` (canonical primitive) and provides title +
 * optional description above the section body. Max-width aligns with
 * the brand-studio pattern (max-w-3xl).
 */
export function SectionShell({ title, description, children }: SectionShellProps) {
  return (
    <PageContainer className="flex flex-col gap-6">
      <div className="space-y-1 max-w-3xl">
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
      </div>
      <div className="space-y-6 max-w-3xl">{children}</div>
    </PageContainer>
  );
}
