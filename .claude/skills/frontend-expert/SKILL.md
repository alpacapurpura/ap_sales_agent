---
name: frontend-expert
description: "Frontend specialist for Next.js 16 App Router + React 19 + Tailwind + Shadcn UI using Feature-Sliced Design Lite (domain-grouped features/, not traditional layers). Use when: creating responsive layouts, building interactive forms/dashboards, implementing dynamic routes, integrating Shadcn UI components, refactoring UI architecture, configuring Tailwind theming, wiring React Query hooks to backend APIs, or solving Server/Client Component boundaries. Triggers: 'nueva funcionalidad', 'modifica el front', 'crea un componente', 'refactoriza la UI', 'implementa layout', 'configura rutas', 'integra con la API', 'arregla el estilo'."
---

# SOP — Flujo de Trabajo

Sigue este orden para cualquier tarea frontend:

1. **Ubicación:** Lee `docs/domains/INDEX.md` → identifica el feature/dominio destino.
2. **Explorar código existente:** Lista `frontend/src/features/{nombre}/` y lee archivos relevantes. Consulta `frontend/src/components/` para reutilizar primitivos.
3. **Tests (TDD):** Escribir tests para hooks y componentes clave ANTES de implementar (ver `references/testing-patterns.md`). El test debe fallar (RED). Para features existentes sin tests, cubrir comportamiento actual primero.
4. **Scaffold (solo features nuevas):**
   ```bash
   python .claude/skills/frontend-expert/scripts/scaffold_feature.py <nombre-en-kebab-case> --layer features --path frontend/src
   ```
   Detente si el módulo no existe en INDEX — propón nombre y propósito, espera confirmación.
5. **Crear/modificar componentes:** Usa la plantilla [component.tsx](frontend-expert/assets/templates/component.tsx) y las reglas de [component-rules.md](frontend-expert/references/component-rules.md).
6. **Integrar datos:** Si necesita fetching/mutaciones, sigue [api-standards.md](frontend-expert/references/api-standards.md).
7. **Quality runtime checklist OBLIGATORIO:** lee [runtime-quality-checklist.md](frontend-expert/references/runtime-quality-checklist.md) antes de commit Y antes de spawn auditor. Cubre: useEffect deps, stale closures, routing tenantId, mock anti-patterns, live verification gate.
8. **Live verification:** invocá `chrome-devtools-verify` skill antes de marcar PR shipped (FE PR ≥ M). Si dev-app no disponible → escalate Chris staging gate manual.

## Arquitectura (FSD-Lite)

Estructura plana agrupada por dominio. Detalles completos en [fsd-cheatsheet.md](frontend-expert/references/fsd-cheatsheet.md).

| Capa | Propósito |
| ---- | --------- |
| `src/features/{dominio}/` | Módulo autocontenido de negocio |
| `src/components/ui/` | Primitivos Shadcn UI |
| `src/components/shared/` | Layouts y componentes globales |
| `src/app/` | Solo routing y layouts de alto nivel |

**Reglas de importación:** Public API via `index.ts` — sin deep imports entre features. `shared` nunca importa de `features`.

### Decisión de ubicación

- **Componente de un dominio** → `features/{dominio}/components/`
- **Componente genérico/reutilizable** → `components/shared/` o `components/ui/`
- **UI cruza módulos** → Va en el feature "dueño" de los datos principales. Datos secundarios via Public API de otros features.
- **Feature nueva sin documentar** → Detente, propón nombre, espera confirmación, luego scaffold.

## Referencias (lee solo cuando necesites)

- **Estructura e imports:** [fsd-cheatsheet.md](frontend-expert/references/fsd-cheatsheet.md)
- **Server vs Client Components:** [component-rules.md](frontend-expert/references/component-rules.md)
- **Fetching, mutaciones, caché:** [api-standards.md](frontend-expert/references/api-standards.md)
- **Patrones de arquitectura:** [frontend-patterns.md](frontend-expert/references/frontend-patterns.md)
- **Documentación AI-optimizada:** [ai-documentation.md](frontend-expert/references/ai-documentation.md)
- **Estilos y theming Tailwind:** [styling-rules.md](frontend-expert/references/styling-rules.md)
- **Stack tecnológico:** [tech-stack.md](frontend-expert/references/tech-stack.md) — si hay discrepancia con el código real, el código manda.

## Ejemplos

**1. "Necesito un componente para mostrar el perfil del lead en el dashboard de ventas."**
- Dominio: `sales` → `features/sales/components/lead-profile.tsx`
- Exportar en `features/sales/index.ts`
- No crear `entities/lead` salvo que se use en múltiples features

**2. "Crea un botón que haga scroll hacia arriba."**
- Genérico → `components/shared/` o `components/ui/`
- Requiere `onClick` → Client Component (`"use client"`)
- Usar plantilla `component.tsx` + iconos `lucide-react`

## Troubleshooting

| Problema | Solución |
| -------- | -------- |
| "Cannot access X from Y" | Importar desde `index.ts` (Public API). Si hay dependencia circular, mover lógica compartida a `shared`. |
| Hydration Mismatch | Usar `useEffect` con flag `isMounted` antes de renderizar UI dependiente del cliente. |
| Server Action Error | Solo pasar JSON plano (strings, números, booleanos) a través del límite Server→Client. |
| ¿Dónde va este componente? | Ante la duda: `features/{dominio}/components/`. Refactorizar después es más barato que sobre-ingenierizar. |

## E2E Testing

**TDD aplica también a E2E:** Para rutas nuevas, escribir el smoke test ANTES de implementar la página.

**E2E smoke es obligatorio para rutas nuevas o flujos críticos modificados.**

- Agregar smoke test en `frontend/e2e/specs/smoke/` si es ruta nueva o crítica (suffix `.smoke.spec.ts`)
- Agregar regression test en `frontend/e2e/specs/regression/{domain}/` para flujos completos
- Usar POM de `frontend/e2e/pages/` o crear uno nuevo
- Ejecutar nativamente: `cd frontend && npm run test:e2e:smoke` (NUNCA `make e2e-smoke`)
- Requiere dev containers corriendo (`docker compose up -d`)
- **Para detalles completos: invocar skill `playwright-expert` (SSoT — Clerk auth, POMs, fixtures, mocks, CI, anti-patterns, recipe agregar smoke).** Stub: `.claude/rules/e2e-testing.md`

## Constraints (CRITICAL — read last)

- **Anti-alucinación:** Si un componente, hook o tipo no aparece al explorar el código real, **no existe**. Los docs de dominio son orientación de negocio, nunca inventario técnico.
- **Server-First:** Todos los componentes son Server Components por defecto. Solo agregar `"use client"` en nodos hoja que usen `useState`, `useEffect`, o event handlers.
- **No inventar utilidades:** Usar `cn()` de `shared/lib/utils.ts` para clases Tailwind. No crear helpers duplicados.
- **Imports:** Relativos dentro del mismo slice (`./ui/MiComponente`). Alias global entre slices (`@/features/other`).

## Project invariants (read on demand)

- `references/frontend-quality.md` — ESLint 60+ rules, TS strict, Vitest, 10 arch tests
- `references/runtime-quality-checklist.md` — **OBLIGATORIO leer antes commit y antes spawn auditor**. useEffect deps, stale closures, routing tenantId, mock anti-patterns, live verification gate (origen S4 PI-1)
- `references/studio-section-pages.md` — lazy-loading per-section pattern (brand/offer/futuros)
- E2E Playwright → invocar skill `playwright-expert` (SSoT migrada 2026-05-04 — más amplia: arquitectura, Clerk auth deep-dive, freshness gate, recipe agregar smoke, POMs, fixtures+mocks, CI+flake debugging, anti-patterns)
