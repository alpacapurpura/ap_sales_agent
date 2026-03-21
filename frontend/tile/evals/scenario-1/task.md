# LocalStorage State Hook

A React hook that persists component state to localStorage, so values survive page refreshes. The hook must be safe to use in SSR environments where `window` may not be available.

## Capabilities

### Persistent state initialization

Reads the initial value from localStorage on mount, falling back to the provided default when no stored value exists.

- When localStorage has no value for key `"theme"`, the hook returns the provided default value `"light"` [@test](./tests/localstorage-default.test.ts)
- When localStorage already contains `"dark"` for key `"theme"`, the hook returns `"dark"` on initialization [@test](./tests/localstorage-read.test.ts)

### State persistence on update

Writing a new value via the setter both updates the React state and writes to localStorage.

- After calling the setter with `"dark"`, `localStorage.getItem("theme")` returns `"dark"` [@test](./tests/localstorage-write.test.ts)
- The hook handles non-string values by JSON-serializing them; setting an object `{ count: 3 }` stores valid JSON and restores the object correctly [@test](./tests/localstorage-json.test.ts)

### SSR safety

- When `window` is not defined (SSR context), the hook returns the initial value without throwing [@test](./tests/localstorage-ssr.test.ts)

## Implementation

[@generates](./src/use-local-storage.ts)

## API

```typescript { #api }
export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T) => void];
```

## Dependencies { .dependencies }

### visionarias-client 0.1.0 { .dependency }

AI Sales & Marketing Platform frontend providing localStorage-backed React state hooks with SSR support.

[@satisfied-by](visionarias-client)
