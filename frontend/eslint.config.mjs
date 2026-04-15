// For more info, see https://github.com/storybookjs/eslint-plugin-storybook#configuration-flat-config-format
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import nextConfig from "eslint-config-next";
import storybook from "eslint-plugin-storybook";
import sonarjs from "eslint-plugin-sonarjs";
import importPlugin from "eslint-plugin-import";
import boundaries from "eslint-plugin-boundaries";
import reactPerf from "eslint-plugin-react-perf";
import prettier from "eslint-plugin-prettier/recommended";
import checkFile from "eslint-plugin-check-file";
import jsdoc from "eslint-plugin-jsdoc";
import globals from "globals";

/** @type {import("eslint").Linter.Config[]} */
export default [
  // Base JS recommendations
  js.configs.recommended,

  // TypeScript (recommended + stylistic)
  ...tseslint.configs.recommendedTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        project: true,
        tsconfigRootDir: import.meta.dirname,
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
  },

  // Next.js
  ...nextConfig,

  // Storybook
  ...storybook.configs["flat/recommended"],

  // ─── SonarJS (bug & code smell detection) ───
  {
    plugins: { sonarjs },
    rules: {
      // Phase 1C: error + lowered threshold (15)
      "sonarjs/cognitive-complexity": ["error", 15],
      "sonarjs/no-duplicate-string": "warn",
      "sonarjs/no-identical-functions": "warn",
      "sonarjs/no-nested-template-literals": "warn",
      "sonarjs/prefer-single-boolean-return": "warn",
      "sonarjs/max-switch-cases": ["warn", 10],
      "sonarjs/no-small-switch": "warn",
      "sonarjs/no-collection-size-mischeck": "warn",
      "sonarjs/no-redundant-jump": "warn",
      "sonarjs/unused-import": "warn",
      "sonarjs/no-unused-collection": "warn",
      "sonarjs/no-redundant-assignments": "warn",
      "sonarjs/no-dead-store": "warn",
      "sonarjs/no-gratuitous-expressions": "warn",
      "sonarjs/no-identical-conditions": "warn",
      "sonarjs/no-collapsible-if": "warn",
      "sonarjs/no-nested-switch": "warn",
      "sonarjs/no-nested-functions": "warn",
      "sonarjs/no-nested-conditional": "warn",
    },
  },

  // ─── Import ordering & control ───
  {
    plugins: { import: importPlugin },
    rules: {
      // Phase 1A: warn; Phase 1C: error
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
      "import/no-duplicates": "warn", // Phase 1B: error after fixing
      "import/no-unresolved": "error",
      "import/no-self-import": "error",
      "import/no-cycle": ["warn", { maxDepth: 3 }],
      "import/no-named-as-default": "warn",
      "import/no-named-as-default-member": "warn",
    },
  },

  // ─── FSD Boundaries (prevent cross-feature imports) ───
  {
    plugins: { boundaries },
    rules: {
      // Phase 3: disabled — fires on every @/ import targeting ignored files (components/ui/**)
      // because ESLint ignores prevent those files from being registered as known elements.
      // boundaries/dependencies (below) provides the real FSD enforcement.
      "boundaries/no-unknown": "off",
      // Phase 3: error — 4 violations existed, all fixed.
      "boundaries/dependencies": [
        "error",
        {
          default: "disallow",
          rules: [
            // app/ pages can import from anywhere (Next.js pages are thin orchestrators)
            {
              from: { type: "app" },
              allow: { to: { type: ["feature", "feature:own", "shared", "lib", "ui", "hooks", "providers"] } },
            },
            // features can import from: own feature subdirs, shared components, lib
            {
              from: { type: "feature" },
              allow: { to: { type: ["feature:own", "shared", "lib", "util"] } },
            },
            // feature:own subdirs — same permissions as feature root
            // NOTE: cross-feature subdirectory imports are caught via feature → feature rule.
            {
              from: { type: "feature:own" },
              allow: { to: { type: ["feature:own", "feature", "shared", "lib", "util", "ui"] } },
            },
            // components/shared layout can import from other shared AND feature hooks
            // (sidebar, tenant-switcher need settings hooks — pragmatic FSD-lite allowance)
            {
              from: { type: "shared" },
              allow: { to: { type: ["shared", "lib", "util", "ui", "feature", "feature:own"] } },
            },
            // lib imports from util only (never from features)
            {
              from: { type: "lib" },
              allow: { to: { type: ["util"] } },
            },
          ],
        },
      ],
    },
    settings: {
      "boundaries/elements": [
        { type: "app", pattern: "src/app/*" },
        { type: "feature", pattern: "src/features/*" },
        { type: "feature:own", pattern: "src/features/*/**", mode: "full" },
        { type: "shared", pattern: "src/components/shared/*" },
        { type: "ui", pattern: "src/components/ui/*" },
        { type: "lib", pattern: "src/lib/*" },
        { type: "util", pattern: "src/lib/utils/*" },
        { type: "hooks", pattern: "src/hooks/*" },
        { type: "providers", pattern: "src/components/providers/*" },
      ],
    },
  },

  // ─── Accessibility (a11y) strict ───
  // Note: jsx-a11y is already included by eslint-config-next
  // We just override severity levels here (no need to re-register plugin)
  {
    rules: {
      // Phase 1A: warn; Phase 1C: error
      "jsx-a11y/alt-text": "warn",
      "jsx-a11y/aria-props": "error",
      "jsx-a11y/aria-role": ["warn", { ignoreNonDom: false }],
      "jsx-a11y/aria-unsupported-elements": "error",
      "jsx-a11y/heading-has-content": "warn",
      "jsx-a11y/html-has-lang": "warn",
      "jsx-a11y/iframe-has-title": "warn",
      "jsx-a11y/img-redundant-alt": "warn",
      "jsx-a11y/no-access-key": "error",
      "jsx-a11y/no-distracting-elements": "warn",
      "jsx-a11y/role-has-required-aria-props": "warn",
      "jsx-a11y/role-supports-aria-props": "warn",
      "jsx-a11y/scope": "warn",
      "jsx-a11y/tabindex-no-positive": "warn",
      "jsx-a11y/label-has-associated-control": "warn",
      "jsx-a11y/media-has-caption": "warn",
      "jsx-a11y/mouse-events-have-key-events": "warn",
    },
  },

  // ─── React Performance ───
  {
    plugins: { "react-perf": reactPerf },
    rules: {
      // Phase 1A: warn
      "react-perf/jsx-no-new-object-as-prop": "warn",
      "react-perf/jsx-no-new-array-as-prop": "warn",
      "react-perf/jsx-no-new-function-as-prop": "warn",
      "react-perf/jsx-no-jsx-as-prop": "warn",
    },
  },

  // ─── TypeScript strict ───
  {
    rules: {
      // Phase 1B: error for strict type safety
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/consistent-type-imports": [
        "warn",
        { prefer: "type-imports" },
      ],
      "@typescript-eslint/no-misused-promises": [
        "error",
        {
          checksVoidReturn: {
            attributes: false, // JSX event handlers (onClick, onSubmit) — standard React async pattern
            arguments: false, // setInterval, setTimeout, Array.forEach callbacks
          },
        },
      ],
      "@typescript-eslint/require-await": "warn",
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/prefer-nullish-coalescing": "warn",
      "@typescript-eslint/no-non-null-assertion": "warn",
      // Phase 1A: warn for unsafe any usage; Phase 1B: consider stricter rules
      "@typescript-eslint/no-unsafe-assignment": "warn",
      "@typescript-eslint/no-unsafe-return": "warn",
      "@typescript-eslint/no-unsafe-argument": "warn",
      "@typescript-eslint/no-unsafe-member-access": "warn",
      "@typescript-eslint/no-unsafe-call": "warn",
      "@typescript-eslint/prefer-optional-chain": "warn",
      "@typescript-eslint/explicit-function-return-type": [
        "off", // Phase 1C: consider enabling as warn
      ],
      "@typescript-eslint/consistent-type-definitions": ["warn", "interface"],
      "@typescript-eslint/no-var-requires": "error",
      "@typescript-eslint/no-require-imports": "error",
      "@typescript-eslint/prefer-as-const": "warn",
      "@typescript-eslint/no-empty-interface": "warn",
      "@typescript-eslint/no-inferrable-types": "warn",
      "@typescript-eslint/ban-ts-comment": "warn",
      "@typescript-eslint/no-empty-function": "warn",
      // Phase 1A: warn for style rules; Phase 1B: consider stricter
      "@typescript-eslint/array-type": "warn",
      "@typescript-eslint/no-unnecessary-type-assertion": "warn",
      "@typescript-eslint/no-redundant-type-constituents": "warn",
      "@typescript-eslint/non-nullable-type-assertion-style": "warn",
      "@typescript-eslint/dot-notation": "warn",
      "@typescript-eslint/prefer-regexp-exec": "warn",
      "@typescript-eslint/no-base-to-string": "warn",
      "@typescript-eslint/no-unsafe-enum-comparison": "warn",
      "@typescript-eslint/consistent-generic-constructors": "warn",
      "@typescript-eslint/only-throw-error": "warn",
      "@typescript-eslint/no-empty-object-type": "warn",
    },
  },

  // ─── General quality rules ───
  {
    rules: {
      // Style preferences
      "prefer-const": "error", // Phase 1B: error
      "no-var": "error",
      "prefer-template": "warn",
      "prefer-arrow-callback": "warn",
      "no-param-reassign": "warn",
      "prefer-object-spread": "warn",
      "prefer-destructuring": "warn",
      "no-nested-ternary": "warn",
      "no-unneeded-ternary": "warn",
      // Production safety
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-debugger": "error",
      "no-alert": "error", // Phase 1B: error
      "no-eval": "error",
      "no-implied-eval": "error",
      "no-empty": "error", // Phase 1B: error
      "no-constant-binary-expression": "warn",
      "no-case-declarations": "warn",
      "no-useless-escape": "warn",

      // Complexity limits
      // Phase 1D: max-lines lowered to 350. max-lines-per-function stays at 100
      // (75 target deferred — 328 violations, needs systematic per-file refactor).
      // Remaining large files tracked in frontend-quality-tracker.md Phase 1D-b.
      "max-lines": [
        "warn",
        { max: 350, skipBlankLines: true, skipComments: true },
      ],
      "max-lines-per-function": [
        "warn",
        { max: 100, skipBlankLines: true, skipComments: true },
      ],
      // Phase 1C: lowered to 4 and raised to error
      "max-depth": ["error", 4],
      "max-params": ["error", 4],
      "max-nested-callbacks": ["warn", 4],
      "complexity": ["warn", 20],

      // React hooks (already in next/core-web-vitals but explicit here)
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",

      // General
      "eqeqeq": ["warn", "always", { null: "ignore" }],
      // "no-undef" disabled — TypeScript handles this via tsconfig
      "no-unused-vars": "off", // delegated to @typescript-eslint/no-unused-vars
    },
  },

  // ─── File naming conventions ───
  {
    plugins: { "check-file": checkFile },
    rules: {
      "check-file/filename-naming-convention": [
        "warn",
        {
          // React components: PascalCase
          "src/features/**/components/**/*.tsx": "PASCAL_CASE",
          "src/components/shared/**/*.tsx": "PASCAL_CASE",
          // Non-component files: kebab-case
          "src/features/**/api/*.ts": "KEBAB_CASE",
          "src/features/**/types/*.ts": "KEBAB_CASE",
          "src/features/**/utils/*.ts": "KEBAB_CASE",
          "src/features/**/config/*.ts": "KEBAB_CASE",
          "src/lib/**/*.ts": "KEBAB_CASE",
        },
        { ignoreMiddleExtensions: true },
      ],
      "check-file/folder-naming-convention": [
        "warn",
        {
          // All folders kebab-case (Next.js special dirs handled by ignoreMiddleExtensions)
          "src/features/**/": "KEBAB_CASE",
          "src/lib/**/": "KEBAB_CASE",
          "src/components/shared/**/": "KEBAB_CASE",
        },
        { ignoreMiddleExtensions: true },
      ],
    },
  },

  // ─── JSDoc enforcement (exported functions discoverable) ───
  {
    plugins: { jsdoc },
    rules: {
      "jsdoc/require-jsdoc": [
        "warn",
        {
          require: {
            FunctionDeclaration: true,
            MethodDefinition: false,
            ClassDeclaration: true,
          },
          publicOnly: true,
          checkConstructors: false,
        },
      ],
      "jsdoc/require-description": "warn",
      "jsdoc/check-tag-names": "warn",
      "jsdoc/no-undefined-types": "off",
      "jsdoc/require-param-type": "off",
      "jsdoc/require-returns-type": "off",
    },
  },

  // ─── Prettier integration ───
  prettier,

  // ─── Disable type-checked rules for test/story/mock files (performance: skip TypeScript program) ───
  // Block 1: spread disableTypeChecked alone — MUST NOT mix with extra rules key or spread gets overwritten
  // This alone saves ~30-40% of ESLint time by excluding 150+ files from the TS program.
  {
    files: [
      "**/*.test.ts",
      "**/*.test.tsx",
      "**/*.spec.ts",
      "**/*.spec.tsx",
      "**/*.stories.ts",
      "**/*.stories.tsx",
      "**/__tests__/**",
      "**/__mocks__/**",
    ],
    ...tseslint.configs.disableTypeChecked,
  },
  // Block 2: additional relaxed rules for test files (separate object so Block 1 rules are not overwritten)
  {
    files: [
      "**/*.test.ts",
      "**/*.test.tsx",
      "**/*.spec.ts",
      "**/*.spec.tsx",
      "**/*.stories.ts",
      "**/*.stories.tsx",
      "**/__tests__/**",
      "**/__mocks__/**",
    ],
    rules: {
      "max-lines": "off",
      "max-lines-per-function": "off",
      "@typescript-eslint/no-explicit-any": "warn",
    },
  },

  // ─── Ignore generated files ───
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "storybook-static/**",
      "src/components/ui/**", // shadcn auto-generated
      "e2e/**",
      "playwright/**",
      "coverage/**",
      "*.config.*", // config files (eslint, vitest, playwright, etc.)
      "*.config.mjs",
      "prettier.config.*",
    ],
  },
];
