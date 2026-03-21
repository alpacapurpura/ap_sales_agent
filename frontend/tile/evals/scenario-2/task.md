# Conditional Class Name Utility

A utility function that merges multiple class name inputs — including strings, arrays, and conditional expressions — while also resolving Tailwind CSS class conflicts so that later classes override earlier ones.

## Capabilities

### Class name combination

Combines multiple class string arguments into a single space-separated string.

- `("px-4", "py-2", "rounded")` returns `"px-4 py-2 rounded"` [@test](./tests/cn-combine.test.ts)
- `("base-class", false && "hidden-class", "another-class")` returns `"base-class another-class"` (falsy values are excluded) [@test](./tests/cn-conditional.test.ts)

### Tailwind conflict resolution

When two Tailwind classes conflict (same utility, different value), the last one wins.

- `("p-4", "p-8")` returns `"p-8"` (later padding wins) [@test](./tests/cn-tailwind-conflict.test.ts)
- `("text-red-500", "text-blue-500")` returns `"text-blue-500"` [@test](./tests/cn-color-conflict.test.ts)
- `("flex", "hidden", "block")` returns `"block"` (last display utility wins) [@test](./tests/cn-display-conflict.test.ts)

## Implementation

[@generates](./src/utils.ts)

## API

```typescript { #api }
export function cn(...inputs: ClassValue[]): string;
```

## Dependencies { .dependencies }

### visionarias-client 0.1.0 { .dependency }

AI Sales & Marketing Platform frontend providing the `cn` className merging utility built on clsx and tailwind-merge.

[@satisfied-by](visionarias-client)
