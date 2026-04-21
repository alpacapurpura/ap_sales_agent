# ESLint warnings cleanup — plan de ejecución

**Fecha snapshot:** 2026-04-21
**Baseline:** 2968 warnings, 0 errors
**Branch:** `development`
**Origen del snapshot:** sesión del 2026-04-20/21 que refactorizó Settings al patrón Finder brand-studio (commits `6b2280b7..157063e6`). Durante esa sesión se limparon 41 warnings (unused imports/vars/console/dead-stores) y se corrigieron 15 errores blocker preexistentes. El resto queda documentado aquí para una sesión dedicada.

## Contexto — por qué este doc existe

- Gate `/test-frontend` acepta warnings, bloquea errors. Actualmente en verde (0 errors).
- Baseline 2026-04-15 registró ~5863 warnings (`.claude/rules/frontend-quality.md`). Hoy 2968. Reducción orgánica sostenida pero sin meta cero.
- Reglas enforce-as-warn están ahí para señalar deuda, no para ignorarse. Al vender el código, cada warning es una pregunta del due-diligence.
- Zerar las 2968 restantes en una sola sesión no es viable: muchas requieren juicio por caso (nullish coalescing), refactor estructural (max-lines, complexity) o pueden introducir regresiones sutiles (react-perf).

## Reproducción del snapshot

```bash
cd /home/chris/AISALESHT/frontend
rm -f .eslintcache
./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache > /tmp/eslint.log 2>&1
echo "exit=$?"
tail -3 /tmp/eslint.log
```

Conteo por regla (ordenado por count, segundo número = # archivos afectados):

```bash
./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache --format json 2>/dev/null \
  | python3 -c "
import json,sys,collections
d=json.load(sys.stdin)
by_rule=collections.Counter(); by_files=collections.defaultdict(set)
for f in d:
  fp=f['filePath'].split('/frontend/')[-1]
  for m in f['messages']:
    if m['severity']!=1: continue
    r=m.get('ruleId') or 'unknown'
    by_rule[r]+=1; by_files[r].add(fp)
for r,c in by_rule.most_common():
  print(f'{c}\t{len(by_files[r])}\t{r}')
"
```

## Inventario por regla (2968 total)

| # warns | # files | Rule | Riesgo | Auto-fixable | Batch |
|--------:|--------:|------|--------|--------------|-------|
| 670 | 193 | `react-perf/jsx-no-new-function-as-prop` | **alto** — useCallback mal puesto rompe deps; afecta re-renders reales | no | D |
| 516 | 383 | `jsdoc/require-description` | bajo | no, script | A |
| 265 | 89 | `@typescript-eslint/prefer-nullish-coalescing` | medio — `a \|\| b` vs `a ?? b` diverge cuando `a` ∈ {0,"",false} | parcial (suggestions) | B |
| 239 | 98 | `react-perf/jsx-no-new-object-as-prop` | **alto** — mismo riesgo que 670 | no | D |
| 153 | 88 | `sonarjs/no-duplicate-string` | bajo | no, manual | C |
| 132 | 119 | `max-lines-per-function` | **alto** — requiere descomponer funciones | no | E |
| 129 | 56 | `@typescript-eslint/no-unused-vars` | bajo — borrar import/var o prefijar `_` | sí | A |
| 125 | 66 | `sonarjs/no-nested-conditional` | medio — nested ternaries → if/else o early return | no | E |
| 122 | 37 | `react-perf/jsx-no-new-array-as-prop` | **alto** | no | D |
| 110 | 62 | `no-nested-ternary` | medio | no | E |
| 93 | 36 | `sonarjs/unused-import` | bajo | sí | A |
| 49 | 14 | `@typescript-eslint/no-non-null-assertion` | medio — cada `!` es contrato invisible | no | C |
| 44 | 12 | `@typescript-eslint/no-empty-function` | bajo — usar `noop` o `undefined` | no | A |
| 43 | 43 | `max-lines` | alto — archivos >350 líneas, split por sección | no | E |
| 36 | 22 | `prefer-destructuring` | bajo | sí | A |
| 34 | 29 | `complexity` | alto — cognitive complexity | no | E |
| 27 | 14 | `no-console` | bajo — borrar o conditional | sí, manual | A |
| 25 | 2 | `@typescript-eslint/no-explicit-any` | alto — tipar correctamente | no | C |
| 22 | 18 | `react-perf/jsx-no-jsx-as-prop` | alto | no | D |
| 20 | 9 | `@typescript-eslint/no-base-to-string` | medio — `${obj}` → JSON.stringify | no | C |
| 17 | 13 | `import/order` | bajo | sí | A |
| 17 | 6 | `jsx-a11y/label-has-associated-control` | medio — a11y | no | C |
| 11 | 7 | `@typescript-eslint/require-await` | bajo | no | C |
| 10 | 4 | `@typescript-eslint/no-redundant-type-constituents` | bajo | no | C |
| 8 | 3 | `no-restricted-globals` | medio | no | C |
| 8 | 2 | `@typescript-eslint/no-unsafe-assignment` | medio | no | C |
| 6 | 6 | `@typescript-eslint/consistent-type-imports` | bajo | sí | A |
| 5 | 4 | `sonarjs/no-nested-template-literals` | bajo | no | C |
| 4 | 2 | `@next/next/no-img-element` | bajo — `<Image />` | no | C |
| 4 | 3 | `sonarjs/no-nested-functions` | medio | no | E |
| 3 | 3 | `@typescript-eslint/prefer-optional-chain` | bajo | sí | A |
| 3 | 2 | `@typescript-eslint/only-throw-error` | bajo | no | C |
| 3 | 3 | `sonarjs/max-switch-cases` | medio | no | E |
| 3 | 3 | `sonarjs/no-dead-store` | bajo | no | A |
| 2 | 2 | `jsx-a11y/iframe-has-title` | bajo | no | C |
| 2 | 1 | `@typescript-eslint/no-unsafe-member-access` | medio | no | C |
| 1 | 1 | `sonarjs/cognitive-complexity` | alto | no | E |
| 1 | 1 | `sonarjs/no-small-switch` | bajo | no | A |
| 1 | 1 | `jsx-a11y/html-has-lang` | bajo | no | C |
| 1 | 1 | `react-hooks/incompatible-library` | **crítico** — investigar caso por caso | no | Z |
| 1 | 1 | `@typescript-eslint/no-unsafe-argument` | medio | no | C |
| 1 | 1 | `no-constant-binary-expression` | medio | no | C |
| 1 | 1 | `no-param-reassign` | bajo | no | C |
| 1 | 1 | `sonarjs/no-redundant-assignments` | bajo | no | A |

Top archivos con mayor densidad (candidatos a refactor dedicado, no limpieza):

```
48 src/app/(main)/book/[tenant_slug]/[event_slug]/page.tsx
41 src/features/sales/components/AvailabilityView.tsx
39 src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailCampanasTab.tsx
39 src/features/offer-studio/api/adapter.ts
37 src/features/sales/components/EventTypeForm.tsx
32 src/features/growth-studio/components/metrics-dashboard/detail-panels/ExpansionEvangelizationDetail.tsx
31 src/features/growth-studio/components/metrics-dashboard/stage-widgets/__tests__/StageCard.test.tsx
31 src/features/sales/components/EventTypeView.tsx
30 src/features/growth-studio/components/metrics-dashboard/sidebar/SidebarContent.tsx
30 src/lib/api/connections.ts
27 src/features/connections/components/MetaView.tsx
26 src/components/shared/layout/AppSidebar.tsx
26 src/features/brand-studio/components/legacy-team/TeamMemberForm.tsx
```

## Plan de ejecución — batches

Cinco batches (A–E) + excepciones (Z). Orden propuesto = riesgo ascendente. Cada batch = 1 PR. Entre PRs correr `/test-frontend` + smoke E2E.

### Batch A — mecánico (~820 warnings, 1 día)

Reglas: `jsdoc/require-description`, `no-unused-vars`, `unused-import`, `no-empty-function`, `prefer-destructuring`, `import/order`, `consistent-type-imports`, `prefer-optional-chain`, `no-dead-store`, `no-console`, `no-small-switch`, `no-redundant-assignments`.

Estrategia:
1. Auto-fix pass con `--fix` — recoge import/order, consistent-type, prefer-destructuring, prefer-optional-chain, unused-import trivial.
2. Script Python: para cada export sin JSDoc, insertar `/** {{stub}} */` con descripción mínima derivada del nombre (split camelCase → prose). Humano revisa después, pero vale como baseline.
3. Manual por archivo para `no-unused-vars` que requiera juicio (función overrides, test helpers).
4. `no-console`: borrar `console.log/info/debug` en prod code. Conservar en archivos `e2e/`, `scripts/`, `playground/`.

Acceptance: warnings_A_before − warnings_A_after ≥ 780 (95%).

### Batch B — nullish coalescing (~265 warnings, medio día)

Regla: `@typescript-eslint/prefer-nullish-coalescing`.

Estrategia: manual con confirmación. Regla: solo convertir `a || b` → `a ?? b` cuando `a` sea `string | null | undefined`, `object | null | undefined` o `array | null | undefined`. NO convertir cuando `a` pueda ser `0`, `""` o `false` intencionalmente (ej. toggles `value || 'default'` donde 0 = "sin valor"). Dejar los ambiguos en allowlist con `// eslint-disable-next-line prefer-nullish-coalescing — 0/false semantics` + justificación.

Acceptance: ≥200 convertidos; resto justificados.

### Batch C — type safety + a11y + sonar menores (~330 warnings, 1 día)

Reglas: `no-non-null-assertion` (49), `no-explicit-any` (25), `no-base-to-string` (20), `jsx-a11y/label-has-associated-control` (17), `require-await` (11), `no-redundant-type-constituents` (10), `no-restricted-globals` (8), `no-unsafe-assignment` (8), `no-nested-template-literals` (5), `no-img-element` (4), `only-throw-error` (3), `iframe-has-title` (2), `no-unsafe-member-access` (2), `html-has-lang` (1), `no-unsafe-argument` (1), `no-constant-binary-expression` (1), `no-param-reassign` (1), `sonarjs/no-duplicate-string` (153).

Estrategia por regla:
- `no-non-null-assertion`: cada `!` → optional chain o guard; si es inevitable (discriminated-union narrow), convert a runtime assert con mensaje útil.
- `no-explicit-any`: reemplazar por `unknown` + type guard o tipo concreto. 25 warnings en 2 archivos → targeted refactor.
- `no-base-to-string`: `${obj}` en template string cuando obj no tiene custom toString → convertir a JSON.stringify o acceder a campo concreto.
- `label-has-associated-control`: revisar cada `<Label>` que no apunta a un `<input id=...>` asociado.
- `no-img-element`: swap por `next/image` con width/height declarados.
- `no-duplicate-string`: extraer a constante si la cadena aparece ≥3 veces y es semánticamente la misma (no coincidencia).
- Todas las otras: fix per-caso siguiendo sugerencia del linter.

Acceptance: ≥300 resueltos; allowlist de lo estructuralmente justificable documentada.

### Batch D — react-perf (1053 warnings, **alto riesgo**, 2-3 días)

Reglas: `react-perf/jsx-no-new-function-as-prop` (670), `jsx-no-new-object-as-prop` (239), `jsx-no-new-array-as-prop` (122), `jsx-no-jsx-as-prop` (22).

Estrategia:
1. Antes de tocar nada: profiling real con React DevTools — identificar componentes hot. El warning es un *olor*, no un bug. Muchos casos son irrelevantes (listas cortas, renders puntuales).
2. Para cada componente, decisión:
   - Hot path + muchos hijos → `useCallback` / `useMemo` con deps correctas.
   - Cold path / shallow tree → `// eslint-disable-next-line react-perf/... — trivial render cost`.
   - Estructuralmente raro (nueva key cada render) → refactor estructura.
3. Cambios en deps de `useCallback` son la fuente #1 de bugs. Tests obligatorios antes de cada commit.
4. Splittar en mini-PRs por feature (offer-studio, growth-studio, sales, etc.) — no un PR gigante.

Acceptance: ≥70% resuelto (target ~735), resto justificado con allowlist + comentario técnico. **NO** meter un decorator tipo `// eslint-disable react-perf/*` global.

### Batch E — estructural (~485 warnings, 3-5 días)

Reglas: `max-lines-per-function` (132), `no-nested-conditional` (125), `no-nested-ternary` (110), `max-lines` (43), `complexity` (34), `no-nested-functions` (4), `max-switch-cases` (3), `cognitive-complexity` (1).

Estrategia:
1. Ordenar archivos de peor densidad a mejor (usar top-files del snapshot arriba).
2. Por archivo, aplicar patrones:
   - `max-lines-per-function` → extract sub-functions o componentes JSX. Target función <100 líneas.
   - `max-lines` (archivo) → split por sección lógica (subcomponentes, hooks al hook-file, constants a config-file).
   - `no-nested-ternary / conditional` → early returns, guard clauses, switch, o lookup table.
   - `complexity` → partition por responsabilidad.
3. Cada file-refactor = 1 commit. Tests cubren el comportamiento antes de tocar.

Este batch es prácticamente un mini-refactor por feature. Candidatos a refactor completo (>30 warnings):
- `src/app/(main)/book/[tenant_slug]/[event_slug]/page.tsx` (48)
- `src/features/sales/components/AvailabilityView.tsx` (41) / `EventTypeForm.tsx` (37) / `EventTypeView.tsx` (31)
- `src/features/growth-studio/.../MailCampanasTab.tsx` (39)
- `src/features/offer-studio/api/adapter.ts` (39)

Acceptance: ≥50% resuelto (242), top-10 archivos por densidad todos reducidos a <15 warnings.

### Batch Z — investigación (1 warning, indefinido)

`react-hooks/incompatible-library` (1 warning, 1 archivo) — regla raramente vista. Requiere entender qué librería flagea el hook y si es ignorable o indica bug real. Investigar antes de cerrar.

## Gobernanza

- **Ratchet gate** (propuesta): agregar a `.claude/rules/frontend-quality.md` un tope dinámico `MAX_ESLINT_WARNINGS=2968`. CI falla si el nuevo count > tope. Cada batch baja el tope en su PR. Cero regresión posible.

  Implementación: nuevo test en `src/__tests__/architecture/test-eslint-warning-ratchet.test.ts` que corre `eslint --format json`, cuenta, compara contra constant en el test, y hace `expect(current).toBeLessThanOrEqual(MAX)`. Cada PR del cleanup baja la constante.

- **No mezclar con features**. Cada batch = PR dedicado; nunca agregar warnings al tocar código nuevo.

- **No `// eslint-disable` en bulk**. Si se usa, comentario justificando el caso específico.

## Artefactos a crear durante el cleanup

- `docs/tech-debt/eslint-warnings-history.md` — log de snapshots por fecha + cuenta total, para medir progreso.
- `scripts/count-eslint-warnings.sh` — corre el comando y anexa resultado al history.
- `frontend/src/__tests__/architecture/test-eslint-warning-ratchet.test.ts` — gate CI.

## Checkpoint para retomar

Comandos para re-verificar el estado al volver:

```bash
cd /home/chris/AISALESHT/frontend
rm -f .eslintcache
./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache 2>&1 | tail -1
# Esperado hoy: ✖ 2968 problems (0 errors, 2968 warnings)
# Si ese número cambió: regenerar snapshot arriba antes de planear.
```

Último commit de la sesión que produjo este doc: `157063e6`. Para ver qué se limpió: `git log --oneline 6b2280b7..HEAD`.
