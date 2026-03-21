# Hooks & Utilities

Shared React hooks and utility functions used across the application.

## Custom Hooks

All hooks are exported from `src/hooks/index.ts`.

```typescript
import { useDebounce, useLocalStorage, useIntersectionObserver } from "@/hooks";
```

### `useDebounce`

Debounces a value, delaying updates until a specified time has elapsed without further changes. Useful for search inputs or any rapidly-changing value.

```typescript { .api }
/**
 * Debounces a value by the specified delay.
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds
 * @returns The debounced value (updated only after delay elapses)
 */
function useDebounce<T>(value: T, delay: number): T;
```

**Usage:**
```typescript
import { useDebounce } from "@/hooks";
import { useState } from "react";

function SearchInput() {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);

  // debouncedQuery only updates 300ms after typing stops
  useEffect(() => {
    if (debouncedQuery) fetchResults(debouncedQuery);
  }, [debouncedQuery]);

  return <input value={query} onChange={e => setQuery(e.target.value)} />;
}
```

### `useLocalStorage`

Persists state to localStorage with SSR safety (returns `initialValue` during server-side rendering).

```typescript { .api }
/**
 * Persists state to localStorage.
 * @param key - localStorage key
 * @param initialValue - Default value if key not set or on SSR
 * @returns [storedValue, setValue] tuple
 */
function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T | ((val: T) => T)) => void];
```

**Usage:**
```typescript
import { useLocalStorage } from "@/hooks";

function ThemeToggle() {
  const [theme, setTheme] = useLocalStorage<"light" | "dark">("theme", "light");
  return <button onClick={() => setTheme(theme === "light" ? "dark" : "light")}>{theme}</button>;
}
```

### `useIntersectionObserver`

Tracks whether an element is visible in the viewport using the IntersectionObserver API.

```typescript { .api }
interface UseIntersectionObserverProps {
  threshold?: number | number[];   // default: 0
  root?: Element | null;
  rootMargin?: string;             // default: "0px"
  freezeOnceVisible?: boolean;     // stop observing after first intersection
}

/**
 * Tracks element visibility via IntersectionObserver.
 * @param options - IntersectionObserver options
 * @returns [ref, isVisible] — attach ref to target element
 */
function useIntersectionObserver(
  options?: UseIntersectionObserverProps
): [RefObject<Element | null>, boolean];
```

**Usage:**
```typescript
import { useIntersectionObserver } from "@/hooks";

function LazySection() {
  const [ref, isVisible] = useIntersectionObserver({ threshold: 0.1, freezeOnceVisible: true });
  return (
    <div ref={ref}>
      {isVisible ? <ExpensiveComponent /> : <Skeleton />}
    </div>
  );
}
```

---

## Utility Functions

### `cn` — Class Name Merger

Merges Tailwind CSS class names, resolving conflicts with tailwind-merge and supporting conditional classes via clsx.

```typescript { .api }
import { cn } from "@/lib/utils";
import type { ClassValue } from "clsx";

/**
 * Merges class names, resolving Tailwind conflicts.
 * @param inputs - Any number of class values (strings, arrays, objects)
 * @returns Merged class string
 */
function cn(...inputs: ClassValue[]): string;
```

**Usage:**
```typescript
cn("px-4 py-2", "px-6")                    // → "py-2 px-6"
cn("text-red-500", { "font-bold": isActive }) // conditional
cn(buttonVariants({ variant: "outline" }), className)
```

---

### `getAssetUrl` — Asset URL Resolver

Resolves an asset's `public_url` field to a fully-qualified URL. Handles both absolute Cloudflare R2 URLs and legacy relative paths.

```typescript { .api }
import { getAssetUrl } from "@/lib/utils/assets";

/**
 * Resolves an asset public URL to a fully-qualified URL.
 * - Absolute URLs (http/https) are returned as-is
 * - Relative paths are prefixed with config.api.baseUrl
 * @param publicUrl - The public_url field from an Asset record
 * @returns Fully-qualified URL string, or "" if input is null/undefined
 */
function getAssetUrl(publicUrl?: string | null): string;
```

**Usage:**
```typescript
const url = getAssetUrl(asset.public_url);
// "https://assets.nicolify.com/image.jpg" → returned as-is
// "/static/uploads/image.jpg" → "https://api.example.com/static/uploads/image.jpg"
// null/undefined → ""
```

---

### Color Utilities

Color manipulation utilities for brand theming. All functions in `src/lib/utils/colors.ts`.

```typescript { .api }
import {
  hexToRgb,
  getLuminance,
  getContrastColor,
  adjustBrightness,
  hexToHsl,
} from "@/lib/utils/colors";

/**
 * Converts hex color string to RGB components.
 * @param hex - Hex color string (with or without #)
 * @returns { r, g, b } object or null if invalid
 */
function hexToRgb(hex: string): { r: number; g: number; b: number } | null;

/**
 * Calculates relative luminance per WCAG.
 * @returns Luminance value (0 = black, 1 = white)
 */
function getLuminance(r: number, g: number, b: number): number;

/**
 * Returns accessible contrast color (#000000 or #ffffff) for text on the given background.
 * @param hex - Background hex color
 * @returns "#000000" for light backgrounds, "#ffffff" for dark
 */
function getContrastColor(hex: string): string;

/**
 * Adjusts color brightness by a percentage.
 * @param hex - Source hex color
 * @param percent - Positive to brighten, negative to darken (e.g. 20 = +20%)
 * @returns Adjusted hex color string
 */
function adjustBrightness(hex: string, percent: number): string;

/**
 * Converts hex color to HSL format used in Tailwind/CSS variables.
 * @param hex - Hex color string
 * @returns HSL string in format "H S% L%" (e.g. "220 14.3% 95.9%")
 */
function hexToHsl(hex: string): string;
```

**Usage:**
```typescript
const rgb = hexToRgb("#3b82f6");          // { r: 59, g: 130, b: 246 }
const contrast = getContrastColor("#3b82f6"); // "#ffffff"
const darker = adjustBrightness("#3b82f6", -20); // darker blue
const hsl = hexToHsl("#3b82f6");          // "217 91.2% 59.8%"
```

---

## HTTP Client & Config

### `fetchClient`

The core HTTP client used by all API modules. Automatically injects the current tenant's `X-Tenant-ID` header from the URL path (or localStorage fallback) and redirects on auth errors.

```typescript { .api }
import { fetchClient } from "@/lib/http-client";

/**
 * Fetch wrapper with tenant injection and auth error handling.
 * - Injects X-Tenant-ID from URL path first segment (if not a global route)
 * - Redirects to /forbidden on 403 responses
 * - Redirects to /sign-in on 401 responses
 * @param input - URL or RequestInfo
 * @param init - Standard RequestInit options
 * @returns Response promise
 */
async function fetchClient(input: RequestInfo | URL, init?: RequestInit): Promise<Response>;
```

### `config`

Application configuration object.

```typescript { .api }
import { config } from "@/lib/config";

const config: {
  api: {
    /** API base URL. Server-side: INTERNAL_API_URL env var. Client-side: NEXT_PUBLIC_API_URL or "" (same origin) */
    baseUrl: string;
  };
};
```

**Environment variables:**
- `INTERNAL_API_URL` — Server-side Docker internal URL (e.g. `http://visionarias_brain_dev:8000`)
- `NEXT_PUBLIC_API_URL` — Client-side public API URL (e.g. `https://api.nicolify.com`)
