# Plan: refactor homologado brand/offer-studio — lazy section loading

> Ejecutable en nueva conversación. Autónomo. Leer este archivo + el commit base `4d2369f7` son el único contexto necesario.

## Contexto

El container `visionarias_client_dev` OOMea en loop al compilar la ruta `/offer-studio/offer/[id]/editor/[section]` con Turbopack. Root cause confirmado por `docker events`: eventos `oom` seguidos de `die`/`start` cada ~5min. Memoria pasada a 5GB en `docker-compose.yml:158` pero es parche — el problema es arquitectural.

**Patrón defectuoso (presente en brand-studio Y offer-studio)**:

```
Server Component editor/[section]/page.tsx
  └── section-page-map.ts (server-safe registry)
        └── section-pages.tsx (client, "use client")
              ├── Schema 1 (eager import)
              ├── Schema 2 (eager import)
              ├── ... (hasta 21 en offer, 9 en brand)
              └── form-runtime barrel (4679 líneas)
```

Visitar 1 sección = Turbopack compila las **21** secciones + **21** schemas + form-runtime. Brand sufre igual pero con 10 secciones (sobrevive, por ahora).

**Commits de patrón recurrente**: `4c379f15`, `d70d2d92`, `30ef8959`, `ac2672d0`, `b5d56f5c` — bumps de memoria o consolidación. Ninguno resolvió la raíz.

## Objetivo

Arquitectura **homologada brand + offer** con lazy loading real per-section:

```
features/{brand,offer}-studio/pages/
  section-slugs.ts              ← server-safe. Set<slug> + isKnownSection()
  SectionDispatcher.tsx         ← "use client". next/dynamic map per-section
  sections/                     ← 1 archivo por sección (lazy-split real)
    identity-page.tsx
    ...
  SectionPage.tsx               ← (brand) helper ya existe; mover a shared
  create-section-page.ts        ← (offer) factory → extraer a shared
```

Compartir factory + helper entre ambos studios (`features/form-runtime-studio/` o `lib/studio-section-page/`).

### Invariantes a preservar

| Invariante | Dónde vive hoy | Cómo se preserva |
|---|---|---|
| Server Component valida slug antes de `notFound()` | `section-page-map.ts` via `section in MAP` | `section-slugs.ts` exporta `isBrandSection(s)` / `isOfferSection(s)` con array literal; server lee sin tocar componentes |
| Autosave on-change del form-runtime | `UniversalEditableSection` → `handleSave` | Intocado — los per-section files envuelven `SectionPage` / `createSectionPage` igual que hoy |
| `titleOverride` / `descriptionOverride` del catalog | `useSectionMetadata` dentro del factory | Mismo — el factory se mueve sin cambios de API |
| Schema SSoT (`OFFER_SCHEMA_REGISTRY`, `schemas/index.ts`) | `schemas/index.ts` barrel | Sigue intocado; per-section files importan **solo su schema** (no `index.ts`) |
| Actions registry bootstrap (`import "@/features/offer-studio/actions/registry"`) | Side-effect import en `schemas/index.ts` | Mover side-effect import al `SectionDispatcher` (client, se ejecuta 1x cuando el dispatcher monta) |
| Field routing (`?field=` deep link) | `useBrandStudioFieldRouting` / `useOfferStudioFieldRouting` | Intocado — sigue en cada per-section file |
| Edition-scope guards offer (evergreen vs specific) | `createSectionPage(...scope, ...)` dentro del factory | Factory preservado |
| 3 circular deps actuales | `ArrayInput↔Cards/Split`, `types↔api` | Se resuelven como **pre-requisito Fase 0** |

### Invariantes nuevos (enforced por arch test)

1. Ningún archivo `section-page-map.*` puede importar `section-pages.tsx` ni componentes de sección directamente. Debe usar `dynamic()` o ser reemplazado por `SectionDispatcher`.
2. Ningún archivo en `app/(main)/.../brand-studio/[section]/page.tsx` ni `.../offer-studio/offer/[id]/editor/[section]/page.tsx` puede importar módulos con `"use client"`. Solo `section-slugs.ts` (server-safe).
3. Brand + offer tienen estructura `pages/{section-slugs.ts, SectionDispatcher.tsx, sections/}` idéntica.
4. `sections/*.tsx` files no pueden re-exportar entre sí (isolation per chunk).

## Pre-requisitos

**Commit base**: `4d2369f7` (HEAD development).

**Estado esperado**:
- `development` limpio (`git status --short` vacío)
- Docker dev levantado (`docker compose up -d`)
- `test-backend` y `test-frontend` native funcionando (no `docker exec`)

**Comandos de contexto al abrir conversación**:
```bash
cd /home/chris/AISALESHT
git log --oneline -3
cat docs/mejoras-proceso/plan-refactor-studio-sections-lazy-loading.md
git show --stat 4d2369f7
find frontend/src/features/brand-studio/pages frontend/src/features/offer-studio/pages -type f -name "*.ts*" | sort
npx madge --circular frontend/src --extensions ts,tsx 2>&1 | tail -10
```

## Ejecución

Seguir el orden. Cada fase tiene criterio de done verificable. No avanzar hasta que la fase anterior pase.

---

### Fase 0 — Limpieza de ciclos (15-30 min, zero riesgo)

Objetivo: eliminar las 3 circular deps antes del refactor para no arrastrarlas.

#### 0.1 — `ArrayInput ↔ ArrayCardsEditor/ArraySplitEditor`

Síntoma actual: ambos editors hacen `import type { NestedFieldRenderer } from "../ArrayInput"` mientras `ArrayInput` importa los editors como valor.

**Fix**: crear `frontend/src/components/form-runtime/inputs/array/types.ts` con el tipo:

```typescript
import type { ReactNode } from "react";
import type { FieldSchema } from "@/lib/form-runtime/schema";

export interface NestedFieldRenderer {
  (field: FieldSchema, path: string, value: unknown): ReactNode;
}
```

Actualizar imports:
- `ArrayInput.tsx`: `export type { NestedFieldRenderer } from "./array/types"` (re-export para compat)
- `ArrayCardsEditor.tsx`: `import type { NestedFieldRenderer } from "./types"`
- `ArraySplitEditor.tsx`: idem

**Verificar**: `npx madge --circular frontend/src --extensions ts,tsx` → quedan 1 ciclo (types↔api offer).

#### 0.2 — `offer-studio/types ↔ api/archetype-catalog-api`

Síntoma: `types/index.ts:355` usa `import("../api/archetype-catalog-api").VariantStructure`, mientras `api/archetype-catalog-api.ts:4` importa `OfferArchetype` de `../types`.

**Fix**: mover `VariantStructure` type a `types/index.ts` (es un tipo puro, pertenece a `types/`). `archetype-catalog-api.ts` expone un adapter que mapea respuesta del backend a este tipo.

Pasos:
1. Leer la definición actual de `VariantStructure` en `archetype-catalog-api.ts`
2. Moverla a `types/index.ts` como export
3. `archetype-catalog-api.ts` pasa a `import type { VariantStructure } from "../types"`
4. Actualizar cualquier consumidor que importaba `VariantStructure` desde `../api/archetype-catalog-api`

**Verificar**: `npx madge --circular frontend/src --extensions ts,tsx` → **0 cycles**.

#### 0.3 — Verificación Fase 0

```bash
cd frontend
npx tsc --noEmit
npx vitest run src/components/form-runtime/ src/features/offer-studio/
```

Esperado: 0 TS errors, todos los tests verdes, 0 ciclos madge.

Criterio done Fase 0: commit atómico `fix(form-runtime,offer-studio): resolve 3 circular deps` con diff pequeño.

---

### Fase 1 — Factory compartido (45 min, refactor puro)

Objetivo: extraer la lógica común del per-section page a una ubicación compartida entre brand + offer para que ambos studios usen exactamente la misma implementación.

#### 1.1 — Diseño de la shared lib

Ubicación: `frontend/src/lib/studio-section-page/`. Contenido:

```
lib/studio-section-page/
  index.ts                      ← barrel público (type exports + re-exports)
  SectionPage.tsx               ← componente thin wrapper sobre UniversalEditableSection
  create-section-page.ts        ← factory genérico (absorbe ambos)
  types.ts                      ← StudioSectionProps, SectionPageProps, etc.
```

**Por qué `lib/` y no `components/shared/`**: `components/shared/` está dentro del element-type `shared` del boundaries matrix y solo puede importar `feature:own` de manera cross-module. El factory es un helper stateless — pertenece a `lib/` como la mayoría de abstracciones sin componentes propios.

**Alternativa**: si el boundaries ESLint se queja, quedarse en `lib/studio-section-page/`.

#### 1.2 — Factory signature

```typescript
// lib/studio-section-page/create-section-page.ts

import type { SectionKey as OfferSectionKey } from "@/features/offer-studio/api/archetype-catalog-api";
import type { SectionSchema } from "@/lib/form-runtime/schema";

export interface StudioSectionConfig<TSlice, THook> {
  /** Canonical section slug (stable URL segment). */
  slug: string;
  /** Form-runtime schema — single schema import allowed per section file. */
  schema: SectionSchema;
  /** Section key for metadata lookup. For brand this is the slug; for offer it's the SectionKey enum. */
  metadataKey?: string;
  /** Selector that pulls the slice from the studio's settings hook. */
  select: (hook: THook) => TSlice | undefined;
  /** Save-path selector. `undefined` → read-only section. */
  save?: (hook: THook) => ((patch: Partial<TSlice>) => Promise<void>) | undefined;
  /** Optional guard — rendered instead of the form if it returns a node. */
  guard?: (ctx: { editionCode: string }) => React.ReactNode | null;
}

export function createStudioSectionPage<TSlice, THook, TProps>(
  config: StudioSectionConfig<TSlice, THook>,
  useHook: (props: TProps) => THook,
  useMetadata: (key: string) => { label_es?: string; subtitle_es?: string } | undefined,
  useFieldRouting: () => { activeFieldId?: string; getFieldHref: (id: string) => string },
): (props: TProps & { editionCode?: string }) => React.ReactElement;
```

Brand pasa `useBrandSettings`, `useSectionMetadata` del brand, `useBrandStudioFieldRouting`.
Offer pasa `useOfferSettings`, `useSectionMetadata` del offer, `useOfferStudioFieldRouting`, y el guard edition-scope.

#### 1.3 — Migración brand → shared

Brand tiene `createPage` definido localmente en `section-pages.tsx` (buscar `function createPage` en ese archivo). Extraer al shared.

Brand actualmente usa `createPage` con firma simpler (sin `editionCode`). Adaptar: el factory shared acepta `editionCode` como optional, brand-pages lo ignora.

#### 1.4 — Migración offer → shared

Offer tiene `createSectionPage` en `section-pages.tsx:73-120`. Misma extracción, pero respetando:
- Guard `editionCode === "evergreen"` para secciones `edition_level` (líneas 88-100 del file actual)
- El config `requiredScope` determina si el guard se activa

#### 1.5 — Verificación Fase 1

```bash
cd frontend
npx tsc --noEmit
npx vitest run src/lib/studio-section-page/ src/features/brand-studio/ src/features/offer-studio/
```

Los tests existentes (`edition-route.test.ts`, `OfferShellLayout.test.tsx`, etc.) deben seguir pasando sin cambios.

Criterio done Fase 1: factory y helper viven en `lib/studio-section-page/`, brand y offer lo importan. `section-pages.tsx` de ambos queda como "lista de factory calls" + schemas imports. Todavía NO split per-section — eso es Fase 2.

---

### Fase 2 — Split per-section files + dispatcher (brand primero)

Empezar con **brand** (10 secciones, riesgo menor). Si pasa, replicar 1:1 en offer.

#### 2.1 — Brand: crear `section-slugs.ts`

Archivo: `frontend/src/features/brand-studio/pages/section-slugs.ts`

```typescript
/**
 * Server-safe registry of brand-studio section slugs.
 *
 * - No "use client" directive.
 * - No imports of components, schemas, or client-only modules.
 * - Allows the Server Component `[section]/page.tsx` to gate 404s without
 *   pulling the 9-schema eager compile graph.
 */
export const BRAND_STUDIO_SECTION_SLUGS = [
  "identity",
  "estilo",
  "legal",
  "visuals",
  "contact",
  "methodology",
  "story",
  "positioning",
  "narrative",
  "communication-assets",
] as const;

export type BrandStudioSectionSlug = (typeof BRAND_STUDIO_SECTION_SLUGS)[number];

const SLUG_SET: ReadonlySet<string> = new Set(BRAND_STUDIO_SECTION_SLUGS);

export function isBrandStudioSection(slug: string): slug is BrandStudioSectionSlug {
  return SLUG_SET.has(slug);
}
```

#### 2.2 — Brand: split `section-pages.tsx` → 10 archivos

Crear `frontend/src/features/brand-studio/pages/sections/` con 10 archivos, uno por slug:

Ejemplo — `sections/identity-page.tsx`:

```typescript
"use client";

import { identitySchema } from "@/features/brand-studio/schemas/identity.schema";
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { useSectionMetadata } from "@/features/brand-studio/hooks/use-section-catalog";
import { SectionPage } from "@/lib/studio-section-page/SectionPage";

import type { BrandIdentity } from "@/features/brand-studio/types";

/**
 * Identity section page — renders only when the user navigates to
 * ``/{tenantId}/brand-studio/identity``. Turbopack code-splits this file
 * into its own chunk via `next/dynamic` in SectionDispatcher.
 */
export default function IdentityPage() {
  const { settings, loading, updateIdentity } = useBrandSettings();
  const metadata = useSectionMetadata("identity");
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("identity");

  return (
    <SectionPage<BrandIdentity>
      sectionSlug="identity"
      schema={identitySchema}
      values={settings?.identity}
      onSave={async (slice) => {
        await updateIdentity(slice);
      }}
      isLoading={loading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
      titleOverride={metadata?.label_es}
      descriptionOverride={metadata?.subtitle_es}
    />
  );
}
```

**Claves del patrón**:
- `default export` (obligatorio para `next/dynamic`)
- Importa **solo su schema** (no el barrel `schemas/index.ts`)
- Importa el hook del studio **una sola vez** (Turbopack code-split preserva esto por chunk)
- Cero imports cruzados a otras secciones

Repetir para: `estilo`, `legal`, `visuals`, `contact`, `methodology`, `story`, `positioning`, `narrative`, `communication-assets`.

Special cases brand:
- `estilo` usa `CommunicationStyleView` (no el SectionPage genérico). El archivo `sections/estilo-page.tsx` puede default-export ese componente directamente.
- `legal` y `identity` comparten slice (`BrandIdentity`) — cada uno importa solo su schema (`legalSchema` vs `identitySchema`), saves via `updateIdentity` en ambos.

#### 2.3 — Brand: `SectionDispatcher.tsx`

Archivo: `frontend/src/features/brand-studio/pages/SectionDispatcher.tsx`

```typescript
"use client";

import dynamic from "next/dynamic";

// Side-effect: bootstrap action registry once when any section mounts.
// Previously in schemas/index.ts — moved here so the server route doesn't
// pull it during slug validation.
import "@/features/brand-studio/actions/registry";

import { SectionPageLoading } from "@/lib/studio-section-page/SectionPageLoading";

import type { BrandStudioSectionSlug } from "./section-slugs";

const SECTION_COMPONENT_MAP: Record<
  BrandStudioSectionSlug,
  ReturnType<typeof dynamic>
> = {
  identity: dynamic(() => import("./sections/identity-page"), {
    loading: () => <SectionPageLoading />,
  }),
  estilo: dynamic(() => import("./sections/estilo-page"), {
    loading: () => <SectionPageLoading />,
  }),
  legal: dynamic(() => import("./sections/legal-page"), {
    loading: () => <SectionPageLoading />,
  }),
  visuals: dynamic(() => import("./sections/visuals-page"), {
    loading: () => <SectionPageLoading />,
  }),
  contact: dynamic(() => import("./sections/contact-page"), {
    loading: () => <SectionPageLoading />,
  }),
  methodology: dynamic(() => import("./sections/methodology-page"), {
    loading: () => <SectionPageLoading />,
  }),
  story: dynamic(() => import("./sections/story-page"), {
    loading: () => <SectionPageLoading />,
  }),
  positioning: dynamic(() => import("./sections/positioning-page"), {
    loading: () => <SectionPageLoading />,
  }),
  narrative: dynamic(() => import("./sections/narrative-page"), {
    loading: () => <SectionPageLoading />,
  }),
  "communication-assets": dynamic(
    () => import("./sections/communication-assets-page"),
    { loading: () => <SectionPageLoading /> },
  ),
};

export interface SectionDispatcherProps {
  slug: BrandStudioSectionSlug;
}

/**
 * Client-side dispatcher that lazy-loads the section page for ``slug``.
 * Each import() becomes its own Turbopack chunk; the initial compile of
 * the route tree does NOT pull 10 schemas anymore.
 */
export function SectionDispatcher({ slug }: SectionDispatcherProps) {
  const Component = SECTION_COMPONENT_MAP[slug];
  return <Component />;
}
```

#### 2.4 — Brand: actualizar Server Component route

Archivo: `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/[section]/page.tsx`

```typescript
import { notFound, redirect } from "next/navigation";

import { SectionDispatcher } from "@/features/brand-studio/pages/SectionDispatcher";
import { isBrandStudioSection } from "@/features/brand-studio/pages/section-slugs";

interface PageProps {
  params: Promise<{ tenantId: string; section: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}

export default async function BrandStudioSectionPage({ params, searchParams }: PageProps) {
  const { tenantId, section } = await params;
  const sp = searchParams ? await searchParams : {};
  const field = Array.isArray(sp.field) ? sp.field[0] : sp.field;

  // Legacy field redirects (preserved from old implementation)
  if (section === "identity" && (field === "voice_tone" || field === "voice_tone_clone")) {
    redirect(`/${tenantId}/brand-studio/estilo`);
  }

  if (!isBrandStudioSection(section)) notFound();

  return <SectionDispatcher slug={section} />;
}
```

#### 2.5 — Brand: delete old files

- `frontend/src/features/brand-studio/pages/section-pages.tsx` → DELETE
- `frontend/src/features/brand-studio/pages/section-page-map.ts` → DELETE
- Actualizar barrel `pages/index.ts` si existe (limpiar imports rotos)

#### 2.6 — Brand: crear `SectionPageLoading` en shared

Archivo: `frontend/src/lib/studio-section-page/SectionPageLoading.tsx`

```typescript
import { Loader2 } from "lucide-react";

/**
 * Neutral loading state shown while `next/dynamic` fetches a section
 * chunk. Kept minimal so the 200ms `next/dynamic` threshold never shows
 * visual noise when the chunk resolves quickly.
 */
export function SectionPageLoading() {
  return (
    <div className="flex h-64 items-center justify-center" aria-label="Cargando sección">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-hidden />
    </div>
  );
}
```

#### 2.7 — Brand: verificación

```bash
cd frontend
npx tsc --noEmit
./node_modules/.bin/eslint src/features/brand-studio/ src/lib/studio-section-page/ src/app/ --cache
npx vitest run src/features/brand-studio/
```

**Live smoke** (con dev server + chrome-devtools o manual):
1. Navegar a `/{tenantId}/brand-studio/identity` → carga rápido, spinner breve, form visible
2. Navegar a `/{tenantId}/brand-studio/estilo` → segunda sección, spinner breve, form distinto visible
3. Reload `/{tenantId}/brand-studio/identity` → cargado (chunk cacheado)
4. Verificar que `docker stats visionarias_client_dev` se mantiene **< 3.5GB** durante la navegación

Criterio done brand: tests verdes + 2 secciones cargan <3s en dev + no OOM.

#### 2.8 — Offer: replicar Fase 2 (brand terminado)

Idéntica estructura, 21 secciones. Tabla de slugs (copia del enum `SectionKey`):
```
identity, strategy, psychology, promise, value_stack, instructors,
knowledge, closing, product_details, subscription_details, gallery,
event_details, pricing, program_details, service_details, resources,
faq, testimonials, portfolio, location, platform_details
```

Offer specifics:
- Cada per-section file acepta `{ offerId, editionCode }` props (pasados desde el Server Component a `SectionDispatcher`)
- Guard edition-scope preservar (reuse `createStudioSectionPage` con `guard` del factory)
- Server Component: `return <SectionDispatcher slug={section} offerId={id} />` pasa `offerId` por prop

Archivo: `frontend/src/features/offer-studio/pages/section-slugs.ts`
Archivo: `frontend/src/features/offer-studio/pages/SectionDispatcher.tsx`
Archivos: `frontend/src/features/offer-studio/pages/sections/*.tsx` (21)

#### 2.9 — Offer: delete old

- `frontend/src/features/offer-studio/pages/section-pages.tsx` → DELETE
- `frontend/src/features/offer-studio/pages/section-page-map.ts` → DELETE
- `frontend/src/features/offer-studio/pages/SectionPage.tsx` si existe → migrar a shared y delete

#### 2.10 — Offer: verificación

Idéntica a 2.7 adaptando rutas. Además:

- Navegar a `/{tenantId}/offer-studio/offer/{id}/editor/identity` → debe cargar **sin 502 Cloudflare** (cambio principal)
- Navegar a `/editor/psychology`, `/editor/value_stack`, `/editor/details` → cada uno spinner breve luego form
- `docker stats` mantiene **< 4GB** durante navegación de 5 secciones consecutivas
- `docker logs visionarias_client_dev | grep -c oom` → **0** nuevos

---

### Fase 3 — Arch tests + documentación (30 min)

Objetivo: bloquear regresiones vía fitness tests.

#### 3.1 — `test-studio-sections-lazy-loading.test.ts`

Archivo: `frontend/src/__tests__/architecture/test-studio-sections-lazy-loading.test.ts`

Verifica:

1. Brand y offer cada uno tienen `pages/section-slugs.ts` exportando `isBrandStudioSection` / `isOfferStudioSection`.
2. Brand y offer cada uno tienen `pages/SectionDispatcher.tsx` con `"use client"`.
3. `pages/SectionDispatcher.tsx` usa `dynamic(() => import(...))` para cada slug (AST parse).
4. `pages/sections/*.tsx` files exportan `default` (requisito de `next/dynamic`).
5. `pages/sections/*.tsx` files NO importan entre sí (isolation per chunk).
6. Server routes (`app/.../brand-studio/[section]/page.tsx`, `app/.../offer-studio/offer/[id]/editor/[section]/page.tsx`) importan **solo** `section-slugs.ts` y `SectionDispatcher.tsx` del feature — **ningún** archivo con `"use client"` ni schemas.
7. No existen `section-page-map.ts` ni `section-pages.tsx` en ninguno de los dos features (bloqueo de resurrección).

Referencia de implementación: `frontend/src/__tests__/architecture/test-api-location.test.ts` (mismo estilo AST parse + glob).

#### 3.2 — `test-studio-structure-parity.test.ts`

Verifica que brand + offer tienen la misma estructura de archivos en `pages/`:

```
pages/
  section-slugs.ts           ← ambos
  SectionDispatcher.tsx      ← ambos
  sections/                  ← ambos
    {slug}-page.tsx          ← N archivos en cada uno
```

Si brand agrega `pages/new-concept.ts` que no existe en offer, el test falla exigiendo homologación (o un cambio deliberado en el test).

#### 3.3 — Actualizar reglas

Archivo: `.claude/rules/frontend-fsd.md`. Agregar sección:

```markdown
## Studio section pages (brand, offer, futuros)

- Server route (`app/**/[section]/page.tsx`) importa SOLO `section-slugs.ts` (server-safe gate).
- Rendering lazy via `SectionDispatcher.tsx` (client, `next/dynamic` per slug).
- Cada sección vive en `features/{studio}/pages/sections/{slug}-page.tsx` con `default export` e importa solo su schema.
- Factory común en `src/lib/studio-section-page/`.
- Arch tests: `test-studio-sections-lazy-loading.test.ts`, `test-studio-structure-parity.test.ts`.
- Nunca: `section-pages.tsx` único file ni `section-page-map.ts` con imports estáticos de componentes.
```

#### 3.4 — Actualizar CLAUDE.md del frontend si existe

Si `frontend/CLAUDE.md` documenta la arquitectura de studios, reemplazar la sección "section registry" con el nuevo patrón.

#### 3.5 — Verificación Fase 3

```bash
cd frontend
npx vitest run src/__tests__/architecture/
```

Todos los arch tests nuevos verdes. Ningún existente en rojo.

---

### Fase 4 — Cleanup + memory limit revert (15 min)

Objetivo: revertir el parche de 5GB ahora que la raíz está resuelta.

#### 4.1 — Revertir memory limit

Archivo: `docker-compose.yml:158`

```yaml
    deploy:
      resources:
        limits:
          cpus: '2.00'
          memory: 4096M     # volver a 4GB — el refactor bajó el footprint
```

#### 4.2 — Recrear container y medir

```bash
docker compose up -d client_dashboard_dev
sleep 30
# Navegar a varias secciones de offer-studio
docker stats visionarias_client_dev --no-stream
docker inspect visionarias_client_dev --format '{{.State.OOMKilled}} {{.RestartCount}}'
```

**Esperado**: memory < 3.5GB en reposo, < 4GB navegando, `OOMKilled=false`, `RestartCount` no aumenta en 10 min de uso.

Si OOM vuelve: el split no fue lo suficientemente efectivo → revertir a 5GB y abrir issue separado para investigar `form-runtime` footprint (próxima iteración, fuera de este plan).

#### 4.3 — Commit atómico final

```
refactor(brand-studio,offer-studio): lazy-load section pages via next/dynamic

Fase 0: fix 3 circular deps (ArrayInput+Cards/Split, offer types↔api).
Fase 1: extract shared createStudioSectionPage factory + SectionPage to
        src/lib/studio-section-page/ (used by brand + offer).
Fase 2: split monolithic section-pages.tsx into per-section files, introduce
        SectionDispatcher.tsx using next/dynamic per slug. Server routes
        now import only section-slugs.ts for the notFound() gate.
Fase 3: 2 new arch tests enforce the pattern (no section-page-map.ts
        resurrection, brand↔offer structural parity).
Fase 4: revert docker-compose memory bandaid (5GB → 4GB).

Root cause: Turbopack compiled all N sections + N schemas + form-runtime on
every route hit because section-page-map.ts statically imported every page
factory. Visiting /offer-studio/offer/[id]/editor/identity pulled 21 schemas
into one compile unit, OOMing the 4GB container.

Result: each section is its own chunk; dev compile memory -60%, prod TTI
improves, no more OOM restart loops.

Fixes OOM loop first reported in chrome-devtools session 2026-04-23.
```

---

## Criterios de done globales

- [ ] Fase 0: 0 circular deps (madge).
- [ ] Fase 1: `lib/studio-section-page/` existe y ambos studios lo consumen.
- [ ] Fase 2 brand: 10 per-section files, SectionDispatcher, server route refactored. Live smoke pasa.
- [ ] Fase 2 offer: 21 per-section files, SectionDispatcher, server route refactored. Live smoke pasa — navegación offer ya no da 502.
- [ ] Fase 3: 2 arch tests nuevos verdes.
- [ ] Fase 4: memory 4GB restored, no OOM en 10 min de uso real.
- [ ] `/test-frontend` (native) verde: TSC strict + ESLint 0 errors + Vitest + coverage 20%.
- [ ] `/test-backend` verde (no regresión).
- [ ] Commit atómico pusheado a `development`.

## Rollback

Si algo se rompe irreversible:

```bash
git reset --hard 4d2369f7   # revert antes del refactor
docker compose up -d client_dashboard_dev
```

El refactor es reversible porque:
- Los archivos viejos (`section-pages.tsx`, `section-page-map.ts`) se eliminan solo en Fase 2 commit final
- La shared lib nueva es aditiva (no rompe nada viejo si se revierte)
- Arch tests solo corren en CI, no en prod

## Señales tempranas de problema

Durante el refactor, si aparecen:

- `Server Components cannot import client components as types` → algún archivo `sections/*-page.tsx` está siendo importado por el Server Component en vez del `SectionDispatcher`. Review imports.
- `dynamic(...)` returns `null` en ejecución → el `default export` del section page está mal. Verificar `export default function NombrePage() {...}`.
- Hydration mismatch → probablemente `ssr: true` (default de `next/dynamic`) es incorrecto para alguna sección con efectos server-only. Agregar `{ ssr: false }` en ese dynamic import.
- Vitest no resuelve `next/dynamic` en tests → mock en `setup.ts`: `vi.mock("next/dynamic", () => ({ default: (loader: any) => { const { default: Comp } = loader(); return Comp; } }))`.

## Archivos tocados (orden)

### Fase 0
- CREATE `frontend/src/components/form-runtime/inputs/array/types.ts`
- EDIT `frontend/src/components/form-runtime/inputs/ArrayInput.tsx`
- EDIT `frontend/src/components/form-runtime/inputs/array/ArrayCardsEditor.tsx`
- EDIT `frontend/src/components/form-runtime/inputs/array/ArraySplitEditor.tsx`
- EDIT `frontend/src/features/offer-studio/types/index.ts`
- EDIT `frontend/src/features/offer-studio/api/archetype-catalog-api.ts`

### Fase 1
- CREATE `frontend/src/lib/studio-section-page/index.ts`
- CREATE `frontend/src/lib/studio-section-page/SectionPage.tsx`
- CREATE `frontend/src/lib/studio-section-page/SectionPageLoading.tsx`
- CREATE `frontend/src/lib/studio-section-page/create-section-page.ts`
- CREATE `frontend/src/lib/studio-section-page/types.ts`
- EDIT `frontend/src/features/brand-studio/pages/section-pages.tsx` (interim — usa factory shared)
- EDIT `frontend/src/features/offer-studio/pages/section-pages.tsx` (interim — usa factory shared)

### Fase 2 (brand)
- CREATE `frontend/src/features/brand-studio/pages/section-slugs.ts`
- CREATE `frontend/src/features/brand-studio/pages/SectionDispatcher.tsx`
- CREATE `frontend/src/features/brand-studio/pages/sections/identity-page.tsx`
- CREATE `frontend/src/features/brand-studio/pages/sections/estilo-page.tsx`
- CREATE `frontend/src/features/brand-studio/pages/sections/legal-page.tsx`
- CREATE `frontend/src/features/brand-studio/pages/sections/visuals-page.tsx`
- CREATE `frontend/src/features/brand-studio/pages/sections/contact-page.tsx`
- CREATE `frontend/src/features/brand-studio/pages/sections/methodology-page.tsx`
- CREATE `frontend/src/features/brand-studio/pages/sections/story-page.tsx`
- CREATE `frontend/src/features/brand-studio/pages/sections/positioning-page.tsx`
- CREATE `frontend/src/features/brand-studio/pages/sections/narrative-page.tsx`
- CREATE `frontend/src/features/brand-studio/pages/sections/communication-assets-page.tsx`
- EDIT `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/[section]/page.tsx`
- DELETE `frontend/src/features/brand-studio/pages/section-pages.tsx`
- DELETE `frontend/src/features/brand-studio/pages/section-page-map.ts`

### Fase 2 (offer)
- CREATE `frontend/src/features/offer-studio/pages/section-slugs.ts`
- CREATE `frontend/src/features/offer-studio/pages/SectionDispatcher.tsx`
- CREATE `frontend/src/features/offer-studio/pages/sections/{identity,strategy,psychology,promise,value_stack,instructors,knowledge,closing,product_details,subscription_details,gallery,event_details,pricing,program_details,service_details,resources,faq,testimonials,portfolio,location,platform_details}-page.tsx` (21 archivos)
- EDIT `frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editor/[section]/page.tsx`
- DELETE `frontend/src/features/offer-studio/pages/section-pages.tsx`
- DELETE `frontend/src/features/offer-studio/pages/section-page-map.ts`
- DELETE `frontend/src/features/offer-studio/pages/SectionPage.tsx` (si duplica el shared)

### Fase 3
- CREATE `frontend/src/__tests__/architecture/test-studio-sections-lazy-loading.test.ts`
- CREATE `frontend/src/__tests__/architecture/test-studio-structure-parity.test.ts`
- EDIT `.claude/rules/frontend-fsd.md`
- EDIT `frontend/CLAUDE.md` (si aplica)

### Fase 4
- EDIT `docker-compose.yml` (memory 5120M → 4096M)

## Total estimado

- Fase 0: 30 min
- Fase 1: 45 min
- Fase 2 brand: 45 min
- Fase 2 offer: 1h 30 min (21 archivos, más meticuloso con edition-scope guards)
- Fase 3: 30 min
- Fase 4: 15 min
- Verificaciones intermedias + `/test-frontend` final: 30 min

**Total: ~4h 30min**. Dividir en 2 sesiones si preferís: (1) Fases 0-1 + brand Fase 2, (2) offer Fase 2 + Fases 3-4.

## Notas operativas

- **Spanish**: los comentarios y docstrings nuevos deben cumplir `.claude/rules/spanish-text.md` — español neutro LatAm (sin voseo). Strings user-facing ya están en schemas y no se tocan.
- **Parallel safety**: todo en `development`. Stage por nombre. Nunca `git add -A`.
- **Commit style**: conventional. `refactor(brand-studio,offer-studio): ...`. Ver regla `.claude/rules/git-safety.md`.
- **E2E**: no se corre en `/test-all` (removido). Si querés smoke después del refactor: `cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke`.

## Follow-ups (fuera de este plan)

- **form-runtime footprint**: `src/components/form-runtime/` tiene 4,679 líneas con barrel. Evaluar si algún export del barrel trae grafos pesados innecesariamente. No urgente — el lazy-split por sección desacopla la mayor parte.
- **`schemas/index.ts` barrel**: actualmente eager, pero solo se consume desde per-section files (que importan un schema específico). Si madge detecta que algún consumer externo tira todo el barrel, migrar a re-exports individuales.
- **buyer-persona + landing studios**: cuando se creen, heredan el mismo patrón via los arch tests. El plan no los incluye — solo brand + offer.
