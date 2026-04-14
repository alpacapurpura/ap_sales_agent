# Propuesta de Mejora: Calidad de Código Frontend

**Fecha:** 2026-04-13
**Autor:** Análisis de calidad de código
**Estado:** Propuesta para revisión

---

## Diagnóstico Actual

### Herramientas Existentes

| Herramienta | Configuración | Estado |
|-------------|---------------|--------|
| ESLint | `eslint.config.mjs` (flat config) | ✅ Configurado, pero mínimo |
| TypeScript | `tsconfig.json` | ✅ Strict mode activado |
| Vitest | `vitest.config.mts` | ✅ Configurado con coverage |
| Playwright | `playwright.config.ts` | ✅ E2E tests configurados |
| Husky + lint-staged | En `package.json` | ✅ Configurado |
| Storybook | Con a11y + themes | ✅ Configurado |

### Problemas Detectados

#### 1. ESLint Demasiado Mínimo (CRÍTICO)

El archivo `eslint.config.mjs` actual solo incluye:
```javascript
export default [
  ...nextConfig,                    // eslint-config-next
  ...storybook.configs["flat-recommended"]
]
```

**Comparación con backend:**
- Backend (ruff): **50+ rule sets** activas (E, F, W, I, UP, B, S, C901, PERF, DTZ, SIM, PIE, RET, RSE, C4, FURB, FLY, N, A, ISC, T20, LOG, ERA, PGH, PT, TCH, PL, RUF, ARG, FBT, EM, INP, YTT, ASYNC, FA, ICN, Q, SLOT, TID, INT, T10, EXE, E501, FAST, ANN, D, NPY, PYI, PTH, TD, FIX, G, TRY, BLE)
- Frontend (ESLint): **Solo las reglas básicas de Next.js** + Storybook recomendado

**Falta:**
- Reglas de complejidad ciclomática
- Reglas de tamaño de archivos/funciones
- Reglas de importaciones ordenadas
- Reglas de seguridad (no console.log, no debugger, etc.)
- Reglas de rendimiento React
- Reglas de accesibilidad (a11y) estrictas
- Reglas de TypeScript estrictas
- Reglas de FSD (Feature-Sliced Design)
- Detección de bugs potenciales y code smells
- Formato consistente (Prettier no está integrado)

#### 2. Violaciones Masivas de FSD (194 imports profundos)

Las reglas de FSD dicen:
> "No deep feature imports (except copilot)"

Pero el escaneo encontró **194 imports profundos** dentro de `offer-studio/` y `growth-studio/`:

```typescript
// offer-studio/components/editor/sections/identity/identity-form.tsx
import { OfferSchema, OfferFormValues } from "../../../../types/schema";
import { OfferArchetype } from "../../../../types";

// growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailCrecimientoTab.tsx
import { useMailGrowth } from '../../../../../hooks/useMailDashboard';
import { formatMetricValue } from '../../../../../utils/format-metric-value';
```

Estos imports de `../../../../` y `../../../../../` violan:
- La regla de "no deep feature imports"
- El principio de encapsulamiento de features
- La mantenibilidad del código

#### 3. Coverage Thresholds Muy Bajos

```typescript
// vitest.config.mts
thresholds: {
  statements: 8,   // 8% — debería ser > 70%
  branches: 5,     // 5% — debería ser > 60%
  functions: 5,    // 5% — debería ser > 70%
  lines: 8,        // 8% — debería ser > 70%
}
```

#### 4. Sin Prettier Configurado

- No hay `prettier.config.js` ni `.prettierrc`
- No hay integración de Prettier en ESLint
- El formato depende del editor de cada desarrollador

#### 5. Sin Reglas de Arquitectura

No hay herramientas que prevengan:
- Imports circulares
- Imports entre features no autorizados
- Archivos demasiado grandes (> 300 líneas)
- Funciones demasiado complejas (> 10 condiciones)
- Components con demasiadas props (> 5)

---

## Propuesta de Mejoras (Fases)

### Fase 1: ESLint Estricto (Prioridad Alta)

**Objetivo:** Equiparar la rigurosidad del ESLint frontend con la del ruff backend.

#### Plugins a Instalar

```bash
npm install --save-dev \
  @typescript-eslint/eslint-plugin \
  eslint-plugin-sonarjs \
  eslint-plugin-react-hooks \
  eslint-plugin-jsx-a11y \
  eslint-plugin-testing-library \
  eslint-plugin-jest-dom \
  eslint-plugin-import \
  eslint-plugin-boundaries \
  eslint-plugin-react-perf \
  prettier \
  eslint-config-prettier \
  eslint-plugin-prettier
```

#### Nueva Configuración `eslint.config.mjs`

```typescript
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import nextConfig from "eslint-config-next";
import storybook from "eslint-plugin-storybook";
import sonarjs from "eslint-plugin-sonarjs";
import importPlugin from "eslint-plugin-import";
import boundaries from "eslint-plugin-boundaries";
import reactHooks from "eslint-plugin-react-hooks";
import jsxA11y from "eslint-plugin-jsx-a11y";
import reactPerf from "eslint-plugin-react-perf";
import prettier from "eslint-plugin-prettier/recommended";
import globals from "globals";

/** @type {import("eslint").Linter.Config[]} */
export default [
  // Base JS recommendations
  js.configs.recommended,

  // TypeScript
  ...tseslint.configs.recommendedTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        project: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },

  // Next.js
  ...nextConfig,

  // Storybook
  ...storybook.configs["flat-recommended"],

  // SonarJS (detección de bugs y code smells)
  {
    plugins: { sonarjs },
    rules: {
      "sonarjs/cognitive-complexity": ["error", 15],
      "sonarjs/no-duplicate-string": "warn",
      "sonarjs/no-identical-functions": "warn",
      "sonarjs/no-nested-template-literals": "warn",
      "sonarjs/prefer-single-boolean-return": "error",
      "sonarjs/max-switch-cases": ["warn", 8],
    },
  },

  // React Hooks
  {
    plugins: { "react-hooks": reactHooks },
    rules: {
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "error",
    },
  },

  // Accesibilidad estricta
  {
    plugins: { "jsx-a11y": jsxA11y },
    rules: {
      "jsx-a11y/alt-text": "error",
      "jsx-a11y/aria-props": "error",
      "jsx-a11y/aria-role": ["error", { ignoreNonDom: false }],
      "jsx-a11y/aria-unsupported-elements": "error",
      "jsx-a11y/heading-has-content": "warn",
      "jsx-a11y/html-has-lang": "warn",
      "jsx-a11y/iframe-has-title": "error",
      "jsx-a11y/img-redundant-alt": "warn",
      "jsx-a11y/no-access-key": "error",
      "jsx-a11y/no-distracting-elements": "error",
      "jsx-a11y/role-has-required-aria-props": "error",
      "jsx-a11y/role-supports-aria-props": "error",
      "jsx-a11y/scope": "warn",
      "jsx-a11y/tabindex-no-positive": "warn",
      "jsx-a11y/label-has-associated-control": "error",
    },
  },

  // Importaciones ordenadas y controladas
  {
    plugins: { import: importPlugin },
    rules: {
      "import/order": [
        "warn",
        {
          groups: [
            "builtin",
            "external",
            "internal",
            "parent",
            "sibling",
            "index",
            "object",
            "type",
          ],
          "newlines-between": "always",
          alphabetize: { order: "asc", caseInsensitive: true },
        },
      ],
      "import/no-duplicates": "error",
      "import/no-unresolved": "error",
      "import/no-self-import": "error",
      "import/no-cycle": ["error", { maxDepth: 3 }],
    },
  },

  // FSD Boundaries (previene imports entre features)
  {
    plugins: { boundaries },
    rules: {
      "boundaries/no-unknown": "error",
      "boundaries/element-types": [
        "error",
        {
          default: "disallow",
          rules: [
            // app/ puede importar de features/ y components/
            {
              from: "app",
              allow: ["feature", "component", "shared"],
            },
            // features/ SOLO puede importar de su propio feature, components/shared y lib/
            {
              from: "feature",
              allow: ["feature:own", "component:shared", "lib", "util"],
            },
            // components/shared puede importar de lib/
            {
              from: "component:shared",
              allow: ["lib", "util"],
            },
            // lib/ no importa de features
            {
              from: "lib",
              allow: ["util"],
            },
            // Copilot excepción (infra-like)
            {
              from: "feature",
              target: ["feature:copilot"],
              allow: ["feature"],
            },
          ],
        },
      ],
    },
    settings: {
      "boundaries/elements": [
        { type: "app", pattern: "src/app/*" },
        { type: "feature", pattern: "src/features/*" },
        { type: "feature:own", pattern: "src/features/*/ *" },
        { type: "feature:copilot", pattern: "src/features/copilot/*" },
        { type: "component:shared", pattern: "src/components/shared/*" },
        { type: "component:ui", pattern: "src/components/ui/*" },
        { type: "lib", pattern: "src/lib/*" },
        { type: "util", pattern: "src/lib/utils/*" },
      ],
    },
  },

  // React Performance
  {
    plugins: { "react-perf": reactPerf },
    rules: {
      "react-perf/jsx-no-new-object-as-prop": "warn",
      "react-perf/jsx-no-new-array-as-prop": "warn",
      "react-perf/jsx-no-new-function-as-prop": "warn",
      "react-perf/jsx-no-jsx-as-prop": "warn",
    },
  },

  // TypeScript estricto
  {
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/consistent-type-imports": [
        "warn",
        { prefer: "type-imports" },
      ],
      "@typescript-eslint/no-misused-promises": "error",
      "@typescript-eslint/require-await": "warn",
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/prefer-nullish-coalescing": "warn",
      "@typescript-eslint/no-non-null-assertion": "warn",
      "@typescript-eslint/explicit-function-return-type": [
        "warn",
        { allowExpressions: true },
      ],
      "@typescript-eslint/consistent-type-definitions": ["error", "interface"],
      "@typescript-eslint/no-var-requires": "error",
    },
  },

  // Reglas generales de calidad
  {
    rules: {
      // Prohibido console.log en producción
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-debugger": "error",
      "no-alert": "error",

      // Preferir const sobre let
      "prefer-const": "error",

      // No usar var
      "no-var": "error",

      // Preferir template literals
      "prefer-template": "warn",

      // Preferir arrow functions
      "prefer-arrow-callback": "warn",

      // No reasignar parámetros
      "no-param-reassign": "warn",

      // Max líneas por archivo (progressivo)
      "max-lines": ["warn", { max: 350, skipBlankLines: true, skipComments: true }],
      "max-lines-per-function": ["warn", { max: 75, skipBlankLines: true, skipComments: true }],

      // Max anidación
      "max-depth": ["error", 4],

      // Max params en funciones
      "max-params": ["error", 4],

      // Preferir early returns
      "max-statements-per-line": ["warn", { max: 1 }],
    },
  },

  // Integración Prettier
  prettier,

  // Ignorar archivos generados
  {
    ignores: [
      ".next/",
      "node_modules/",
      "storybook-static/",
      "src/components/ui/",  // shadcn auto-generated
    ],
  },
];
```

#### Reglas por Fase de Adopción

**Fase 1A (activar inmediatamente):**
```typescript
// Estas reglas NO romperán el build actual
"no-console": "warn",
"no-debugger": "error",
"import/no-duplicates": "error",
"import/no-self-import": "error",
"@typescript-eslint/no-unused-vars": "warn",
"prefer-const": "warn",
"no-var": "error",
"@typescript-eslint/consistent-type-imports": "warn",
"import/order": "warn",
```

**Fase 1B (progresivo — 2 semanas):**
```typescript
// Estas reglas requerirán fixes pero mejorará la calidad
"@typescript-eslint/no-explicit-any": "warn",  // luego "error"
"@typescript-eslint/no-misused-promises": "warn",
"@typescript-eslint/no-floating-promises": "warn",
"react-hooks/exhaustive-deps": "warn",
"sonarjs/cognitive-complexity": ["warn", 20],  // luego ["error", 15]
"max-lines": ["warn", 500],  // luego ["warn", 350]
"max-depth": ["warn", 5],  // luego ["error", 4]
"jsx-a11y/alt-text": "warn",  // luego "error"
```

**Fase 1C (estricto — 1 mes):**
```typescript
// Estas reglas son el objetivo final
"@typescript-eslint/no-explicit-any": "error",
"sonarjs/cognitive-complexity": ["error", 15],
"max-lines": ["error", 350],
"max-lines-per-function": ["error", 75],
"boundaries/element-types": "error",  // FSD enforcement
"@typescript-eslint/explicit-function-return-type": "warn",
```

---

### Fase 2: Prettier para Formato Consistente

**Objetivo:** Eliminar debates de estilo y garantizar formato consistente.

#### Crear `prettier.config.mjs`

```typescript
/** @type {import("prettier").Config} */
export default {
  semi: true,
  singleQuote: false,
  trailingComma: "all",
  printWidth: 100,
  tabWidth: 2,
  useTabs: false,
  endOfLine: "lf",
  bracketSpacing: true,
  bracketSameLine: false,
  arrowParens: "always",
  jsxSingleQuote: false,
  quoteProps: "as-needed",
  importOrder: [
    "^react$",
    "^next.*$",
    "<THIRD_PARTY_MODULES>",
    "^@/(.*)$",
    "^[./]",
  ],
  importOrderParserPlugins: ["typescript", "jsx", "decorators-legacy"],
  importOrderTypeScriptVersion: "5.0.0",
  plugins: [
    "@trivago/prettier-plugin-sort-imports",
    "prettier-plugin-tailwindcss",  // ordena clases de Tailwind
  ],
};
```

#### Actualizar `lint-staged` en `package.json`

```json
{
  "lint-staged": {
    "*.{ts,tsx}": [
      "prettier --write",
      "eslint --fix",
      "bash -c 'tsc --noEmit'"
    ],
    "*.{js,jsx,mjs}": [
      "prettier --write",
      "eslint --fix"
    ],
    "*.css": ["prettier --write"],
    "*.json": ["prettier --write"]
  }
}
```

---

### Fase 3: FSD Enforcement con `eslint-plugin-boundaries`

**Objetivo:** Prevenir los 194 imports profundos detectados.

#### Estructura de Boundaries

```typescript
// eslint.config.mjs — settings
{
  settings: {
    "boundaries/elements": [
      {
        type: "app",
        pattern: "src/app/*",
        mode: "full",
        capture: ["name"],
      },
      {
        type: "feature",
        pattern: "src/features/*",
        mode: "full",
        capture: ["name"],
      },
      {
        type: "component:shared",
        pattern: "src/components/shared/*",
        mode: "full",
        capture: ["name"],
      },
      {
        type: "component:ui",
        pattern: "src/components/ui/*",
        mode: "full",
        capture: ["name"],
      },
      {
        type: "lib",
        pattern: "src/lib/*",
        mode: "full",
        capture: ["name"],
      },
    ],
  },
}
```

#### Matriz de Permisos

| Desde \ Hacia | app/ | features/ | components/shared | components/ui | lib/ |
|---------------|------|-----------|-------------------|---------------|------|
| **app/** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **features/** (mismo) | ❌ | ✅ (solo own) | ✅ | ✅ | ✅ |
| **features/** (otro) | ❌ | ❌ (except copilot) | ✅ | ✅ | ✅ |
| **components/shared** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **components/ui** | ❌ | ❌ | ❌ | ✅ (solo own) | ✅ |
| **lib/** | ❌ | ❌ | ❌ | ❌ | ✅ |

**Excepción:** `copilot` puede ser importado por cualquier feature (es infra-like).

#### Migración de Imports Profundos

Los 194 imports detectados deben migrarse:

**Opción A: Mover tipos/utils a shared**
```typescript
// ANTES (violación FSD)
// features/offer-studio/components/editor/sections/identity/identity-form.tsx
import { OfferSchema, OfferFormValues } from "../../../../types/schema";

// DESPUÉS (correcto)
// 1. Mover types a lib/ o components/shared/
// lib/types/offer-schema.ts (o features/offer-studio/types/index.ts exportado)
import { OfferSchema, OfferFormValues } from "@/lib/types/offer-schema";
// O
import { OfferSchema, OfferFormValues } from "@/features/offer-studio/types";
```

**Opción B: Barrel exports en feature root**
```typescript
// features/offer-studio/index.ts (barrel export)
export { OfferSchema, OfferFormValues } from "./types/schema";
export { OfferArchetype, ServiceCategory } from "./types";

// Uso correcto (importación desde feature root)
import { OfferSchema, OfferArchetype } from "@/features/offer-studio";
```

**Opción C: Shared types para features múltiples**
```typescript
// Si múltiples features necesitan los mismos types → mover a lib/
// lib/types/metrics.ts (usado por growth-studio y analytics)
// lib/utils/format-metric-value.ts (usado por growth-studio y analytics)
```

---

### Fase 4: Mejorar Coverage Thresholds

**Objetivo:** Subir thresholds gradualmente de 8% a 70%.

#### `vitest.config.mts` — Milestones

```typescript
coverage: {
  thresholds: {
    // Milestone 1 (inmediato): 20%
    statements: 20,
    branches: 15,
    functions: 20,
    lines: 20,
  },
}

// Milestone 2 (1 mes): 40%
// Milestone 3 (2 meses): 60%
// Milestone 4 (3 meses): 70%
```

**Estrategia:**
- Nuevos hooks/components: 100% coverage requerido
- Features existentes: cubrir tests críticos primero
- No reducir thresholds existentes (solo aumentar)

---

### Fase 5: Herramientas Adicionales (Opcional)

#### 5.1. `eslint-plugin-react-compiler` (React 19)

Para aprovechar React Compiler y optimizar renders automáticamente:

```bash
npm install --save-dev eslint-plugin-react-compiler
```

```typescript
{
  plugins: { "react-compiler": reactCompiler },
  rules: {
    "react-compiler/react-compiler": "error",
  },
}
```

#### 5.2. `knip` — Detectar código muerto

```bash
npm install --save-dev knip
```

Detecta:
- Imports no usados
- Archivos no referenciados
- Dependencias no usadas en `package.json`

```bash
npx knip  # ejecutar en CI
```

#### 5.3. `madge` — Detectar imports circulares

```bash
npm install --save-dev madge
```

```bash
npx madge --circular src/  # detectar circular imports
npx madge --graph src/ > graph.svg  # visualizar dependencias
```

#### 5.4. `typescript-coverage-report` — Reportes visuales

```bash
npm install --save-dev typescript-coverage-report
```

Genera HTML report de coverage de types.

---

## Plan de Implementación

### Semana 1: Setup Inicial
- [ ] Instalar todos los plugins de ESLint
- [ ] Configurar ESLint con reglas de Fase 1A (non-breaking)
- [ ] Configurar Prettier
- [ ] Integrar Prettier + ESLint en lint-staged
- [ ] Ejecutar `npx eslint src/ --fix` para auto-fix inicial
- [ ] Documentar violaciones restantes para migración

### Semana 2: Migración de Imports (FSD)
- [ ] Configurar `eslint-plugin-boundaries` en modo warn
- [ ] Identificar todos los imports profundos (ya encontrados: 194)
- [ ] Crear barrel exports en features
- [ ] Mover tipos compartidos a `lib/types/`
- [ ] Mover utils compartidos a `lib/utils/`
- [ ] Activar modo error para boundaries

### Semana 3: Reglas Estrictas
- [ ] Activar Fase 1B (reglas en modo warn → error)
- [ ] Fix manual de violaciones no auto-fixables
- [ ] Activar SonarJS cognitive complexity
- [ ] Activar reglas de a11y como errores
- [ ] Activar reglas de TypeScript estrictas

### Semana 4: Coverage y CI
- [ ] Subir coverage thresholds a 20%
- [ ] Agregar `knip` a CI
- [ ] Agregar `madge --circular` a CI
- [ ] Documentar reglas en `QWEN.md`
- [ ] Crear regla `.claude/rules/frontend-quality.md`

---

## Regla para Agentes (`.claude/rules/frontend-quality.md`)

```markdown
# Frontend Quality

## ESLint
- Todo código nuevo DEBE pasar `npx eslint src/` sin errores
- No usar `any` — usar `unknown` + type guards o tipos específicos
- No usar `console.log` — usar logger o `console.warn/error`
- No usar `var` — usar `const` o `let`
- Imports ordenados: externos → internos → relativos → tipos
- No duplicar imports

## FSD (Feature-Sliced Design)
- `app/` es thin — delega a `features/`
- `features/` NO importa de otros features (excepto copilot)
- Tipos compartidos → `lib/types/`
- Utils compartidos → `lib/utils/`
- Componentes compartidos → `components/shared/`
- NO imports profundos (`../../../../`) — máximo 2 niveles (`../`)

## TypeScript
- `strict: true` en tsconfig
- Preferir `interface` sobre `type` para objetos
- Preferir `as const` sobre type assertions
- No usar `non-null assertion` (!) — usar optional chaining o type guards
- Explicit return types en funciones públicas

## Testing
- Todo hook nuevo → test correspondiente
- Todo componente con lógica → test
- Coverage mínimo: 20% (subiendo gradualmente)
- Tests colocados como `*.test.ts` junto al source o en `__tests__/`

## Performance React
- No crear objetos/arrays/funciones inline como props
- Usar `useMemo` y `useCallback` para props costosos
- Server Components por default, `"use client"` solo cuando necesario

## Accesibilidad
- Todo `<img>` debe tener `alt`
- Todo formulario debe tener `<label>`
- No usar `tabIndex` positivo
- Roles ARIA deben ser válidos y tener props requeridas

## Formato
- Prettier para formato — no debatir estilos
- Max 350 líneas por archivo
- Max 75 líneas por función
- Max 4 niveles de anidación
- Max 4 parámetros por función
```

---

## Métricas de Éxito

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Reglas ESLint activas | ~10 | ~60+ |
| Imports profundos (4+ niveles) | 194 | 0 |
| Imports circulares | desconocido | 0 |
| Coverage statements | 8% | 70% |
| Archivos > 350 líneas | desconocido | < 5% |
| Funciones con complejidad > 15 | desconocido | 0 |
| Violaciones de a11y | desconocido | 0 |
| Tiempo de lint (seg) | desconocido | < 30 |

---

## Recursos

- [ESLint Flat Config Docs](https://eslint.org/docs/latest/use/configure/configuration-files)
- [eslint-plugin-sonarjs](https://github.com/SonarSource/eslint-plugin-sonarjs)
- [eslint-plugin-boundaries](https://github.com/nickngraham/eslint-plugin-boundaries)
- [eslint-plugin-import](https://github.com/import-js/eslint-plugin-import)
- [eslint-plugin-react-perf](https://github.com/cvazak/eslint-plugin-react-perf)
- [Prettier](https://prettier.io/)
- [knip](https://knip.dev/)
- [madge](https://github.com/pahen/madge)
- [Feature-Sliced Design](https://feature-sliced.design/)

---

## Notas

- Esta propuesta es **progresiva** — no se activan todas las reglas de golpe
- Cada fase debe pasar lint + tests antes de avanzar a la siguiente
- Las reglas en modo `warn` no bloquean el build pero son visibles
- Las reglas en modo `error` bloquean el build y CI
- Se puede usar `// eslint-disable-next-line rule-name` para excepciones justificadas (con comentario)
