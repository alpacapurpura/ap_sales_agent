# Frontend Quality

## ESLint

Todo código nuevo DEBE pasar `npx eslint src/` sin errores.

### Reglas activas (Phase 1A — warn mode)

El ESLint frontend tiene **60+ reglas** configuradas en `frontend/eslint.config.mjs`, equiparando las 50+ reglas del ruff backend.

- **SonarJS**: Detección de bugs, code smells, complejidad cognitiva (máx 20)
- **Import ordering**: Imports ordenados por grupo, alfabéticamente, con líneas entre grupos
- **FSD Boundaries**: Prevención de imports cruzados entre features (eslint-plugin-boundaries v6)
- **A11y**: Reglas estrictas de accesibilidad
- **React Performance**: No crear objetos/arrays/funciones inline como props
- **TypeScript strict**: No-explicit-any, consistent-type-imports, no-floating-promises, etc.
- **Complejidad**: Max líneas (500), max función (100), max anidación (5), max params (5)

### Reglas prohibidas (error — bloquean build)

| Regla | Qué previene |
|-------|-------------|
| `no-debugger` | Dejar `debugger;` en producción |
| `no-eval` | Uso de `eval()` |
| `no-implied-eval` | `setTimeout(string)` que equivale a eval |
| `no-var` | Uso de `var` (usar `const`/`let`) |
| `@typescript-eslint/no-var-requires` | `require()` (usar `import`) |
| `@typescript-eslint/no-require-imports` | Imports estilo CommonJS |
| `react-hooks/rules-of-hooks` | Hooks fuera de top-level component |

### Reglas en warn (visibles, no bloquean — subirán a error en Phase 1B/1C)

- `no-console` — permitir solo `console.warn` y `console.error`
- `no-alert` — no usar `alert()`, `confirm()`, `prompt()`
- `@typescript-eslint/no-explicit-any` — evitar `any`
- `@typescript-eslint/no-floating-promises` — promises sin await
- `@typescript-eslint/no-misused-promises` — promises donde se esperan valores sync
- `@typescript-eslint/no-unsafe-*` — unsafe assignment/return/argument/member/call
- `sonarjs/cognitive-complexity` — máx 20 (bajará a 15 en Phase 1C)
- `max-lines` — máx 500 líneas por archivo (bajará a 350)
- `max-lines-per-function` — máx 100 (bajará a 75)
- `max-depth` — máx 5 niveles de anidación (bajará a 4)
- `import/no-duplicates` — no duplicar imports
- `boundaries/dependencies` — FSD enforcement (feature → feature no permitido)

## FSD (Feature-Sliced Design)

Estructura de boundaries configurada con `eslint-plugin-boundaries` v6:

| Desde \ Hacia | app/ | features/ | components/shared | components/ui | lib/ |
|---------------|------|-----------|-------------------|---------------|------|
| **app/** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **features/** (mismo) | ❌ | ✅ (solo own) | ✅ | ✅ | ✅ |
| **features/** (otro) | ❌ | ❌ | ✅ | ✅ | ✅ |
| **components/shared** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **lib/** | ❌ | ❌ | ❌ | ✅ | ✅ |

**Reglas de importación:**
- `app/` es thin — delega a `features/`
- `features/` NO importa de otros features
- Tipos compartidos → `lib/types/`
- Utils compartidos → `lib/utils/`
- Componentes compartidos → `components/shared/`
- NO imports profundos (`../../../../`) — máximo 2 niveles (`../`)
- Usar barrel exports en feature root: `features/{name}/index.ts`

## TypeScript

- `strict: true` en tsconfig
- Preferir `interface` sobre `type` para objetos
- Preferir `type imports` para tipos: `import type { Foo } from '...'`
- No usar `non-null assertion` (!) — preferir optional chaining o type guards
- `Array<T>` → `T[]` (estilo consistente)
- Dot notation preferida sobre bracket notation: `obj.key` no `obj["key"]`
- Optional chaining preferido sobre encadenamiento de null checks

## Testing

- Todo hook nuevo → test correspondiente
- Todo componente con lógica → test
- Coverage mínimo actual: 8% (subiendo gradualmente — Phase 4)
- Tests colocados como `*.test.ts` junto al source o en `__tests__/`
- Vitest con happy-dom environment

## Performance React

- No crear objetos/arrays/funciones inline como props (react-perf)
- Usar `useMemo` y `useCallback` para props costosos
- Server Components por default, `"use client"` solo cuando necesario

## Accesibilidad

- Todo `<img>` debe tener `alt`
- Todo formulario debe tener `<label>`
- No usar `tabIndex` positivo
- Roles ARIA deben ser válidos y tener props requeridas
- `<html>` debe tener `lang`
- `<iframe>` debe tener `title`
- Media debe tener captions

## Formato (Prettier)

- Prettier configurado en `prettier.config.mjs`
- `endOfLine: "lf"` — Unix line endings
- `printWidth: 100`
- `trailingComma: "all"`
- `singleQuote: false` (double quotes por default)
- `semi: true`

## Complejidad

| Métrica | Límite | Estado |
|---------|--------|--------|
| Max líneas por archivo | 500 | warn (Phase 1C: 350) |
| Max líneas por función | 100 | warn (Phase 1C: 75) |
| Max anidación | 5 | warn (Phase 1C: 4) |
| Max params | 5 | warn (Phase 1C: 4) |
| Max nested callbacks | 4 | warn |
| Complejidad ciclomática | 20 | warn (Phase 1C: 15) |
| SonarJS cognitive complexity | 20 | warn (Phase 1C: 15) |
| Max switch cases | 10 | warn |

## Comandos de Verificación

```bash
# ESLint (lint + fix)
cd frontend && npx eslint src/                    # Check all
cd frontend && npx eslint src/ --fix              # Auto-fix

# TypeScript
cd frontend && npx tsc --noEmit                   # Type check

# Tests
cd frontend && npx vitest run                     # Run tests
cd frontend && npx vitest run --coverage          # With coverage

# Pre-commit simulation
cd frontend && npx lint-staged                    # Run lint-staged
```

## Notas para Agentes

- NO desactivar reglas de ESLint sin justificación en comentario
- `// eslint-disable-next-line` solo con comentario explicativo
- Si un archivo tiene muchas violaciones → refactorizar, no desactivar
- Para excepciones legítimas → documentar en comentario
- NO añadir imports de `react` si no se usa JSX directamente
- Los imports deben estar ordenados: externos → internos → relativos → tipos
