# AI Brand Identity Extraction API

API functions that use AI to automatically extract brand identity information from external sources. Supports two extraction modes:
1. **Visual extraction** — extracts colors and typography from a URL (website or social profile)
2. **Full extraction** — extracts a complete brand profile from structured data or a form submission

Both functions must support both JSON and `FormData` request bodies, routing correctly based on the input type.

## Capabilities

### Visual brand extraction from URL

Sends a POST request with a URL and source type, returning extracted visual identity data (colors, fonts).

- Posting `{ url: "https://example.com", type: "website" }` to the AI actions endpoint returns extracted brand visuals [@test](./tests/extract-visuals.test.ts)
- The request uses `Content-Type: application/json` and includes `Authorization: Bearer <token>` [@test](./tests/extract-visuals-auth.test.ts)

### Full brand extraction

Accepts either a plain object or a `FormData` instance. When given a plain object, sends JSON; when given `FormData`, sends multipart.

- Passing a plain JavaScript object sends a JSON request with `Content-Type: application/json` [@test](./tests/extract-full-json.test.ts)
- Passing a `FormData` instance sends the request without setting `Content-Type` (allowing the browser to set multipart boundaries) [@test](./tests/extract-full-formdata.test.ts)
- Both paths POST to the same endpoint and include the Bearer token [@test](./tests/extract-full-auth.test.ts)

## Implementation

[@generates](./src/lib/api/ai-actions.ts)

## API

```typescript { #api }
export interface BrandVisualsResult {
  colors: string[];
  fonts: string[];
  [key: string]: unknown;
}

export interface FullBrandResult {
  name?: string;
  tagline?: string;
  description?: string;
  [key: string]: unknown;
}

export function extractBrandIdentity(
  data: { url: string; type: string },
  token?: string
): Promise<BrandVisualsResult>;

export function extractFullBrand(
  data: Record<string, unknown> | FormData,
  token?: string
): Promise<FullBrandResult>;
```

## Dependencies { .dependencies }

### visionarias-client 0.1.0 { .dependency }

AI Sales & Marketing Platform frontend providing AI-powered brand extraction API clients for automated brand identity capture.

[@satisfied-by](visionarias-client)
