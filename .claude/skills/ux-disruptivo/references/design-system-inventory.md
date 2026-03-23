# Nicolify Design System Inventory

> **Note:** This is a snapshot. Phase 3 of ux-disruptivo always verifies against the live codebase.

## Installed Shadcn Components (37)

accordion, alert, alert-dialog, avatar, badge, button, calendar, card, checkbox,
collapsible, command, currency-selector, dialog, dropdown-menu, field-info, form,
highlighted-text, input, label, popover, progress, radio-group, rich-select,
scroll-area, select, separator, sheet, skeleton, smart-datetime-picker, sonner,
switch, table, tabs, textarea, timezone-select, tooltip

## CSS Variables (globals.css)

### Light Mode
| Token | HSL Value | Usage |
|---|---|---|
| `--background` | `0 0% 100%` | Page background (white) |
| `--foreground` | `222.2 84% 4.9%` | Primary text (near-black) |
| `--card` | `0 0% 100%` | Card backgrounds |
| `--primary` | `222.2 47.4% 11.2%` | Buttons, links (dark navy) |
| `--secondary` | `210 40% 96.1%` | Secondary actions (light blue-gray) |
| `--muted` | `210 40% 96.1%` | Disabled/subtle backgrounds |
| `--muted-foreground` | `215.4 16.3% 46.9%` | Secondary text |
| `--accent` | `210 40% 96.1%` | Hover backgrounds |
| `--destructive` | `0 84.2% 60.2%` | Errors, delete actions (red) |
| `--border` | `214.3 31.8% 91.4%` | Borders (light gray) |
| `--ring` | `222.2 84% 4.9%` | Focus rings |
| `--radius` | `0.5rem` | Border radius base |

### Dark Mode (html.dark)
| Token | HSL Value | Usage |
|---|---|---|
| `--background` | `222.2 47.4% 11.2%` | Slate-950 background |
| `--foreground` | `210 40% 98%` | White text |
| `--card` | `217.2 32.6% 17.5%` | Slightly lighter than bg |
| `--primary` | `210 40% 98%` | White/light buttons |
| `--secondary` | `217.2 32.6% 17.5%` | Muted blue-gray |
| `--muted-foreground` | `215 20.2% 65.1%` | Low-contrast text |
| `--destructive` | `0 62.8% 30.6%` | Darker red for dark mode |
| `--border` | `217.2 32.6% 17.5%` | Subtle borders |

## Custom Utility Classes

| Class | Equivalent | Usage |
|---|---|---|
| `.v-stack` | `flex flex-col` | Vertical stacking |
| `.h-stack` | `flex flex-row items-center` | Horizontal row with centering |
| `.center` | `flex items-center justify-center` | Centering content |
| `.spacer` | `grow` | Flex spacer |

## Animations

| Class | Animation | Duration | Usage |
|---|---|---|---|
| `.animate-fade-in` | fadeIn (opacity 0→1, translateY 4px→0) | 200ms ease-in | Panel reveals |
| `.bottleneck-critical` | pulseBorder (red glow pulse) | 2s infinite | Critical alerts |
| `.skeleton-loading` | shimmer (gradient slide) | 1.5s infinite | Loading states |

## Data Visualization

- Library: `@visx` (Airbnb's viz primitives for React)
- Used in: Growth Studio metrics dashboard

## Icons

- Library: `lucide-react`
- Pattern: `import { IconName } from "lucide-react"`

## Typography

- Font stack: System defaults (no custom fonts loaded)
- Scale: Tailwind defaults (text-xs through text-5xl)

## Radius Scale

| Token | Value |
|---|---|
| `--radius` (lg) | `0.5rem` |
| `--radius-md` | `calc(0.5rem - 2px)` = ~6px |
| `--radius-sm` | `calc(0.5rem - 4px)` = ~4px |
