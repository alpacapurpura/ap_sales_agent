# Design Stack & Assets

## 1. Core Frameworks
- **Styling**: Tailwind CSS v4.
  - **Configuration**: Managed via CSS variables in `globals.css` (`@theme`).
  - **Dark Mode**: Native semantic colors (`--background`, `--foreground`).
- **Components**: Shadcn UI (Radix UI + Tailwind).
  - **Location**: `src/components/ui/`.
  - **Philosophy**: Copy-paste, owned code. Customizable.

## 2. Available Primitives (Lego Blocks)
These are the building blocks available in the project. DO NOT reinvent them.

### Layout & Containers
- `card.tsx`: Base container. Use for everything.
- `sheet.tsx`: Side panels for complex edits without leaving context.
- `dialog.tsx`: Modals for critical confirmations.
- `scroll-area.tsx`: Essential for internal scrolling in Bento grids.
- `resizable.tsx`: Paneles ajustables (Dashboard style).

### Feedback & Interaction
- `sonner.tsx`: Toasts modernos (stackable).
- `skeleton.tsx`: Loading states (CRITICAL for AI latency).
- `progress.tsx`: For long-running AI tasks.

### Form & Input
- `form.tsx`: React Hook Form wrapper.
- `input.tsx`, `select.tsx`, `switch.tsx`.

## 3. Typography & Icons
- **Font**: Inter (Variable).
- **Icons**: Lucide React (`<IconName className="size-4" />`).

## 4. Theming Capabilities (Tailwind v4)
You can define dynamic themes by injecting CSS variables.
Example:
```css
@theme {
  --color-brand-primary: #ff0000;
}
```
Use this for "Brand Preview" features where the user customizes their agent's look.
