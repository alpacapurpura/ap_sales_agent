# Runtime Quality Checklist (FE)

> Checklist OBLIGATORIO antes de marcar PR FE shipped o REVIEW.md PASS.
> Origen: S4 PI-1 audit failure 2026-04-30 — 9 quality bugs slipped (3 CRITICAL infinite loop / stale closure / routing 404) con 122 Vitest verde + lint 0 errors.
>
> Tests verde + lint verde NO es suficiente para FE. Mocks excesivos esconden bugs runtime.

## Live verification gate (OBLIGATORIA FE PRs ≥ M)

Antes de cerrar PR con verdict PASS, builder/auditor **DEBE** invocar `chrome-devtools-verify` skill y verificar:

1. ✅ Page nueva carga sin Build Error / Console Error
2. ✅ NO `Maximum update depth exceeded` runtime
3. ✅ Routing entre rutas con `[tenantId]` mantiene tenant prefix correctamente
4. ✅ Click handlers happy path NO 404 al navegar
5. ✅ Data fetching funciona contra BE real OR mock razonable
6. ✅ Si dialog → submit → next dialog: chain completa sin re-render loops

**Cuándo skip:** PR docs-only, config-only, fix trivial 1 archivo sin UI changes.

**Cuándo NO skip:**
- Toca `frontend/src/features/**/components/`
- Agrega/modifica `frontend/src/app/**/page.tsx`
- Usa `useEffect` con deps no triviales
- Usa `useRouter().push(...)` o links a otras rutas
- Dialog/modal chains (state mgmt across modals)

**Si chrome-devtools-verify NO disponible (dev-app no levantado):** escalate a Chris staging gate manual ANTES de marcar PR shipped. RESULT.md verdict = `PASS pending Chris staging gate manual`.

---

## React useEffect deps checklist

Antes de approve cualquier `useEffect`:

| Pattern | Decisión |
|---|---|
| `useEffect(..., [open, form, mutation])` | ❌ FAIL — `form`/`mutation` refs unstable cada render → infinite loop |
| `useEffect(..., [open])` con `form.reset()` adentro | ✅ OK con `// eslint-disable-next-line react-hooks/exhaustive-deps` + comment justificación (form.reset ESTABLE pero deps incompletas) |
| `useEffect(() => router.replace(...), [filters, router])` | ⚠ OK si filters stable. Pero corre on mount → URL replace innecesario. Add `useRef(true)` skip-first-render pattern |
| `useEffect(..., [])` con dependencies del scope | ❌ FAIL si captura stale state |
| `useMemo(() => fn(handler), [otherDep])` con `handler` recreated cada render | ❌ FAIL — `handler` no in deps; useCallback handler primero con deps `[]` (setters React son stable) |

### Pattern stable handlers via useCallback con setters como deps

```typescript
// ✅ React state setters son ESTABLES por design — useCallback con [] es correcto
const stableHandler = React.useCallback((id: string) => {
  setSelectedIds((prev) => [...prev, id]);  // setSelectedIds es stable
}, []);
```

### Pattern skip-first-render (URL sync)

```typescript
const isFirstRender = React.useRef(true);
React.useEffect(() => {
  if (isFirstRender.current) {
    isFirstRender.current = false;
    return;
  }
  const t = setTimeout(() => router.replace(`?${sp}`, { scroll: false }), 300);
  return () => clearTimeout(t);
}, [filters, limit, offset, router]);
```

---

## Hooks con state-derived params (stale closure prevention)

❌ **PROHIBIDO:** Hooks que capturan `id` en closure de `mutationFn` cuando `id` viene de state que cambia post-mount:

```typescript
// ANTI-PATTERN — id capturado al construir hook (closure stale)
export function useAddCampaignStepMutation(campaignId: string) {
  return useMutation({
    mutationFn: async (payload) => {
      // campaignId capturado AL CONSTRUIR HOOK — si caller pasa "" inicial → POST /api/v1/campaigns//steps/ → 404
      await fetch(`/api/v1/campaigns/${campaignId}/steps/`, ...);
    }
  });
}

// Caller: const [id, setId] = useState<string | null>(null);
//         const addStep = useAddCampaignStepMutation(id ?? "");  // ← closure captura ""
//         setId(realId);
//         addStep.mutateAsync({...});  // ← usa "" stale, POST 404
```

✅ **CORRECTO:** `id` en payload del mutate (per-call):

```typescript
export interface AddCampaignStepPayload {
  campaignId: string;  // ← per-call
  step_type: string;
}

export function useAddCampaignStepMutation() {
  return useMutation<Response, Error, AddCampaignStepPayload>({
    mutationFn: async ({ campaignId, ...body }) => {
      await fetch(`/api/v1/campaigns/${campaignId}/steps/`, {body: JSON.stringify(body)});
    }
  });
}
```

---

## Routing tenant prefix (Next.js App Router con `[tenantId]`)

❌ **PROHIBIDO:** literal `router.push("/sales/...")` sin `[tenantId]` prefix en cualquier componente bajo route `[tenantId]/...`:

```typescript
// ANTI-PATTERN — hardcoded path sin tenantId → 404
router.push("/sales/campa%C3%B1as/nuevo");
```

❌ **PROHIBIDO:** parsing de URL via `window.location.pathname.split("/")[1]`:

```typescript
// ANTI-PATTERN — frágil, no SSR-safe
const tenantId = window.location.pathname.split("/")[1];
router.push(`/${tenantId}/sales/campa%C3%B1as/${id}`);
```

✅ **CORRECTO:** `useParams<{tenantId: string}>()` de `next/navigation`:

```typescript
import { useParams, useRouter } from "next/navigation";

export function MyComponent() {
  const router = useRouter();
  const params = useParams<{ tenantId: string }>();
  router.push(`/${params.tenantId}/sales/campa%C3%B1as/${id}`);
}
```

---

## Mock anti-patterns (Vitest + React)

❌ **PROHIBIDO:** Mock completo del hook bajo prueba:

```typescript
// ANTI-PATTERN — mock devuelve refs estables artificiales → esconde infinite loops + stale closures
vi.mock("../api/use-create-segment-mutation", () => ({
  useCreateSegmentMutation: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false }))
}));
```

✅ **PREFERIDO:** MSW + react-query real (validates useEffect deps reales):

```typescript
import { setupServer } from "msw/node";
import { rest } from "msw";

const server = setupServer(
  rest.post("/api/v1/campaigns/segments/", (req, res, ctx) =>
    res(ctx.json({ id: "seg-123" }))
  )
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Component usa useCreateSegmentMutation REAL
```

❌ **PROHIBIDO:** path matching laxo en routing assertions:

```typescript
// ANTI-PATTERN — "stringContaining" matchea "/sales/x?segment_id=seg-id" Y "/x?seg-id" Y cualquier path con seg-id
expect(mockPush).toHaveBeenCalledWith(expect.stringContaining("seg-id"));
```

✅ **CORRECTO:** full path enforcement:

```typescript
expect(mockPush).toHaveBeenCalledWith(
  "/test-tenant/sales/campa%C3%B1as/nuevo?segment_id=seg-id"
);
```

❌ **PROHIBIDO:** Mock `next/navigation` SIN incluir TODAS las exports usadas:

```typescript
// ANTI-PATTERN — si componente usa useParams runtime → tests pasan, real browser falla
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  // ← falta useParams!
}));
```

✅ **CORRECTO:** Mock incluye TODAS las exports que el componente importa:

```typescript
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, back: vi.fn(), replace: vi.fn() }),
  useParams: () => ({ tenantId: "test-tenant" }),  // OBLIGATORIO si componente usa useParams
}));
```

❌ **PROHIBIDO:** Factory inline plain function (no permite chain `.mockReturnValue`):

```typescript
// ANTI-PATTERN — useHook no es vi.fn(), tests no pueden override per-test
vi.mock("../api/x", () => ({ useHook: () => ({ data: ... }) }));
```

✅ **CORRECTO:** wrap factory en vi.fn() para chain methods:

```typescript
vi.mock("../api/x", () => ({
  useHook: vi.fn(() => ({ data: defaultData })),  // permite vi.mocked(useHook).mockReturnValue per-test
}));
```

---

## Dead code / unused imports

❌ Imports unused en componentes (ESLint `unused-imports` warn) — SIEMPRE eliminar.

❌ `cn` import sin usage en componente — eliminar.

❌ Helper functions declared dentro componente sin call → mover a utils o eliminar.

---

## Skeleton/list rendering — stable keys

❌ **PROHIBIDO:** key={index} para skeleton cells/rows:

```typescript
// ANTI-PATTERN — React docs warn key={index}
{Array.from({ length: 10 }).map((_, i) => (
  <TableRow key={`skeleton-${i}`}>
    {columns.map((_, ci) => (
      <TableCell key={ci}>...</TableCell>  // ← key={index}
    ))}
  </TableRow>
))}
```

✅ **CORRECTO:** prefijo + column id stable:

```typescript
{columns.map((col, ci) => (
  <TableCell key={`skeleton-cell-${col.id ?? ci}`}>...</TableCell>
))}
```

---

## Auditor invocation checklist (read source + grep)

Cuando builder spawnea auditor o auditor agent paused/killed → resume Opus auditor (NO PM fallback). Auditor MUST execute en orden:

1. ✅ Run gates locales nativo (tsc/eslint/vitest) — necesario pero NO suficiente
2. ✅ **Read full source de cada archivo PR-touched** — buscar anti-patterns:
   - useEffect deps con `form`, `mutation`, `queryClient`, hook returns objects → flag CRITICAL
   - Hooks que capturan `id` en constructor closure cuando `id` viene de state changing → flag CRITICAL
   - `router.push(...)` strings literales sin `[tenantId]` prefix → flag CRITICAL
   - `window.location.pathname.split(...)` parsing en client → flag HIGH (use `useParams`)
   - Imports unused → flag HIGH
   - useMemo deps incompletos → flag HIGH
   - Skeleton arrays con `key={index}` → flag MEDIUM
   - Mock completo del hook bajo prueba → flag MEDIUM (test smell)
   - `expect.stringContaining(...)` para routing assertions → flag MEDIUM
3. ✅ **Live verification** (sección anterior) — chrome-devtools-verify O escalate Chris staging
4. ✅ Solo si pasos 1-3 verde → REVIEW.md PASS
5. Si CUALQUIER finding flag CRITICAL/HIGH/MEDIUM → REVIEW.md WARN o FAIL + builder fix loop O escalate PM si fix > 30 LOC

---

## Cuándo invocar este checklist

- ✅ `nicolify-frontend` builder Phase 1 implement (mientras escribe código)
- ✅ `nicolify-frontend` builder Phase 2 antes spawn auditor
- ✅ `nicolify-frontend-auditor` Phase audit antes producir REVIEW.md
- ✅ Bug fix FE (un check rápido pre-commit)
