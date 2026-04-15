import type { KnipConfig } from "knip";

const config: KnipConfig = {
  entry: [
    "src/app/**/page.tsx",
    "src/app/**/layout.tsx",
    "src/app/**/route.ts",
    "src/app/**/loading.tsx",
    "src/app/**/error.tsx",
    "src/app/**/not-found.tsx",
    "src/lib/design-system/registry.ts",
    "src/middleware.ts",
  ],
  project: ["src/**/*.{ts,tsx}"],
  ignore: [
    "src/components/ui/**",
    "e2e/**",
    "**/*.test.*",
    "**/*.spec.*",
    "**/*.stories.*",
  ],
  ignoreDependencies: [
    "@trivago/prettier-plugin-sort-imports",
    "prettier-plugin-tailwindcss",
    "eslint-plugin-jsx-a11y",
    "eslint-plugin-react-hooks",
    "lint-staged",
    "tailwindcss-animate",
    "eslint-plugin-check-file",
    "eslint-plugin-jsdoc",
  ],
};

export default config;
