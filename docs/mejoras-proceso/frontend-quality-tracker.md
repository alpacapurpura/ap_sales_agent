# Frontend Quality — Execution Tracker

**Started:** 2026-04-13  
**Last updated:** 2026-04-14  
**Current Phase:** 1C — Reducir umbrales de complejidad

---

## Resumen Ejecutivo

| Phase | Objetivo | Estado | Errores |
|-------|----------|--------|---------|
| 1A | ESLint setup (60+ reglas, warn mode) | ✅ COMPLETA | 0 errores |
| 1B | Strict rules + fix `any`/catch/promises | ✅ COMPLETA | 0 errores |
| 1C | Reducir umbrales de complejidad | ⬜ pendiente | — |
| 2 | Prettier integration global | ⬜ pendiente | — |
| 3 | FSD boundary enforcement | ⬜ pendiente | 194 deep imports |
| 4 | Coverage thresholds | ⬜ pendiente | ~8% actual |
| 5 | Knip + Madge (dead code / circular) | ⬜ pendiente | — |

---

## Cómo Retomar en Nueva Sesión

**Lee este documento primero.** Luego:

```bash
cd /home/chris/AISALESHT/frontend
npx tsc --noEmit 2>&1 | tail -3          # Debe ser 0 errores
npx eslint src/ --format json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
total={};
[total.update({m['ruleId']:total.get(m['ruleId'],0)+1}) for f in data for m in f['messages'] if m['severity']==2]
[print(f'{c:4} {r}') for r,c in sorted(total.items(),key=lambda x:x[1],reverse=True)]
print(f'TOTAL: {sum(total.values())}')
"
npx vitest run 2>&1 | tail -4            # Debe pasar (1063 tests)
```

Regla crítica: lint/tests NATIVO en WSL — nunca via Docker.

---

## Phase 1A: ESLint Setup ✅ COMPLETA

**Objetivo:** Instalar 60+ reglas en modo `warn` sin romper nada.  
**Resultado:** 0 errores, ~12.000 warnings. TypeScript ✅.

### Tareas

- [x] Instalar plugins: sonarjs, import, boundaries, react-perf, prettier, prettier-config, jsx-a11y, globals, trivago sort-imports, prettier-plugin-tailwindcss
- [x] Crear `eslint.config.mjs` con 60+ reglas (warn mode)
- [x] Crear `prettier.config.mjs` (prep para Phase 2)
- [x] `npx eslint src/ --fix` → auto-fix Prettier (CRLF→LF) + import order
- [x] Fix manual: 1 `require()` → import en test file
- [x] `npx tsc --noEmit` → 0 errores ✅
- [x] `npx vitest run` → todos los tests pasan ✅

### Learnings 1A

- ESLint flat config + `eslint-config-next`: Next.js ya incluye `jsx-a11y` y `react-hooks` — no re-registrar plugins
- SonarJS v4: reglas con nombres diferentes a la doc. Ver con `node -e "console.log(Object.keys(require('eslint-plugin-sonarjs').rules))"`
- Boundaries v6: regla renombrada de `element-types` → `dependencies`
- `no-undef` debe desactivarse — TypeScript ya maneja esto
- Prettier + ESLint: usar `eslint-plugin-prettier/recommended` al final
- ESLint con `project: true` (type-aware) es lento (~3 min full scan)
- CRLF vs LF: archivos con CRLF generan warnings → `endOfLine: "lf"` en prettier config + `--write` fixea todos

---

## Phase 1B: Strict Rules ✅ COMPLETA

**Objetivo:** Subir 6 reglas de `warn` → `error` y eliminar todas las violations.  
**Resultado (2026-04-14):** 0 errores ESLint, 0 errores TypeScript, 1063 tests pasan.

### Reglas activadas como `error`

- [x] `@typescript-eslint/no-explicit-any`
- [x] `@typescript-eslint/no-floating-promises`
- [x] `@typescript-eslint/no-misused-promises`
- [x] `no-alert`
- [x] `no-empty`
- [x] `prefer-const`

### Todas las violations fijas ✅

| Categoría | Cantidad | Estrategia |
|-----------|----------|------------|
| `catch {}` vacíos → `catch { /* comentario */ }` | 5 | Manual |
| `alert()`/`confirm()`/`prompt()` → eslint-disable con TODO | 3 | Manual |
| `prettier/prettier` → `npx prettier --write` en archivos específicos | 12 | Script |
| `no-misused-promises` JSX attrs + args → config change | 148 → 1 | **Config fix** |
| `no-misused-promises` spread async en test → `async/await vi.importActual` | 1 | Manual |
| `no-floating-promises` → script Python + `void` insertion | 141 | **Script** |
| `no-explicit-any` → `unknown`, interfaces, eslint-disable documentado | 24 | Manual |
| TypeScript errors nuevos descubiertos tras cache reset | 7 | Manual |

### Learnings 1B (CRÍTICOS para próxima sesión)

- **`no-misused-promises` en React = falso positivo para JSX.** Configurar:
  ```js
  "@typescript-eslint/no-misused-promises": ["error", {
    checksVoidReturn: { attributes: false, arguments: false }
  }]
  ```
  Esto elimina 148/149 errores de una vez. `attributes: false` = onClick/onSubmit. `arguments: false` = setInterval/Array.forEach.

- **Script para bulk `void` insertion:** ESLint `--format json` da `filePath`, `line`, `column` exactos. Script Python inserta `void ` en col-1 (0-indexed) de cada línea. Guardarlo:
  ```bash
  npx eslint src/ --format json > /tmp/eslint.json
  # luego script Python lee /tmp/eslint.json y parchea archivos
  ```
  (Script completo disponible en learnings de esta sesión)

- **`eslint-disable-next-line` falla si hay línea en blanco entre comment y código.** El disable aplica EXACTAMENTE a la siguiente línea, no a la siguiente línea no-vacía.

- **`useState<unknown>` rompe TypeScript** cuando el estado tiene propiedades accedidas. Para respuestas de API con shape variable, usar `// eslint-disable-next-line @typescript-eslint/no-explicit-any -- TODO: define per-provider API response type` + `useState<any>`.

- **TypeScript incremental cache esconde errores.** Cambios en archivos importados pueden revelar errores TS en archivos que nunca tocaste. Son reales, no regresiones.

- **`useMutation` React Query con parámetro con default** necesita tipo explícito: `useMutation<TData, Error, TVariables | undefined>({...})`. Sin esto: `Type 'number' is not assignable to type 'void'`.

- **`document.querySelector('input[type="file"]')` retorna `Element`, no `HTMLInputElement`.** Cast necesario: `as HTMLInputElement` para acceder a `.accept`, `.value`, `.files`.

- **`prettier --write <archivos>` más confiable que `eslint src/ --fix`** para correcciones de formato en archivos específicos. El `--fix` de ESLint no siempre corre prettier en todos los archivos (puede tener problemas de timing).

- **`Record<string, any>` → `Record<string, unknown>` es seguro** en la mayoría de tipos/interfaces. Pero `ComponentType<any>` necesita `ComponentType<{ className?: string }>` o similar — `ComponentType<unknown>` NO acepta props.

- **`vi.mock("module", () => {...})` con `vi.importActual` debe ser async:**
  ```ts
  vi.mock("module", async () => {
    const actual = await vi.importActual("module");
    return { ...actual, ... };
  });
  ```
  Sin `async/await`, el spread de Promise falla con `no-misused-promises`.

---

## Deuda técnica descubierta (no era del plan) ⚠️

- [ ] **`connections/` views**: 8 archivos usan `useState<any>` para `testResult` (respuesta del test de conexión). Cada provider tiene una forma de `data` diferente. Fix correcto: definir `ConnectionTestResult<T>` genérico por provider. Actualmente con `eslint-disable`.
- [ ] **`availability-view.tsx` y `event-type-view.tsx`**: `confirm()` → AlertDialog de shadcn. Actualmente con `eslint-disable` y TODO.
- [ ] **`EditableImage.tsx`**: `prompt()` en landing editor visual. Actualmente con `eslint-disable`. Fix: input modal.
- [ ] **`useSyncAllSources.ts`**: `queryClient.invalidateQueries()` retorna promise → todos fixados con `void`. Pero sería mejor usar `Promise.all()` para hacer las invalidaciones en paralelo.
- [ ] **`event-type-form.tsx`**: bloque `try` vacío en `fetchCal` (línea ~100) — placeholder sin implementar. Needs ticket.

---

## Phase 1C: Complejidad ⬜ PENDIENTE

**Objetivo:** Reducir umbrales de complejidad cognitiva y tamaño de archivos.  
**Prerequisito:** Phase 1B completa ✅

### Prompt para iniciar Phase 1C

```
Iniciar Phase 1C (complejidad). Lee docs/mejoras-proceso/frontend-quality-tracker.md.
Estado actual: Phase 1B COMPLETA (0 errores ESLint, 0 TS errors, 1063 tests).

Paso 1: Identificar archivos que exceden nuevos umbrales:
  cd frontend
  npx eslint src/ --rule '{"max-lines": ["error", {"max": 350, "skipBlankLines": true, "skipComments": true}]}' --format json 2>/dev/null | python3 -c "import json,sys; [print(f['filePath'].replace('/home/chris/AISALESHT/frontend/src/',''), '→', f['errorCount'], 'errores') for f in json.load(sys.stdin) if f['errorCount']>0]" | sort -t→ -k2 -rn | head -20

Paso 2: Refactorizar archivos grandes (priorizar growth-studio, offer-studio — los más complejos).
  Estrategia: extraer hooks, componentes y utils. NO cambiar lógica.

Paso 3: Bajar umbrales en eslint.config.mjs:
  - sonarjs/cognitive-complexity: 20 → 15
  - max-lines: 500 → 350
  - max-lines-per-function: 100 → 75
  - max-depth: 5 → 4
  - max-params: 5 → 4
  Subir de warn → error.

Paso 4: npx eslint src/ → 0 errores. npx vitest run → pasa.
```

---

## Phase 2: Prettier Global ⬜ PENDIENTE

**Objetivo:** Formatear TODO `src/` con Prettier de forma consistente.  
**Prerequisito:** Phase 1B + 1C completas.

### Contexto

- `prettier.config.mjs` ya creado en Phase 1A ✅
- `eslint-plugin-prettier` ya integrado ✅ (Phase 1A pre-integrado)
- La mayoría de archivos tienen `prettier/prettier` violations pre-existentes
- `npx eslint src/ --fix` ya auto-aplica prettier — esto es mayormente un paso de verificación

### Tareas

- [ ] `cd frontend && npx eslint src/ --fix` → aplicar prettier a todo `src/`
- [ ] Verificar que no se rompió ningún test: `npx vitest run`
- [ ] Verificar TypeScript: `npx tsc --noEmit`
- [ ] Actualizar `lint-staged` en `package.json` para aplicar prettier en pre-commit:
  ```json
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"]
  }
  ```
- [ ] Verificar: `npx lint-staged` funciona correctamente
- [ ] `npx eslint src/ 2>&1 | grep "prettier/prettier" | wc -l` → 0
- [ ] Actualizar tracker

### Prompt para iniciar Phase 2

```
Iniciar Phase 2 (Prettier global). Lee docs/mejoras-proceso/frontend-quality-tracker.md.
Paso 1: cd frontend && npx eslint src/ --fix  (aplica prettier a todo)
Paso 2: npx tsc --noEmit + npx vitest run (verificar sin regresiones)
Paso 3: actualizar lint-staged en package.json
Paso 4: npx eslint src/ 2>&1 | grep "prettier/prettier" | wc -l → debe ser 0
```

---

## Phase 3: FSD Enforcement ⬜ PENDIENTE

**Objetivo:** Eliminar los 194 deep imports y hacer cumplir la arquitectura FSD.  
**Prerequisito:** Phase 2 completa.

### Contexto

- `eslint-plugin-boundaries v6` ya instalado (Phase 1A)
- Boundaries configurado en `warn` mode — 194 violaciones encontradas
- Principales ofensores: `offer-studio/`, `growth-studio/`

### Tareas

- [ ] Hacer inventario completo de deep imports:
  ```bash
  cd frontend && npx eslint src/ 2>&1 | grep "boundaries/dependencies" > /tmp/fsd-violations.txt
  ```
- [ ] Crear barrel exports en features que los necesiten:
  - [ ] `features/offer-studio/index.ts`
  - [ ] `features/growth-studio/index.ts`
  - [ ] `features/brand/index.ts`
  - [ ] `features/connections/index.ts`
- [ ] Mover tipos compartidos a `lib/types/`
- [ ] Mover utils compartidos a `lib/utils/`
- [ ] Mover componentes compartidos a `components/shared/`
- [ ] Resolver cross-feature imports (features importando de otros features)
- [ ] Subir `boundaries/dependencies` de `warn` → `error`
- [ ] `npx eslint src/ 2>&1 | grep "boundaries" | wc -l` → 0
- [ ] `npx vitest run` → pasa
- [ ] Actualizar tracker

### Deep Imports Catalog (poblar durante Phase 3)

| Archivo | Import problemático | Profundidad | Estrategia de fix |
|---------|--------------------|-----------|--------------------|
| (poblar al iniciar Phase 3) | | | |

### Prompt para iniciar Phase 3

```
Iniciar Phase 3 (FSD enforcement). Lee docs/mejoras-proceso/frontend-quality-tracker.md.
Paso 1: npx eslint src/ 2>&1 | grep "boundaries" > /tmp/fsd.txt → catalogar todas las violaciones
Paso 2: crear barrel exports en features/offer-studio/index.ts, features/growth-studio/index.ts
Paso 3: mover tipos compartidos a lib/types/, utils a lib/utils/
Paso 4: fix cross-feature imports
Paso 5: subir boundaries a error, verificar 0 errores
```

---

## Phase 4: Coverage Thresholds ⬜ PENDIENTE

**Objetivo:** Subir cobertura de tests de ~8% actual a umbrales mínimos.  
**Prerequisito:** Lint estable (Phase 1B mínimo).

### Hitos progresivos

- [ ] **Milestone 1:** 20% statements/branches/functions/lines
- [ ] **Milestone 2:** 40% (a definir timeline)
- [ ] **Milestone 3:** 60% en features críticos (copilot, brand, connections)

### Tareas Milestone 1

- [ ] Configurar thresholds en `vitest.config.mts`:
  ```ts
  coverage: {
    thresholds: { statements: 20, branches: 20, functions: 20, lines: 20 }
  }
  ```
- [ ] `npx vitest run --coverage` → identificar archivos que fallan
- [ ] Priorizar tests para: hooks de React Query, utils en `lib/`, servicios de API
- [ ] Agregar tests para paths críticos sin cobertura
- [ ] Verificar CI pasa en 20%
- [ ] Actualizar tracker con porcentaje real

### Prompt para iniciar Phase 4

```
Iniciar Phase 4 (coverage). Lee docs/mejoras-proceso/frontend-quality-tracker.md.
Paso 1: npx vitest run --coverage → ver % actual por feature
Paso 2: añadir threshold 20% en vitest.config.mts
Paso 3: identificar archivos críticos sin tests y agregar tests básicos
Paso 4: npx vitest run --coverage → debe pasar los thresholds
```

---

## Phase 5: Dead Code y Circular Imports ⬜ PENDIENTE

**Objetivo:** Eliminar código muerto y dependencias circulares.  
**Prerequisito:** Phase 3 (FSD estable).

### Tareas

- [ ] Instalar knip: `npm install -D knip`
- [ ] Configurar `knip.config.ts`
- [ ] `npx knip` → revisar findings (exports sin uso, archivos sin uso, dependencias sin uso)
- [ ] Fix: eliminar archivos/exports muertos identificados
- [ ] Instalar madge: `npm install -D madge`
- [ ] `npx madge --circular src/` → revisar circulares
- [ ] Fix: romper ciclos (extract a `lib/`, invert dependencies)
- [ ] Agregar knip y madge a CI pipeline (`.github/workflows/`)
- [ ] Actualizar tracker

### Prompt para iniciar Phase 5

```
Iniciar Phase 5 (dead code + circular). Lee docs/mejoras-proceso/frontend-quality-tracker.md.
Paso 1: npm install -D knip && npx knip → identificar código muerto
Paso 2: npm install -D madge && npx madge --circular src/ → identificar circulares
Paso 3: fix los más críticos
Paso 4: agregar a CI
```

---

## Log de Violations por Fase

| Fecha | Phase | Comando | Errores | Warnings | Notas |
|-------|-------|---------|---------|---------|-------|
| 2026-04-13 | Baseline | `npx eslint src/` | 13 | 0 | Config anterior (solo nextjs rules) |
| 2026-04-13 | 1A done | `npx eslint src/` | 0 | ~12.000 | Después de upgrade a 60+ reglas (warn mode) |
| 2026-04-13 | 1A done | `npx tsc --noEmit` | 0 | — | TypeScript ✅ |
| 2026-04-14 | 1B reglas activadas | `npx eslint src/` | ~600+ | — | Antes de fixes de sesión 1 |
| 2026-04-14 | 1B ~80% | `npx eslint src/` | 544 | — | Después de ~168 fixes sesión 1 |
| 2026-04-14 | 1B sesión 2 inicio | `npx eslint src/` | 529 | — | Inicio sesión 2 |
| 2026-04-14 | 1B config fix | `no-misused-promises` config | 148→1 | — | `checksVoidReturn: { attributes: false, arguments: false }` |
| 2026-04-14 | 1B completa | `npx eslint src/` | 0 | — | Todas violations fijas |
| 2026-04-14 | 1B completa | `npx tsc --noEmit` | 0 | — | TypeScript ✅ |
| 2026-04-14 | 1B completa | `npx vitest run` | 0 fallos | — | 1063 tests ✅ |

---

## Dependencias Instaladas

### Phase 1A (todas instaladas ✅)

| Package | Notas |
|---------|-------|
| `eslint-plugin-sonarjs@4.0.2` | Cognitive complexity, code smells |
| `eslint-plugin-import@2.32.0` | Import ordering |
| `eslint-plugin-boundaries@6.0.2` | FSD architecture enforcement |
| `eslint-plugin-react-perf@3.x` | No inline objects/arrays como props |
| `prettier@3.8.2` | Formatter |
| `eslint-config-prettier@10.x` | Desactiva reglas que conflictúan con Prettier |
| `eslint-plugin-prettier@5.x` | Prettier como regla ESLint |
| `globals@16.x` | Globals para flat config |
| `@trivago/prettier-plugin-sort-imports@5.x` | Sort imports en Prettier |
| `prettier-plugin-tailwindcss@0.7.2` | Sort Tailwind classes |

### Phase 5 (pendiente instalar)

| Package | Cuándo |
|---------|--------|
| `knip` | Al iniciar Phase 5 |
| `madge` | Al iniciar Phase 5 |

---

## Comandos de Referencia

```bash
# ESLint — verificar errores por regla (JSON, no timeout por grep)
npx eslint src/ --format json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
total={}
[total.update({m['ruleId']:total.get(m['ruleId'],0)+1}) for f in data for m in f['messages'] if m['severity']==2]
[print(f'{c:4} {r}') for r,c in sorted(total.items(),key=lambda x:x[1],reverse=True)]
print(f'TOTAL: {sum(total.values())}')
"

# ESLint — listar archivos + líneas de una regla específica
npx eslint src/ --format json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
rule='@typescript-eslint/no-floating-promises'
for f in data:
    errs=[(m['line'],m['column']) for m in f['messages'] if m['severity']==2 and m['ruleId']==rule]
    if errs: print(f['filePath'].replace('/home/chris/AISALESHT/frontend/src/',''), errs)
"

# Script void-insertion (floating-promises batch fix)
# 1. Guardar JSON: npx eslint src/ --format json > /tmp/eslint.json
# 2. Correr script:
python3 << 'SCRIPT'
import json
data = json.load(open('/tmp/eslint.json'))
file_errors = {}
for f in data:
    errs = [(m['line'], m['column']) for m in f['messages']
            if m['severity'] == 2 and m['ruleId'] == '@typescript-eslint/no-floating-promises']
    if errs:
        file_errors[f['filePath']] = sorted(errs, reverse=True)
fixed = 0
for filepath, errors in file_errors.items():
    lines = open(filepath).readlines()
    mod = False
    for line_num, col in errors:
        idx, col_idx = line_num - 1, col - 1
        if col_idx >= len(lines[idx]): continue
        if lines[idx][col_idx:].lstrip().startswith(('void ', 'await ', 'return ')): continue
        lines[idx] = lines[idx][:col_idx] + 'void ' + lines[idx][col_idx:]
        mod, fixed = True, fixed + 1
    if mod:
        open(filepath, 'w').writelines(lines)
print(f"Fixed {fixed} in {len(file_errors)} files")
SCRIPT

# Prettier (específico, más confiable que eslint --fix para prettier)
npx prettier --write src/path/to/file.tsx

# TypeScript
cd frontend && npx tsc --noEmit

# Tests
cd frontend && npx vitest run
cd frontend && npx vitest run --coverage
cd frontend && npx vitest run src/features/{domain}/
```
