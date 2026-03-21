# visionarias-client

visionarias-client is a private Next.js 15 / React 19 frontend application for Nicolify (formerly Visionarias), an AI-powered multi-tenant Sales and Marketing Platform. It provides a comprehensive dashboard for managing AI sales agents, brand identity, offer creation, marketing analytics, and third-party service integrations.

## Package Information

- **Package Name**: visionarias-client
- **Package Type**: npm (private application)
- **Language**: TypeScript
- **Framework**: Next.js 15 (App Router)
- **Installation**: Internal application — clone repository and run `npm install` in the `frontend/` directory

## Core Imports

```typescript
// UI components (shadcn/ui)
import { Button, Input, Dialog } from "@/components/ui/<component>";

// Custom hooks
import { useDebounce, useLocalStorage, useIntersectionObserver } from "@/hooks";

// Utilities
import { cn } from "@/lib/utils";
import { getAssetUrl } from "@/lib/utils/assets";
import { getContrastColor, hexToRgb, adjustBrightness, hexToHsl } from "@/lib/utils/colors";

// HTTP client
import { fetchClient } from "@/lib/http-client";
import { config } from "@/lib/config";

// API clients
import { settingsApi } from "@/lib/api/settings";
import { assetsApi } from "@/lib/api/assets";
import { connectionsApi } from "@/lib/api/connections";
// ... other API modules
```

## Basic Usage

```typescript
// Example: Fetch tenant settings and display brand settings
import { settingsApi } from "@/lib/api/settings";
import { Button } from "@/components/ui/button";
import { useAuth } from "@clerk/nextjs";

export default function SettingsPage() {
  const { getToken } = useAuth();

  async function loadSettings() {
    const token = await getToken();
    const brand = await settingsApi.getBrandSettings(token!);
    console.log(brand.visuals.primary_color);
  }

  return <Button onClick={loadSettings}>Load Settings</Button>;
}
```

## Architecture

The application follows Feature-Sliced Design (FSD) with multi-tenant routing:

- **Routing**: Next.js App Router with `[tenantId]` dynamic segments for per-tenant isolation
- **Authentication**: Clerk for auth; all API calls require Bearer JWT tokens
- **State Management**: TanStack Query for server state; React Hook Form + Zod for forms
- **UI System**: Radix UI primitives with shadcn/ui component patterns and Tailwind CSS v4
- **Multi-tenancy**: `X-Tenant-ID` header auto-injected by `fetchClient` from URL path
- **API Layer**: Typed REST client modules per domain (`settingsApi`, `assetsApi`, etc.)

## Capabilities

### UI Components

Comprehensive set of accessible, styled UI primitives based on Radix UI and shadcn/ui. Includes form controls, layout components, overlays, navigation, and data display.

```typescript { .api }
import { Button, buttonVariants, type ButtonProps } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Badge, badgeVariants, type BadgeProps } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Select, SelectTrigger, SelectContent, SelectItem } from "@/components/ui/select";
import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
```

[UI Components](./ui-components.md)

### Custom Hooks & Utilities

Shared React hooks for common patterns and utility functions for class names, assets, and color manipulation.

```typescript { .api }
import { useDebounce } from "@/hooks";
import { useLocalStorage } from "@/hooks";
import { useIntersectionObserver } from "@/hooks";
import { cn } from "@/lib/utils";
import { getAssetUrl } from "@/lib/utils/assets";
import { getContrastColor, hexToRgb, adjustBrightness, hexToHsl, getLuminance } from "@/lib/utils/colors";
```

[Hooks & Utilities](./hooks-utils.md)

### REST API Clients

Typed API client modules for each backend domain. All methods require a Clerk JWT auth token. The `fetchClient` HTTP wrapper handles tenant injection and auth error redirects automatically.

```typescript { .api }
import { fetchClient } from "@/lib/http-client";
import { config } from "@/lib/config";

// Domain-specific API clients
import { settingsApi } from "@/lib/api/settings";
import { assetsApi } from "@/lib/api/assets";
import { avatarApi } from "@/lib/api/avatar";
import { availabilityApi } from "@/lib/api/availability";
import { connectionsApi } from "@/lib/api/connections";
import { crmDashboardApi } from "@/lib/api/crm-dashboard-api";
import { eventTypesApi } from "@/lib/api/event-types";
import { leadsApi } from "@/lib/api/leads";
import { offerGalleryApi } from "@/lib/api/offer-gallery";
import { bookingLinksApi } from "@/lib/api/booking-links";
import { publicApi } from "@/lib/api/public";
import { whatsappApi } from "@/lib/api/whatsapp";
import { aiActionsApi } from "@/lib/api/ai-actions";
import { adminApi } from "@/lib/api/admin";
```

[API Clients](./api-clients.md)

### Feature Modules

Domain-specific modules following Feature-Sliced Design. Each feature encapsulates its own components, hooks, API calls, and types.

```typescript { .api }
// Brand feature
import { brandApi } from "@/features/brand/api";
import type { BrandSettings, BrandIdentity, BrandVisuals, KeyFigure } from "@/features/brand/types";

// Settings feature
import { WebhookView, AIKeysForm, GeneralSettingsForm, ProfileView } from "@/features/settings";
import { useUserProfile, useTenants } from "@/features/settings";

// Audit feature
import { AuditDashboard, useAudit } from "@/features/audit";

// Connections feature
import { GoogleWorkspaceView, TelegramView } from "@/features/connections";
```

[Feature Modules](./features.md)

### Constants & Design Tokens

Currency constants and design system registry.

```typescript { .api }
import { CURRENCIES, DEFAULT_CURRENCY, type Currency } from "@/lib/constants/currencies";
import { COMPONENT_REGISTRY } from "@/lib/design-system/registry";
import type { AtomicLevel, ComponentEntry, DesignToken } from "@/lib/design-system/types";

interface Currency {
  code: string;    // e.g. "USD"
  name: string;    // e.g. "US Dollar"
  symbol: string;  // e.g. "$"
  flag: string;    // emoji flag
}

// CURRENCIES: Currency[] — array of all 13 supported currencies
// DEFAULT_CURRENCY: Currency — defaults to USD

type AtomicLevel = "token" | "atom" | "molecule" | "organism";

interface ComponentEntry {
  name: string;             // Display name, e.g. "Button"
  atomicLevel: AtomicLevel;
  filePath: string;         // Path relative to frontend/src
  source: "shadcn" | "shared" | "feature";
  featureSlice?: string;    // Set when source === 'feature'
  variants?: string[];      // CVA variant names if applicable
  props?: string[];         // Key exported prop names
  description: string;      // One-line purpose
  issues?: string[];        // Audit issues found
}

interface DesignToken {
  category: "color" | "typography" | "spacing" | "radius" | "shadow";
  name: string;
  cssVar?: string;
  tailwindClass: string;
  value: string;
  darkValue?: string;       // Dark mode HSL value (color tokens only)
}

// COMPONENT_REGISTRY: ComponentEntry[] — machine-readable catalog of all components
// Used by AI generation tools and component playground
```

Supported currencies: USD, EUR, GBP, CAD, AUD, MXN, COP, ARS, CLP, PEN, BRL, JPY, CNY.
