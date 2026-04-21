# UI-SPEC — Settings Finder Navigation (brand-studio homologation)

**Session:** 2026-04-20
**Scope:** Refactor `/[tenantId]/settings/*` to mirror brand-studio + offer-studio Finder-style architecture. Integrate `/settings/perfil-negocio` as a section tab inside the "Principal" group. No backend changes.
**Exclusions:** `/connections` (separate module). No change to individual form components (`GeneralSettingsForm`, `ProfileView`, `TeamView`, `AIKeysForm`, `SchedulingSettingsView`, `PaymentSettingsView`, `WebhookView`, `PerfilNegocioSettingsClient`). Only the shell + routing + navigation rail + breadcrumb change.

---

## 1. Reference pattern (brand-studio)

| Layer | File |
|---|---|
| Route shell | `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/layout.tsx` |
| Root redirect | `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/page.tsx` (redirects to first section) |
| Section dispatcher | `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/[section]/[[...fieldId]]/page.tsx` |
| Section map (server-safe) | `frontend/src/features/brand-studio/pages/section-page-map.ts` |
| Section catalog (SSoT) | `frontend/src/features/brand-studio/lib/section-catalog.ts` |
| NavRail (col 1) | `frontend/src/features/brand-studio/components/BrandStudioNavRail.tsx` |
| Breadcrumb (topbar) | `frontend/src/features/brand-studio/components/BrandStudioBreadcrumb.tsx` |
| Finder primitive | `frontend/src/components/form-runtime/FinderColumn.tsx` |

Settings replicates this 1:1 — same dimensions, same CSS vars (`--brand-topbar-h: 48px`, `--brand-col-sections: 260px`), same row height, same behaviors.

---

## 2. Target route map

```
/[tenantId]/settings                        → 308 redirect → /settings/general
/[tenantId]/settings/[section]              → section page (dispatched via SETTINGS_SECTION_MAP)
/[tenantId]/settings/perfil-negocio         → perfil-negocio section (moved under shell)
/[tenantId]/settings?tab=<slug>             → 308 redirect → /settings/<slug>  (back-compat)
```

### Sections

| Slug | Group | Label | Icon | Component |
|---|---|---|---|---|
| `general` | Principal | General | `Settings` | `GeneralSettingsForm` |
| `perfil` | Principal | Perfil | `User` | `ProfileView` |
| `equipo` | Principal | Equipo | `Users` | `TeamView` |
| `perfil-negocio` | Principal | Perfil de negocio | `Building2` | `PerfilNegocioSection` (wrapper around `PerfilNegocioSettingsClient` w/o server prefetch) |
| `llm-keys` | Principal | LLM API Keys | `Key` | `AIKeysForm` |
| `agenda` | Ventas | Agenda | `CalendarClock` | `SchedulingSettingsView` |
| `pagos` | Ventas | Pagos | `CreditCard` | `PaymentSettingsView` |
| `webhooks` | Desarrolladores | Webhooks | `Webhook` | `WebhookView` |

**URL slug changes** (SEO-friendly Spanish): `profile` → `perfil`, `team` → `equipo`, `ai-keys` → `llm-keys`, `scheduling` → `agenda`, `payments` → `pagos`. Back-compat handled by redirects.

---

## 3. Layout shell

`app/(main)/[tenantId]/(dashboard)/settings/layout.tsx`:

```
┌────────────────────────────────────────────────────────┐
│ [Topbar 48px] Configuración › General                  │  ← SettingsBreadcrumb
├──────────┬─────────────────────────────────────────────┤
│ Rail     │                                             │
│ 260px    │          {children}                         │
│          │                                             │
│ [Principal]                                            │
│  • General         ›                                   │
│  • Perfil          ›                                   │
│  • Equipo          ›                                   │
│  • Perfil de …     ›                                   │
│  • LLM API Keys    ›                                   │
│ [Ventas]                                               │
│  • Agenda          ›                                   │
│  • Pagos           ›                                   │
│ [Desarrolladores]                                      │
│  • Webhooks        ›                                   │
└──────────┴─────────────────────────────────────────────┘
```

Shell matches `brand-studio/layout.tsx` exactly:

```tsx
<div className="flex h-full min-h-[calc(100vh-4rem)] flex-col">
  <header className="flex h-[var(--brand-topbar-h)] shrink-0 items-center gap-3 border-b border-border bg-background px-5" aria-label="Ruta de Configuración">
    <SettingsBreadcrumb />
  </header>
  <div className="flex min-h-0 flex-1">
    <SettingsNavRail />
    <div className="flex min-w-0 flex-1 overflow-auto">{children}</div>
  </div>
</div>
```

---

## 4. Files to add

### 4.1 Section catalog — `features/settings/lib/section-catalog.ts`

```ts
import {
  Building2, CalendarClock, CreditCard, Key,
  Settings as SettingsIcon, User, Users, Webhook,
} from "lucide-react";

export type SettingsGroup = "principal" | "ventas" | "desarrolladores";

export interface SettingsSectionMeta {
  slug: string;
  label: string;           // es-LatAm neutro — NO voseo
  group: SettingsGroup;
  icon: React.ComponentType<{ className?: string }>;
}

export const SETTINGS_GROUP_LABELS: Record<SettingsGroup, string> = {
  principal: "Principal",
  ventas: "Ventas",
  desarrolladores: "Desarrolladores",
};

export const SETTINGS_SECTIONS: readonly SettingsSectionMeta[] = [
  { slug: "general",        label: "General",           group: "principal",      icon: SettingsIcon },
  { slug: "perfil",         label: "Perfil",            group: "principal",      icon: User },
  { slug: "equipo",         label: "Equipo",            group: "principal",      icon: Users },
  { slug: "perfil-negocio", label: "Perfil de negocio", group: "principal",      icon: Building2 },
  { slug: "llm-keys",       label: "LLM API Keys",      group: "principal",      icon: Key },
  { slug: "agenda",         label: "Agenda",            group: "ventas",         icon: CalendarClock },
  { slug: "pagos",          label: "Pagos",             group: "ventas",         icon: CreditCard },
  { slug: "webhooks",       label: "Webhooks",          group: "desarrolladores", icon: Webhook },
] as const;

export const SETTINGS_DEFAULT_SECTION = "general" as const;

const BY_SLUG: Record<string, SettingsSectionMeta> = Object.fromEntries(
  SETTINGS_SECTIONS.map((s) => [s.slug, s]),
);
export function getSettingsSection(slug: string) { return BY_SLUG[slug]; }
export function getSettingsSectionLabel(slug: string): string { return BY_SLUG[slug]?.label ?? slug; }
```

### 4.2 Section page map — `features/settings/pages/section-page-map.ts` (server-safe, NO `"use client"`)

```ts
import {
  AgendaPage, EquipoPage, GeneralPage, LlmKeysPage,
  PagosPage, PerfilNegocioPage, PerfilPage, WebhooksPage,
} from "./section-pages";

export const SETTINGS_SECTION_MAP = {
  general:          GeneralPage,
  perfil:           PerfilPage,
  equipo:           EquipoPage,
  "perfil-negocio": PerfilNegocioPage,
  "llm-keys":       LlmKeysPage,
  agenda:           AgendaPage,
  pagos:            PagosPage,
  webhooks:         WebhooksPage,
} as const satisfies Readonly<Record<string, () => React.JSX.Element>>;

export type SettingsSectionSlug = keyof typeof SETTINGS_SECTION_MAP;
```

### 4.3 Section pages — `features/settings/pages/section-pages.tsx` (`"use client"`)

Thin 1-liners that wrap existing forms. Each page responsible for its own data loading (via React Query inside the form component). No server prefetch — uniform with brand-studio.

```tsx
"use client";

import { AIKeysForm } from "@/features/settings/components/AiKeysForm";
import { GeneralSettingsForm } from "@/features/settings/components/GeneralSettingsForm";
import { PaymentSettingsView } from "@/features/settings/components/PaymentSettingsView";
import { ProfileView } from "@/features/settings/components/ProfileView";
import { SchedulingSettingsView } from "@/features/settings/components/SchedulingSettingsView";
import { TeamView } from "@/features/settings/components/TeamView";
import { WebhookView } from "@/features/settings/components/WebhookView";
import { PerfilNegocioSection } from "@/features/settings/components/PerfilNegocioSection";

import { SectionShell } from "../components/SectionShell";

export const GeneralPage = () => (
  <SectionShell title="General" description="Configuración general del workspace.">
    <GeneralSettingsForm />
  </SectionShell>
);

export const PerfilPage = () => (
  <SectionShell title="Perfil" description="Tu cuenta personal dentro del workspace.">
    <ProfileView />
  </SectionShell>
);

export const EquipoPage = () => (
  <SectionShell title="Equipo" description="Miembros con acceso a este workspace.">
    <TeamView />
  </SectionShell>
);

export const PerfilNegocioPage = () => (
  <SectionShell
    title="Perfil de negocio"
    description="Define qué tipo de negocio manejas. Esto personaliza los tipos de oferta del wizard, las plantillas de landing y el contexto del agente de ventas."
  >
    <PerfilNegocioSection />
  </SectionShell>
);

// ...etc
```

> **Spanish rule (rule 11):** texto user-facing = neutro LatAm. Reemplazar "Definí qué tipo de negocio manejás" → "Define qué tipo de negocio manejas". Eliminar voseo en toda la copy movida.

### 4.4 Section shell — `features/settings/components/SectionShell.tsx`

```tsx
"use client";

import type { ReactNode } from "react";

interface SectionShellProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export function SectionShell({ title, description, children }: SectionShellProps) {
  return (
    <div className="flex flex-col gap-6 p-6 md:p-8 max-w-3xl">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
      </div>
      <div className="space-y-6">{children}</div>
    </div>
  );
}
```

### 4.5 NavRail — `features/settings/components/SettingsNavRail.tsx`

Clone `BrandStudioNavRail` with group headers. Single `FinderColumn` containing grouped `<ul>`s.

```tsx
"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useMemo } from "react";

import { FinderColumn } from "@/components/form-runtime/FinderColumn";
import { cn } from "@/lib/utils";

import {
  SETTINGS_GROUP_LABELS,
  SETTINGS_SECTIONS,
  type SettingsGroup,
  type SettingsSectionMeta,
} from "../lib/section-catalog";

export function SettingsNavRail() {
  const { tenantId = "" } = useParams<{ tenantId?: string }>() ?? {};
  const pathname = usePathname();
  const activeSlug = pathname.split("/settings/")[1]?.split("/")[0] ?? null;

  const grouped = useMemo(() => groupSections(SETTINGS_SECTIONS), []);

  return (
    <FinderColumn
      title="Configuración"
      count={SETTINGS_SECTIONS.length}
      widthClass="w-[var(--brand-col-sections)]"
      ariaLabel="Secciones de Configuración"
    >
      <div className="flex flex-col">
        {grouped.map(([group, sections]) => (
          <section key={group} className="flex flex-col">
            <header className="px-[14px] pt-3 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              {SETTINGS_GROUP_LABELS[group]}
            </header>
            <ul className="flex flex-col">
              {sections.map((s) => (
                <SectionRow key={s.slug} tenantId={tenantId} section={s} isActive={s.slug === activeSlug} />
              ))}
            </ul>
          </section>
        ))}
      </div>
    </FinderColumn>
  );
}

function groupSections(sections: readonly SettingsSectionMeta[]): Array<[SettingsGroup, SettingsSectionMeta[]]> {
  const order: SettingsGroup[] = ["principal", "ventas", "desarrolladores"];
  const byGroup = new Map<SettingsGroup, SettingsSectionMeta[]>();
  for (const s of sections) {
    if (!byGroup.has(s.group)) byGroup.set(s.group, []);
    byGroup.get(s.group)!.push(s);
  }
  return order.filter((g) => byGroup.has(g)).map((g) => [g, byGroup.get(g)!]);
}

// SectionRow: identical styling to BrandStudioNavRail.SectionRow
```

### 4.6 Breadcrumb — `features/settings/components/SettingsBreadcrumb.tsx`

Mirror `BrandStudioBreadcrumb` with path pattern `Configuración › {section}`.

### 4.7 App routes

```
app/(main)/[tenantId]/(dashboard)/settings/
├── layout.tsx                       # shell (see §3)
├── page.tsx                         # redirect(`/${tenantId}/settings/general`) with ?tab= back-compat
└── [section]/
    └── page.tsx                     # dispatcher using SETTINGS_SECTION_MAP + notFound() fallback
```

Back-compat at root `page.tsx`:

```tsx
import { redirect, permanentRedirect } from "next/navigation";

interface Props {
  params: Promise<{ tenantId: string }>;
  searchParams: Promise<{ tab?: string }>;
}

export default async function SettingsRootPage({ params, searchParams }: Props) {
  const { tenantId } = await params;
  const { tab } = await searchParams;
  const legacyMap: Record<string, string> = {
    profile: "perfil",
    team: "equipo",
    "ai-keys": "llm-keys",
    scheduling: "agenda",
    payments: "pagos",
  };
  const resolved = tab ? (legacyMap[tab] ?? tab) : "general";
  redirect(`/${tenantId}/settings/${resolved}`);
}
```

OAuth popup case (see `SettingsViewInner` L158–164) — the popup callback appears on `/settings?code=...`. Handle via `if (searchParams.code || searchParams.error) return <OAuthCallbackHandler />` BEFORE redirect.

---

## 5. Files to delete

- `frontend/src/app/(main)/[tenantId]/(dashboard)/settings/perfil-negocio/page.tsx`
- `frontend/src/app/(main)/[tenantId]/(dashboard)/settings/perfil-negocio/PerfilNegocioSettingsClient.tsx` (content moved to `features/settings/components/PerfilNegocioSection.tsx` as pure-client, no server prefetch prop; use `useTenantProfile()` directly)
- `frontend/src/features/settings/components/SettingsView.tsx` (replaced by layout + section pages)

---

## 6. Files to update

| File | Change |
|---|---|
| `frontend/src/components/shared/layout/AppSidebar.tsx:604` | `settings?tab=profile` → `settings/perfil` |
| `frontend/src/features/tenant-profile/components/BusinessTypesChipBar.tsx:40` | keep `settings/perfil-negocio` (slug unchanged) |
| `frontend/src/components/shared/app-header/TenantContextBar.tsx` | dead code — delete if knip flags; otherwise leave |
| `frontend/src/features/settings/index.ts` | re-export new catalog + section components; remove `SettingsView` |

Search & replace across codebase for any additional `settings?tab=` — should be covered by root-page redirect but clean up callers.

---

## 7. Tests

### 7.1 Unit (Vitest)

- `features/settings/lib/section-catalog.test.ts` — asserts 8 sections, 3 groups, unique slugs, all have icons.
- `features/settings/pages/section-page-map.test.ts` — every catalog slug has a page component; no orphan entries.
- `features/settings/components/SettingsNavRail.test.tsx` — groups render in order, active section has `aria-current`.
- `features/settings/components/SettingsBreadcrumb.test.ts` — `buildCrumbs` returns correct shape per path.

### 7.2 Architecture fitness (add to existing ratchet tests)

- All new `.tsx` components = PascalCase. Test file paths = kebab-case.
- `SETTINGS_SECTION_MAP` server-safe (no `"use client"` directive at top of module) — assertable via file read.
- No default exports inside `features/settings/**` (except nowhere — Next.js pages live in `app/`).

### 7.3 E2E (Playwright smoke, tag `@smoke`)

- `/[tenantId]/settings` redirects to `/[tenantId]/settings/general` (200).
- `/[tenantId]/settings?tab=profile` redirects to `/[tenantId]/settings/perfil`.
- Click NavRail row → URL updates, active state moves.
- Offer Studio dashboard no longer shows "Mostrando ofertas para:" banner.

---

## 8. Scroll + overflow

Content area (`{children}`) must scroll independently. Apply `overflow-auto` to the child container of the shell row, matching brand-studio behavior (see ref commit `3f7f2b23`). No `overflow: hidden` on `body` — rail stays sticky via flex constraints.

---

## 9. Definition of done

- [ ] All 8 sections reachable via `/[tenantId]/settings/<slug>`.
- [ ] `/settings?tab=<legacy>` redirects correctly.
- [ ] OAuth popup callback still works on `/settings?code=...`.
- [ ] OfferStudioView no longer renders `BusinessTypesChipBar`. (done in Phase 1.)
- [ ] 0 TSC errors, 0 ESLint errors (warnings baseline).
- [ ] 8 arch fitness tests green, allowlists unchanged or shrunk.
- [ ] Smoke E2E green.
- [ ] Spanish rule 11 respected: no voseo in touched copy.
- [ ] No new cross-feature imports. `features/settings/*` imports only from `settings/*`, `components/*`, `lib/*`, `hooks/*`, `form-runtime/*`, and `tenant-profile/*` (for `PerfilNegocioSection`).

---

## 10. Open questions (resolved)

1. **Q:** Preserve server prefetch for perfil-negocio?
   **A:** No. Uniform with brand-studio (all sections = client + React Query). `useTenantProfile()` handles loading state. Minor FCP cost is acceptable; simplifies arch.

2. **Q:** Move `features/settings/` to `features/settings-studio/` to mirror `brand-studio` / `offer-studio` naming?
   **A:** Not now. Out of scope; we're homologating the shell, not the feature slice naming. Future concern.

3. **Q:** Connections?
   **A:** Out of scope. Lives at `/connections/*`, untouched.
