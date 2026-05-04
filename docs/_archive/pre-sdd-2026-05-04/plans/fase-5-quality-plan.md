# Fase 5 — Plan de Calidad Excepcional (Continuación)

**Fecha:** 2026-04-16
**Branch:** `development`
**Prerequisito:** fase-4 completada (`60a8ebf7`)

## Estado actual (post fase-4)

| Regla | Nivel | Violaciones PROD | Violaciones TEST | Estrategia |
|---|---|---|---|---|
| `no-non-null-assertion` | warn | 20 | 59 | Fase 5A: fix + promote |
| `sonarjs/no-dead-store` | warn | 25 | 1 | Fase 5B: fix + promote |
| `no-unsafe-return` | warn | 148 | 0 | Fase 5C: fix sistémico |
| `no-unsafe-assignment` | warn | 113 | 0 | Fase 5C: fix sistémico |
| `no-unsafe-member-access` | warn | 99 | 0 | Fase 5C: fix sistémico |
| `no-unsafe-argument` | warn | 63 | 0 | Fase 5C: fix sistémico |
| `no-unsafe-call` | warn | 10 | 0 | Fase 5C: fix sistémico |
| `jsdoc/require-jsdoc` | warn | ~843 | 0 | Fase 5D: mecánica |

---

## Fase 5A — `no-non-null-assertion` → error (20 prod)

**Dificultad:** Baja. Cada fix es un guard explícito o optional chaining.

### Archivos a tocar (agrupados por feature)

**app/ (6 violaciones, 3 archivos)**
```
app/(main)/book/[tenant_slug]/[event_slug]/page.tsx:267 (x2)
app/(main)/visit/[token]/page.tsx:150,153,154,359
```

**components/shared/ (3 violaciones, 1 archivo)**
```
components/shared/layout/AppSidebar.tsx:201,224,303
```

**features/ (11 violaciones, 7 archivos)**
```
features/brand/components/smart-fill/SmartFillDialog.tsx:312
features/growth-studio/components/campaign-panel/CampaignPanel.tsx:67
features/growth-studio/components/metrics-dashboard/offer-widgets/OfferLadder.tsx:194
features/growth-studio/components/metrics-dashboard/sidebar/ChannelDetailSidebar.tsx:251
features/growth-studio/components/strategy-canvas/utils/adapter.ts:54,55
features/offer-studio/components/editions/EditionFormDialog.tsx:88
features/offer-studio/components/landing/components/editor/AiRemixButton.tsx:66
features/sales/components/EventTypeForm.tsx:152,159,167
```

### Patrón de fix

```ts
// Antes
const value = obj!.prop;

// Después (opción A: guard)
if (!obj) throw new Error("Expected obj");
const value = obj.prop;

// Después (opción B: optional chain + fallback)
const value = obj?.prop ?? defaultValue;
```

### Promoción

1. Fix 20 violaciones en prod
2. Añadir override de test: `"@typescript-eslint/no-non-null-assertion": "warn"`
3. Promover regla principal: `"@typescript-eslint/no-non-null-assertion": "error"`

---

## Fase 5B — `sonarjs/no-dead-store` → error (25 prod)

**Dificultad:** Baja-Media. Eliminar asignaciones a variables que nunca se leen.

### Archivos a tocar (agrupados por feature)

**app/ (3 violaciones, 3 archivos)**
```
app/(main)/[tenantId]/(dashboard)/brand-studio/layout.tsx:45
app/(main)/onboarding/page.tsx:21
app/playground/detail-panel-test/page.tsx:21 (x2)
```

**components/shared/ (2 violaciones, 1 archivo)**
```
components/shared/layout/TenantSwitcher.tsx:34,35
```

**features/ (20 violaciones, 14 archivos)**
```
features/brand/components/onboarding/StepProcessing.tsx:34
features/connections/components/ShopifyView.tsx:104
features/connections/hooks/use-whatsapp.ts:63
features/growth-studio/components/metrics-dashboard/detail-panels/AdoptionDetail.tsx:44,54
features/growth-studio/components/metrics-dashboard/detail-panels/NurtureOpportunityDetail.tsx:223
features/growth-studio/components/metrics-dashboard/offer-widgets/SourceProducts.tsx:82
features/growth-studio/components/metrics-dashboard/stage-widgets/StageCard.tsx:51
features/growth-studio/components/strategy-canvas/nodes/NodeFactory.tsx:19
features/offer-studio/api/index.ts:49
features/offer-studio/components/editions/EditionFormDialog.tsx:73
features/offer-studio/components/editor/sections/identity/IdentityPreview.tsx:53
features/offer-studio/components/landing/components/blocks/hero/Hero.tsx:187,291
features/offer-studio/components/landing/components/editor/AiRemixButton.tsx:34
features/sales/components/EventTypeForm.tsx:55 (x2)
features/sales/components/dashboard/ActivityFeedWidget.tsx:19
features/tenant-domains/hooks/use-domains.ts:88
```

### Patrón de fix

```ts
// Antes (variable asignada, nunca leída)
const unused = someFunction();
doSomethingElse();

// Después (opción A: eliminar si no tiene side effects)
someFunction(); // solo si tiene side effects necesarios
doSomethingElse();

// Después (opción B: prefijo _ si es destructuring necesario)
const { needed, _unused } = someObject;
```

### Promoción

1. Fix 25 violaciones en prod
2. Añadir override de test: `"sonarjs/no-dead-store": "warn"`
3. Promover regla principal: `"sonarjs/no-dead-store": "error"`

---

## Fase 5C — `no-unsafe-*` → error (433 prod)

**Dificultad:** Alta pero sistémica. El 80% es UN solo patrón.

### Diagnóstico raíz

`Response.json()` retorna `Promise<any>`. Cada `return res.json()` y `const data = await res.json()` propaga `any` por todo el codebase. Esto infla 5 reglas:

| Regla | Violaciones | Root cause |
|---|---|---|
| `no-unsafe-return` | 148 | `return res.json()` sin tipo |
| `no-unsafe-assignment` | 113 | `const x = await res.json()` sin tipo |
| `no-unsafe-member-access` | 99 | Acceso a `.prop` de `any` retornado |
| `no-unsafe-argument` | 63 | Pasar `any` como argumento |
| `no-unsafe-call` | 10 | Llamar función de `any` |

### Archivos con mayor concentración

| Archivo | Violaciones | Tipo |
|---|---|---|
| `lib/api/connections.ts` | ~120 | API client gigante |
| `features/offer-studio/api/index.ts` | ~25 | API client |
| `features/growth-studio/api/*.ts` | ~60 | 10+ archivos api |
| `features/*/api/*.ts` (otros) | ~20 | API clients |
| `lib/api/*.ts` (otros) | ~40 | API clients genéricos |
| `app/connections/meta/callback/page.tsx` | ~8 | OAuth handler |
| `StrategyCanvas.tsx` + `adapter.ts` | ~12 | visx type mismatch |
| Otros componentes | ~15 | Varios |

### Estrategia: 3 sub-fases

#### 5C-1: Typed fetch helper (fix estructural, ~300 violaciones)

Crear `fetchJson<T>()` en `lib/http-client.ts`:

```ts
export async function fetchJson<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetchClient(url, options);
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(res.status, body);
  }
  return res.json() as Promise<T>;
}
```

Migrar archivos api/ en orden de concentración:

1. `lib/api/connections.ts` (~120 violaciones) — el monstruo
2. `lib/api/settings.ts` + `lib/api/public.ts` (~30)
3. `features/growth-studio/api/*.ts` (~60)
4. `features/offer-studio/api/index.ts` (~25)
5. Resto de `features/*/api/*.ts` y `lib/api/*.ts` (~40)

Cada archivo:
- Reemplazar `await res.json()` por `await fetchJson<ReturnType>(url, opts)`
- O en archivos que manejan errores custom: `(await res.json()) as ReturnType`
- Verificar con `npx tsc --noEmit` después de cada archivo

#### 5C-2: Componentes y hooks (~30 violaciones)

Archivos que usan `any` sin pasar por api/:
- `app/connections/meta/callback/page.tsx` — tipar `searchParams`, `response`
- `features/copilot/hooks/use-proactive-nudges.ts` — tipar event data
- `features/copilot/hooks/use-copilot-field-sync.ts` — tipar
- `features/connections/hooks/use-google-oauth-listener.ts` — tipar MessageEvent
- `features/connections/components/OauthCallbackHandler.tsx` — tipar searchParams

#### 5C-3: StrategyCanvas visx types (~12 violaciones)

`StrategyCanvas.tsx` y `adapter.ts` — `as any` por incompatibilidad con `@visx/sankey`.
**Opción realista:** Estos 12 quedan con `eslint-disable` documentado. Crear `KNOWN_UNSAFE_VISX` comentario y excluir el archivo via ESLint override.

```js
// eslint.config.mjs — nuevo override
{
  files: ["**/strategy-canvas/**"],
  rules: {
    "@typescript-eslint/no-unsafe-assignment": "warn",
    "@typescript-eslint/no-unsafe-argument": "warn",
    "@typescript-eslint/no-unsafe-member-access": "warn",
  },
}
```

### Promoción

1. Fix 5C-1 y 5C-2 (~420 de 433 violaciones)
2. Override para strategy-canvas (12 visx)
3. Override para tests (ya no aplica — tests ya disabled via `disableTypeChecked`)
4. Promover las 5 reglas a `"error"`

---

## Fase 5D — JSDoc en exports públicos

**Dificultad:** Baja pero voluminosa. ~843 exports sin documentar.

### Scope

Solo archivos en:
- `src/features/**/api/*.ts`
- `src/features/**/hooks/*.ts`
- `src/features/**/utils/*.ts`
- `src/lib/**/*.ts`

### Formato mínimo

```ts
/** Fetches the list of offers for the current tenant. */
export async function getOffers(): Promise<OfferDTO[]> {

/** Formats a monetary amount with the tenant's locale. */
export function formatMoney(amount: number, currency: string): string {
```

Para componentes React: una línea de descripción. `@param` y `@returns` opcionales.

### Ejecución

Recorrer por feature, orden alfabético:
1. `features/audit/api/` → `features/audit/hooks/`
2. `features/brand/api/` → `features/brand/hooks/`
3. ... (todas las features)
4. `lib/api/*.ts`
5. `lib/*.ts`

### Promoción

1. Añadir JSDoc a todos los exports
2. Promover `"jsdoc/require-jsdoc"` de `"warn"` a `"error"`

---

## Orden de ejecución recomendado

| Orden | Fase | Violaciones | Tiempo estimado | Riesgo |
|---|---|---|---|---|
| 1 | 5A (non-null) | 20 | 30 min | Bajo |
| 2 | 5B (dead-store) | 25 | 30 min | Bajo |
| 3 | 5C-1 (typed fetch) | ~300 | 2-3 horas | Medio (tocar api/) |
| 4 | 5C-2 (componentes) | ~30 | 45 min | Bajo |
| 5 | 5C-3 (visx override) | 12 | 10 min | Nulo |
| 6 | 5D (JSDoc) | ~843 | 3-4 horas | Nulo |

**Total: ~7-8 horas de trabajo Claude.**

### Checkpoints de commit

- Commit después de 5A+5B (rápidos, bajo riesgo)
- Commit después de 5C-1 (el más grande)
- Commit después de 5C-2+5C-3 + promote reglas
- Commit después de 5D (JSDoc)

### Verificación en cada checkpoint

```bash
cd frontend && npx tsc --noEmit
cd frontend && npx vitest run src/__tests__/architecture/ 2>&1 | tail -4
cd frontend && npx vitest run 2>&1 | tail -4
```

---

## Estado final objetivo

```
npx tsc --noEmit                          → 0 errors
npx vitest run                            → 1071+ tests
npx vitest run src/__tests__/architecture → 8/8 (puck.config only)
npx madge --circular src/                 → 0 cycles

Reglas promovidas warn → error:
- @typescript-eslint/no-non-null-assertion (prod: error, test: warn)
- sonarjs/no-dead-store (prod: error, test: warn)
- @typescript-eslint/no-unsafe-assignment (prod: error, visx: warn)
- @typescript-eslint/no-unsafe-return (prod: error)
- @typescript-eslint/no-unsafe-argument (prod: error, visx: warn)
- @typescript-eslint/no-unsafe-member-access (prod: error, visx: warn)
- @typescript-eslint/no-unsafe-call (prod: error)
- jsdoc/require-jsdoc (error)

Cada export público tiene JSDoc.
```
