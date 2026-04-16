# Prompt — Fase 5 Calidad Excepcional Frontend

> Copiar y pegar completo en nueva conversación de Claude Code.

---

Ejecuta el plan de calidad `docs/plans/fase-5-quality-plan.md`. Lee ese archivo COMPLETO primero.

## Contexto

Branch `development`, commit `60a8ebf7`. Fases 1-4 ya completadas:
- 8/8 arch tests, allowlists vacíos (excepto puck.config documentado)
- 0 circulares, 0 exhaustive-deps suppressions
- 6 reglas ESLint ya promovidas a error
- tsc 0 errors, 1071 tests passing

## Lo que debes hacer

Ejecutar las 4 sub-fases en orden, commiteando en los checkpoints marcados en el plan:

### Fase 5A: `no-non-null-assertion` → error (20 prod)
- Archivo por archivo, reemplazar `obj!.prop` con guard explícito o `?.` + fallback
- El plan tiene la lista exacta de 20 violaciones con archivo:línea
- Al terminar: añadir override test `"@typescript-eslint/no-non-null-assertion": "warn"` y promover regla a `"error"` en `eslint.config.mjs`

### Fase 5B: `sonarjs/no-dead-store` → error (25 prod)
- Eliminar variables asignadas y nunca leídas
- El plan tiene la lista exacta de 25 violaciones con archivo:línea
- Al terminar: añadir override test `"sonarjs/no-dead-store": "warn"` y promover a `"error"`

**COMMIT 1** después de 5A+5B.

### Fase 5C: `no-unsafe-*` → error (433 prod, 80% es un patrón)

**5C-1: Typed fetch helper** — El fix estructural. `Response.json()` retorna `any`, infecta todo.
- Crear `fetchJson<T>()` en `lib/http-client.ts` (ver patrón en el plan)
- Migrar archivos api/ en orden de concentración (el plan lista el orden exacto)
- El archivo más grande es `lib/api/connections.ts` (~120 violaciones solo)
- Patrón: reemplazar `return res.json()` con `return res.json() as Promise<MyType>` o usar `fetchJson<MyType>()`
- Verificar `npx tsc --noEmit` después de cada archivo grande

**COMMIT 2** después de 5C-1.

**5C-2: Componentes y hooks** — ~30 violaciones restantes fuera de api/
- Tipar event data, searchParams, OAuth responses
- El plan lista los 5 archivos específicos

**5C-3: StrategyCanvas visx override** — 12 violaciones irresolubles por incompatibilidad `@visx/sankey`
- Crear override en `eslint.config.mjs` para `**/strategy-canvas/**` dejando esas 3 reglas en warn
- Promover las 5 reglas `no-unsafe-*` a `"error"`

**COMMIT 3** después de 5C-2+5C-3.

### Fase 5D: JSDoc en exports públicos (~843)
- Recorrer `features/**/api/`, `features/**/hooks/`, `features/**/utils/`, `lib/**`
- Formato: una línea de JSDoc antes de cada `export function/const/class`
- Promover `jsdoc/require-jsdoc` a `"error"`

**COMMIT 4** después de 5D.

## Reglas de trabajo

1. Nativo siempre: tsc/vitest/eslint NATIVO en WSL, NUNCA docker exec
2. Commitear solo archivos de esta sesión: `git add path/to/file` (nunca `git add .`)
3. Conventional commits: `refactor(frontend): fase-5X — descripción`
4. Verificación en cada commit:
   ```bash
   cd frontend && npx tsc --noEmit
   cd frontend && npx vitest run 2>&1 | tail -4
   cd frontend && npx vitest run src/__tests__/architecture/ 2>&1 | tail -4
   ```
5. Si una fase se vuelve demasiado grande (5C-1 o 5D), commitear por bloques lógicos
6. No tocar tests que no estén rotos — solo cambiar la regla en el override

## Priorización si el contexto se agota

Si no alcanza para todo en una sesión:
1. **5A + 5B** = rápido, bajo riesgo, alto impacto visible → SIEMPRE hacer
2. **5C-1** = el más valioso pero largo → hacer `lib/api/connections.ts` mínimo
3. **5C-2 + 5C-3** = rápido si 5C-1 está hecho
4. **5D** = se puede hacer en sesión aparte, 0 riesgo

Después de cada commit: `git push origin development`.
