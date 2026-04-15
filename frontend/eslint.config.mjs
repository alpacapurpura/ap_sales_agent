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
      // Phase 1A: warn mode; Phase 1C: error + lower threshold
      "sonarjs/cognitive-complexity": ["warn", 20],
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
      // Phase 1A: warn only (non-breaking); Phase 3: error after fixing deep imports
      "boundaries/no-unknown": "warn",
      "boundaries/dependencies": [
        "warn",
        {
          default: "disallow",
          rules: [
            // app/ pages import from features, shared components, lib (this is Next.js pattern)
            {
              from: { type: "app" },
              allow: { to: { type: ["feature", "feature:own", "shared", "lib", "ui", "hooks", "providers"] } },
            },
            // features can ONLY import from: own feature, shared components, lib
            {
              from: { type: "feature" },
              allow: { to: { type: ["feature:own", "shared", "lib", "util"] } },
            },
            // components/shared can import from lib and util
            {
              from: { type: "shared" },
              allow: { to: { type: ["lib", "util", "ui"] } },
            },
            // lib cannot import from features
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

      // Complexity limits (Phase 1A: warn; Phase 1C: lower thresholds)
      "max-lines": [
        "warn",
        { max: 500, skipBlankLines: true, skipComments: true },
      ],
      "max-lines-per-function": [
        "warn",
        { max: 100, skipBlankLines: true, skipComments: true },
      ],
      "max-depth": ["warn", 5],
      "max-params": ["warn", 5],
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

  // ─── Prettier integration ───
  prettier,

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
