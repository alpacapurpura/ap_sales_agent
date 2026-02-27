# Code Quality & Best Practices

## Styling & Classes

### 1. Enforce `cn()` Utility for Conditional Classes
**Context:** The project uses `clsx` and `tailwind-merge` (typically exposed via a `cn` helper in `src/lib/utils.ts`).
**Rule:** Always use the `cn()` utility for conditional class application. Avoid template literals or string concatenation for classes.
**Why:** Ensures Tailwind classes are merged correctly (handling conflicts like `p-4` vs `p-2`) and keeps code clean.

**Bad:**
```tsx
<div className={`text-primary ${isActive ? 'font-bold' : ''}`} />
```

**Good:**
```tsx
import { cn } from "@/lib/utils";
<div className={cn("text-primary", isActive && "font-bold")} />
```

### 2. Tailwind-First Styling
**Rule:** Use Tailwind utility classes for all styling. Avoid `.css` or `.module.css` files unless absolutely necessary (e.g., complex animations or 3rd party overrides).
**Why:** Consistency, smaller bundle size, and collocation of styles with markup.

### 3. ClassName Prop Override Pattern
**Rule:** Reusable components must accept a `className` prop and merge it *last* using `cn()`.
**Why:** Allows consumers to override default styles without `!important`.

**Pattern:**
```tsx
export function MyComponent({ className, ...props }: Props) {
  return (
    <div className={cn("bg-white p-4", className)} {...props}>
      {/* ... */}
    </div>
  );
}
```

## React Performance & Logic

### 1. Complex Prop Memoization
**Rule:** Wrap complex objects/arrays passed as props in `useMemo` if they are created during render, especially for expensive children.
**Why:** Prevents unnecessary re-renders of child components that use `React.memo` or effect dependencies.

### 2. Component Logic Extraction
**Rule:** If a component exceeds ~150 lines or has complex `useEffect` logic, extract the logic into a custom hook (e.g., `useMyComponentLogic.ts`) located in the same directory (if shared) or `hooks/` folder.
**Why:** Separation of concerns (View vs Logic) and easier testing.
