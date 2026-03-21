# Landing Page Configuration API

API functions for a drag-and-drop landing page builder. Each offer has an associated landing page defined by a structured configuration object (blocks layout, content, and theme). The API also supports AI-powered content remixing via natural language instructions.

## Capabilities

### Fetch landing page configuration

Retrieves the current landing page configuration for a given offer ID.

- A GET request to `/api/offers/<offerId>/landing-page` with Bearer auth returns the landing page config object [@test](./tests/get-landing-page.test.ts)

### Save landing page configuration

Persists an updated landing page configuration by sending a PUT request.

- A PUT to `/api/offers/<offerId>/landing-page` with a JSON body containing the full page config object saves the configuration [@test](./tests/update-landing-page.test.ts)
- The request includes `Content-Type: application/json` and `Authorization: Bearer <token>` [@test](./tests/update-landing-page-headers.test.ts)

### AI remix of landing page content

Sends natural language instructions to an AI endpoint to regenerate landing page content for a given offer, returning updated page configuration.

- A POST to the AI remix endpoint with `{ offer_id: "<id>", instructions: "<text>" }` returns updated page content [@test](./tests/remix-landing-page.test.ts)
- The request uses JSON body with `Content-Type: application/json` and Bearer auth [@test](./tests/remix-auth.test.ts)

## Implementation

[@generates](./src/lib/api/landing-page.ts)

## API

```typescript { #api }
export interface LandingPageConfig {
  blocks: unknown[];
  theme?: Record<string, unknown>;
  [key: string]: unknown;
}

export function getLandingPage(
  offerId: string,
  token?: string
): Promise<LandingPageConfig>;

export function updateLandingPage(
  offerId: string,
  config: LandingPageConfig,
  token?: string
): Promise<LandingPageConfig>;

export function remixLandingPage(
  offerId: string,
  instructions: string,
  token?: string
): Promise<LandingPageConfig>;
```

## Dependencies { .dependencies }

### visionarias-client 0.1.0 { .dependency }

AI Sales & Marketing Platform frontend providing the landing page builder API with AI remix capability for offer landing pages.

[@satisfied-by](visionarias-client)
