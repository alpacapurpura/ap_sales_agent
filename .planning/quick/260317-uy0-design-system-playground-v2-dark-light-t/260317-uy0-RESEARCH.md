# Research: Storybook Setup for Next.js 15 + Tailwind v4 + Shadcn UI

**Quick Task:** 260317-uy0
**Date:** 2026-03-18
**Confidence:** HIGH

## Key Findings

### 1. Framework Choice: @storybook/nextjs-vite
- Storybook team recommends Vite-based framework for Next.js 15
- `@storybook/nextjs` (Webpack) has known React 19 version inconsistencies
- Vite is faster and has better testing feature support

### 2. Tailwind v4 Integration
- Tailwind v4 uses `@tailwindcss/postcss` (already in our devDependencies)
- No `tailwind.config.ts` needed — config is in CSS via `@theme` directive
- Storybook picks up PostCSS config automatically with Vite
- Just import `globals.css` in `.storybook/preview.ts`

### 3. Dark Mode Setup
```typescript
// .storybook/preview.ts
import { withThemeByClassName } from '@storybook/addon-themes';
import '../src/app/globals.css';

const preview = {
  decorators: [
    withThemeByClassName({
      themes: { light: '', dark: 'dark' },
      defaultTheme: 'light',
    }),
  ],
};
```
- Empty string for light (no class on html = `:root` styles)
- `'dark'` for dark mode (adds `dark` class = `html.dark` styles)
- Matches our existing CSS architecture exactly

### 4. Story Pattern for Shadcn Components
```typescript
// Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from '@/components/ui/button';

const meta = {
  title: 'Atoms/Button',
  component: Button,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'secondary', 'destructive', 'ghost', 'link', 'outline'],
    },
    size: { control: 'select', options: ['default', 'sm', 'lg', 'icon'] },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { children: 'Button', variant: 'default' } };
export const Secondary: Story = { args: { children: 'Secondary', variant: 'secondary' } };
// ... one export per variant
```

### 5. Our Stack Versions
- Next.js 15.5.13
- React 19.2.3
- Tailwind CSS 4.1.18 (v4 — CSS-based config)
- @tailwindcss/postcss 4.1.18
- next-themes 0.4.6

### 6. Installation Commands
```bash
npx storybook@latest init --builder vite
npm install -D @storybook/addon-themes @storybook/addon-a11y
```

### 7. Docker Considerations
- Storybook dev server needs port 6006 exposed
- Add to docker-compose.yml: `ports: ["6006:6006"]` on client_dev service
- Script: `"storybook": "storybook dev -p 6006 --host 0.0.0.0"`

## Open Questions
- None — all resolved via research

## Sources
- https://storybook.js.org/docs/get-started/frameworks/nextjs
- https://storybook.js.org/recipes/tailwindcss
- https://storybook.js.org/docs/essentials/themes
- https://dev.to/shaikathaque/design-system-in-react-with-tailwind-shadcnui-and-storybook-17f
