# Debounced Value Hook

A React hook that returns a debounced version of a given value, updating only after the specified delay has elapsed since the last change.

## Capabilities

### Debounced value update

Returns the latest value only after no new value has been provided for the specified delay period.

- Given a value of `"hello"` and a delay of `300`, the hook immediately returns `"hello"` on mount [@test](./tests/debounce-initial.test.ts)
- Given rapid value changes `"a"`, `"ab"`, `"abc"` within 300ms with a 300ms delay, the debounced value only updates to `"abc"` after 300ms have passed [@test](./tests/debounce-rapid.test.ts)
- When the delay is `0`, the debounced value updates synchronously on the next tick [@test](./tests/debounce-zero-delay.test.ts)
- Works with non-string types: given a numeric value `42` and delay `200`, the debounced value returns `42` after 200ms [@test](./tests/debounce-numeric.test.ts)

## Implementation

[@generates](./src/use-debounce.ts)

## API

```typescript { #api }
export function useDebounce<T>(value: T, delay: number): T;
```

## Dependencies { .dependencies }

### visionarias-client 0.1.0 { .dependency }

AI Sales & Marketing Platform frontend providing custom React utility hooks for performance optimization.

[@satisfied-by](visionarias-client)
