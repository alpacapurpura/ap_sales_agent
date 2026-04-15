# Styling Rules (Tailwind CSS + Shadcn UI)

## Core Stack
- Tailwind CSS v3.4+ (utility-first)
- Shadcn UI (Radix primitives, auto-generated in `components/ui/`)
- `cn()` utility (clsx + tailwind-merge) from `lib/utils`

## Rules

### Class merging — always use `cn()`
```tsx
// Correct
className={cn("base-class", isActive && "active-class", className)}

// Wrong — no merge, duplicates not resolved
className={`base-class ${isActive ? 'active-class' : ''}`}
```

### Zero inline styles
No `style={{...}}` attribute. Use Tailwind utilities exclusively.

### Shadcn UI — never edit `components/ui/`
These files are auto-generated. Customization via:
1. `className` prop with `cn()` override
2. CSS variables in `globals.css`
3. Wrapper component in `components/shared/`

### Design tokens
CSS variables defined in `frontend/src/app/globals.css`. Used via Tailwind classes:
- Colors: `bg-primary`, `text-muted-foreground`, `border-border`
- Radius: `rounded-lg` (uses `--radius` var)
- Registry: `lib/design-system/registry.ts` (machine-readable catalog)

### Prettier config
- `prettier-plugin-tailwindcss` sorts Tailwind classes automatically
- `endOfLine: "lf"` — Unix line endings
- `printWidth: 100`
- `trailingComma: "all"`
- `singleQuote: false` (double quotes)
- `semi: true`

### Responsive
Mobile-first: `sm:`, `md:`, `lg:`, `xl:`. Default styles = mobile.

### Dark mode
Not implemented yet. When added: use `dark:` variant + CSS variables.
