# Element Visibility Hook

A React hook that tracks whether a DOM element is visible in the viewport using the Intersection Observer API. Returns a ref to attach to the target element and a boolean indicating current visibility. Supports a `freezeOnceVisible` option that stops observing the element after it first enters the viewport.

## Capabilities

### Viewport visibility detection

Attaches an IntersectionObserver to the target element and updates a boolean state when visibility changes.

- Returns a tuple `[ref, isVisible]` where `isVisible` starts as `false` before the element enters the viewport [@test](./tests/intersection-initial.test.ts)
- When the observed element intersects the viewport, `isVisible` becomes `true` [@test](./tests/intersection-visible.test.ts)
- When the element leaves the viewport, `isVisible` returns to `false` (when `freezeOnceVisible` is not set) [@test](./tests/intersection-leave.test.ts)

### Freeze on first visibility

- When `freezeOnceVisible` is `true` and the element becomes visible, it stays `true` even after the element leaves the viewport [@test](./tests/intersection-freeze.test.ts)

### Observer options passthrough

- Accepts standard IntersectionObserverInit options (threshold, rootMargin, root) which are forwarded to the underlying IntersectionObserver constructor [@test](./tests/intersection-options.test.ts)

## Implementation

[@generates](./src/use-intersection-observer.ts)

## API

```typescript { #api }
interface UseIntersectionObserverOptions extends IntersectionObserverInit {
  freezeOnceVisible?: boolean;
}

export function useIntersectionObserver(
  options?: UseIntersectionObserverOptions
): [React.RefObject<Element>, boolean];
```

## Dependencies { .dependencies }

### visionarias-client 0.1.0 { .dependency }

AI Sales & Marketing Platform frontend providing the useIntersectionObserver hook for lazy-loading and scroll-based animations.

[@satisfied-by](visionarias-client)
