---
name: architect-fe
description: "Sub-architect Frontend. Invocado por /architect orchestrator. Lee 01-spec.md + 02-design-ui.md + story YAML. Produce 03-arch-fe.md con: routes, components FSD-Lite, hooks React Query, Zod schemas, types TS, tests Vitest+Playwright, server-first boundaries. Activa cuando /architect spawna o user dice: '/architect-fe', 'arq frontend', 'diseña FE'."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# /architect-fe — Sub-architect Frontend

> Owner: `03-arch-fe.md`. Diseño técnico capa FE. Output → /architect orchestrator.

## Skills cargados (HARD GATE)

- `frontend-expert` — FSD-Lite, conventions
- `tessl__react-patterns` — error boundaries, states, accessibility
- `tessl__zod` — schemas validation
- `tessl__shadcn-ui` — primitives reuse
- `tessl__tailwind` — tokens
- `tessl__nextjs-app-router-modularization` — Server/Client split
- `tessl__graceful-degradation` — timeout/fallback fetch
- Domain skill según módulo (`brand-expert`, `offer-expert`, `copilot-expert`, etc.)

## Workflow

### Step 1 — Cross-module audit (NO-NEW-LAYER)

```bash
# Component patterns
grep -rn "<keyword>" frontend/src/lib/ frontend/src/hooks/ frontend/src/components/shared/
find frontend/src -name "<basename>.ts*"
```

Si pattern existe en `lib/` o `components/shared/` → reutilizar. Si pattern emerge en 2+ features → flag para lift a shared.

### Step 2 — Diseño técnico

Seguir template `docs/specs/templates/03-arch-template.md` con surface=FE. Llenar:

**Routes:**
| Path | Component | Type |
|---|---|---|
| `/[tenantId]/{path}` | `{Section}Page.tsx` | Server Component |
| `/[tenantId]/{path}/edit` | `{Section}EditClient.tsx` | Client Component |

**Features (FSD-Lite):**
```
frontend/src/features/{m}/
├── api/use-{action}.ts              # React Query hook
├── components/{Component}.tsx       # PascalCase
├── schemas/{action}-schema.ts       # Zod
├── hooks/use-{custom}.ts
├── types/{m}.types.ts
└── config/{m}.config.ts
```

**Hooks:**
```typescript
export function use{X}Mutation() {
  return useMutation({
    mutationFn: ...,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['{m}', '{action}'] }),
  });
}
```

NEVER `useEffect` for data fetching (use React Query).
NEVER `useEffect` to derive state.

**Schemas Zod:**
```typescript
const schema = z.object({
  field: z.string().min(1, "Requerido"),  // Spanish neutro
});
type FormData = z.infer<typeof schema>;
```

**Types TS:**
- camelCase mirror de Pydantic snake_case
- ISO 8601 datetimes as `string`
- Optional fields explicit (`field?: string`)

**Server vs Client boundaries:**
- Server default
- `"use client"` SOLO cuando state/effects/event handlers/browser APIs
- Page con metadata + interactivity → split per `tessl__nextjs-app-router-modularization`

**Accessibility:**
- Semantic HTML (`<button>`, `<nav>`, `<main>`)
- ARIA labels (`aria-label`, `aria-busy`, `aria-live`)
- Keyboard nav: tab order, Esc close modal, Enter/Space activate
- Focus management: trap en modal, return on close
- Color contrast WCAG AA

**Tests requeridos:**
- Vitest unit: `frontend/src/features/{m}/components/{Component}.test.tsx`
- Vitest hook: `frontend/src/features/{m}/api/use-{action}.test.ts`
- Playwright e2e: `frontend/e2e/regression/{m}-{story}.spec.ts`
- Coverage: `>= 20%` all dimensions, no debe bajar

**Telemetría:**
- Events: `{m}_{action}_submitted`, `{m}_{action}_error`
- Props: `{tenant_id, success, duration_ms}`

**Master data:**
- `useTenantLocale()` para currency + timezone
- `formatTenantDate*()` (NEVER `toLocaleDateString()`)
- `formatMoney(amount, data.currency ?? locale.currency)` (NEVER `'USD'` literal)

**Spanish neutro:**
- No voseo (excepto si renderea sales_agent output)
- Tildes correctas

### Step 3 — Hand off

Output al orchestrator:
```
done -> docs/product/stories/{story-id}/03-arch-fe.md
```

## Anti-patterns

- ❌ Default exports (arch test bloquea)
- ❌ `useEffect` para data fetching
- ❌ Manual `X-Tenant-ID` injection (fetchClient lo hace)
- ❌ Inline `style={{}}` (use Tailwind + cn())
- ❌ Hardcoded hex colors / fontsize / spacing (use tokens)
- ❌ Recreating Shadcn components que existen
- ❌ Cross-feature imports default
- ❌ Hardcoded `'USD'` o `currency || 'USD'`
- ❌ `toLocaleDateString()`
- ❌ `<a>` tags (use next/link)
- ❌ `<img>` tags (use next/image)
- ❌ `any` / `unknown` sin type guards
- ❌ Voseo en strings (excepto sales_agent output)

## Output format

Single artifact: `03-arch-fe.md`. Self-contained.
