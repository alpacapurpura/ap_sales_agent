# REST API Clients

All API client modules are located in `src/lib/api/`. They use `fetchClient` for HTTP requests and `config.api.baseUrl` for the base URL. All authenticated methods require a Clerk JWT `token` string obtained via `getToken()` from `useAuth()`.

## Common Pattern

```typescript
import { useAuth } from "@clerk/nextjs";

export default function MyComponent() {
  const { getToken } = useAuth();

  async function loadData() {
    const token = await getToken();
    const data = await someApi.someMethod(token!);
    // ...
  }
}
```

All methods throw an `Error` with a descriptive message if the HTTP response is not ok.

---

## `settingsApi` — Tenant Settings

```typescript { .api }
import { settingsApi } from "@/lib/api/settings";
import type {
  GeneralSettings,
  WebhookSettings,
  AISettings,
  Tenant,
  TenantProfile,
  SystemUserProfile,
  BrandVisuals,
  BrandStrategy,
  BrandSettings,
  TeamMember,
  TeamMemberCreate,
} from "@/lib/api/settings";

interface GeneralSettings {
  default_currency: string; // e.g. "USD"
}

interface WebhookSettings {
  webhook_url: string;
  webhook_secret: string | null;
}

interface AISettings {
  openai_api_key: string | null;
  gemini_api_key: string | null;
  can_use_platform_keys: boolean;
}

interface Tenant {
  id: string;
  name: string;
  slug: string;
  role: string;
}

interface TenantProfile {
  id: string;
  name: string;
  slug: string;
}

interface SystemUserProfile {
  id: string;
  full_name: string | null;
  email: string;
  tenant: TenantProfile | null;
}

interface BrandVisuals {
  primary_color: string;
  accent_color: string;
  background_color?: string;
  text_primary_color?: string;
  text_on_primary?: string;
  font_heading: string;
  font_body: string;
  design_style?: string;
}

interface BrandStrategy {
  unique_value_proposition?: string;
  methodology_name?: string;
}

interface BrandSettings {
  visuals: BrandVisuals;
  strategy: BrandStrategy;
}

interface TeamMember {
  id: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface TeamMemberCreate {
  full_name: string;
  email: string;
  password: string;
}

const settingsApi: {
  getTenants(token: string): Promise<Tenant[]>;
  getTeam(token: string): Promise<TeamMember[]>;
  createTeamMember(data: TeamMemberCreate, token: string): Promise<TeamMember>;
  getGeneralSettings(token: string): Promise<GeneralSettings>;
  updateGeneralSettings(data: Partial<GeneralSettings>, token: string): Promise<GeneralSettings>;
  getProfile(token: string): Promise<SystemUserProfile>;
  getAISettings(token: string): Promise<AISettings>;
  updateAISettings(data: Partial<AISettings>, token: string): Promise<AISettings>;
  getWebhookSettings(token: string): Promise<WebhookSettings>;
  regenerateWebhookSecret(token: string): Promise<WebhookSettings>;
  getBrandSettings(token: string): Promise<BrandSettings>;
};
```

---

## `adminApi` — Admin Operations

```typescript { .api }
import { adminApi } from "@/lib/api/admin";
import type { Tenant } from "@/lib/api/admin";

interface Tenant {
  id: string;
  name: string;
  slug: string;
  can_use_platform_keys: boolean;
  openai_api_key_set: boolean;
  gemini_api_key_set: boolean;
}

const adminApi: {
  getTenants(token: string): Promise<Tenant[]>;
  updateTenantPermissions(token: string, tenantId: string, canUsePlatformKeys: boolean): Promise<any>;
};
```

---

## `assetsApi` — Asset Gallery

```typescript { .api }
import { assetsApi } from "@/lib/api/assets";
import type { Asset } from "@/lib/api/assets";

interface Asset {
  id: string;
  tenant_id: string;
  offer_id?: string | null;
  type: "IMAGE" | "VIDEO" | "AUDIO" | "DOCUMENT";
  filename: string;
  mime_type?: string;
  public_url: string;
  user_description?: string;
  ai_metadata?: Record<string, any>;
  ai_description?: string;
  ai_colors?: string[];
  status: "processing" | "completed" | "failed";
  created_at: string;
}

const assetsApi: {
  upload(token: string, file: File, description?: string, offer_id?: string): Promise<Asset>;
  list(token: string, type?: "IMAGE" | "VIDEO" | "AUDIO" | "DOCUMENT"): Promise<Asset[]>;
  delete(token: string, id: string): Promise<void>;
};
```

---

## `avatarApi` — AI Avatar Management

```typescript { .api }
import { avatarApi } from "@/lib/api/avatar";
import type { Avatar, CreateAvatarDTO } from "@/lib/api/avatar";

interface Avatar {
  id: string;
  name: string;
  is_default: boolean;
  scope: "GLOBAL" | "OFFER_SPECIFIC";
  created_at?: string;
  // Plus all AvatarDefinition fields
  icp_description?: string;
  anti_avatar?: string;
  voice_tone_config?: Record<string, any>;
}

interface CreateAvatarDTO {
  name: string;
  icp_description?: string;   // Ideal Customer Profile description
  anti_avatar?: string;       // Description of who is NOT a fit
  voice_tone_config?: Record<string, any>;
  scope?: "GLOBAL" | "OFFER_SPECIFIC";
}

const avatarApi: {
  listAvatars(token: string, scope?: string): Promise<Avatar[]>;      // default scope: "GLOBAL"
  getAvatar(token: string, id: string): Promise<Avatar>;
  createAvatar(token: string, data: CreateAvatarDTO): Promise<Avatar>;
  updateAvatar(token: string, id: string, data: Partial<CreateAvatarDTO>): Promise<Avatar>;
  deleteAvatar(token: string, id: string): Promise<void>;
  setDefault(token: string, id: string): Promise<Avatar>;
};
```

---

## `availabilityApi` — Availability Schedules

```typescript { .api }
import { availabilityApi } from "@/lib/api/availability";
import type { AvailabilitySchedule, ScheduleUpdate, WeeklySchedule, DaySchedule, TimeRange } from "@/lib/api/availability";

interface TimeRange {
  start: string; // "HH:MM" 24h format
  end: string;   // "HH:MM" 24h format
}

interface DaySchedule {
  active: boolean;
  ranges: TimeRange[];
}

interface WeeklySchedule {
  monday: DaySchedule;
  tuesday: DaySchedule;
  wednesday: DaySchedule;
  thursday: DaySchedule;
  friday: DaySchedule;
  saturday: DaySchedule;
  sunday: DaySchedule;
}

interface AvailabilitySchedule {
  id: string;
  name: string;
  is_default: boolean;
  timezone: string; // IANA timezone
  schedule: WeeklySchedule;
}

type ScheduleUpdate = Partial<AvailabilitySchedule>;

const availabilityApi: {
  listSchedules(token: string): Promise<AvailabilitySchedule[]>;
  createSchedule(schedule: Omit<AvailabilitySchedule, "id">, token: string): Promise<AvailabilitySchedule>;
  updateSchedule(id: string, update: ScheduleUpdate, token: string): Promise<AvailabilitySchedule>;
  deleteSchedule(id: string, token: string): Promise<void>;
};
```

---

## `bookingLinksApi` — Personalized Booking Links

```typescript { .api }
import { bookingLinksApi } from "@/lib/api/booking-links";
import type { BookingLink } from "@/lib/api/booking-links";

interface BookingLink {
  token: string;
  url: string;
  expires_at: string; // ISO 8601 datetime
}

const bookingLinksApi: {
  create(
    payload: { lead_id: string; event_slug: string; expiration_days: number },
    token: string
  ): Promise<BookingLink>;
};
```

---

## `connectionsApi` — Third-Party Integrations

Manages OAuth and API key connections to external services.

```typescript { .api }
import { connectionsApi } from "@/lib/api/connections";
import type {
  ChannelStatusResponse,
  TelegramConnectRequest,
  TestResponse,
  ShopifyConnectRequest,
  ShopifyAuthUrlRequest,
  ShopifyStatusResponse,
  MailerliteConnectRequest,
  MailerliteStatusResponse,
  ManyChatConnectRequest,
  ManyChatStatusResponse,
  GoogleAnalyticsStatusResponse,
  GoogleAnalyticsConfigRequest,
  MetaStatusResponse,
  YoutubeStatusResponse,
} from "@/lib/api/connections";

interface ChannelStatusResponse {
  is_connected: boolean;
  bot_name?: string;
  username?: string;
  config?: Record<string, any>;
}

interface TestResponse {
  status: string;
  message: string;
  data?: any;
}

interface MetaStatusResponse extends ChannelStatusResponse {
  name?: string;
  account_id?: string;
  is_configured?: boolean;
}

interface GoogleAnalyticsStatusResponse extends ChannelStatusResponse {
  account_summary?: any[];
  is_configured?: boolean;
}

interface GoogleAnalyticsConfigRequest {
  client_id: string;
  client_secret: string;
}

interface ShopifyConnectRequest {
  shop_url: string;
  access_token: string;
}

interface ShopifyAuthUrlRequest {
  shop_url: string;
}

interface ShopifyStatusResponse extends ChannelStatusResponse {
  shop_url?: string;
  scope?: string;
}

interface MailerliteConnectRequest {
  api_key: string;
}

interface MailerliteStatusResponse extends ChannelStatusResponse {
  account_info?: Record<string, any>;
}

interface ManyChatConnectRequest {
  api_key: string;
}

interface ManyChatStatusResponse extends ChannelStatusResponse {
  account_info?: Record<string, any>;
}

interface YoutubeStatusResponse extends ChannelStatusResponse {
  is_configured?: boolean;
  channel_id?: string;
  channel_title?: string;
  channel_data?: Record<string, any>;
}

interface TelegramConnectRequest {
  token: string; // Telegram bot token
}

const connectionsApi: {
  // --- Google Calendar ---
  getCalendarStatus(token: string): Promise<any>;
  getGoogleAuthUrl(token: string, redirectUri?: string): Promise<{ url: string; state: string }>;
  connectGoogle(code: string, token: string, redirectUri?: string): Promise<any>;
  disconnectCalendar(token: string): Promise<void>;
  testCalendar(token: string): Promise<TestResponse>;
  listAppointments(start: string, end: string, token: string): Promise<any[]>;
  generateBookingLink(token: string): Promise<{ token: string; url: string }>;

  // --- Gmail ---
  getGmailStatus(token: string): Promise<any>;
  getGmailAuthUrl(token: string, redirectUri?: string): Promise<{ url: string; state: string }>;
  connectGmail(code: string, token: string, redirectUri?: string): Promise<any>;
  disconnectGmail(token: string): Promise<void>;
  testGmail(token: string): Promise<TestResponse>;

  // --- Google Analytics ---
  configureGoogleAnalytics(data: GoogleAnalyticsConfigRequest, token: string): Promise<any>;
  getGoogleAnalyticsStatus(token: string): Promise<GoogleAnalyticsStatusResponse>;
  getGoogleAnalyticsAuthUrl(token: string, redirectUri?: string): Promise<{ url: string; state: string }>;
  connectGoogleAnalytics(code: string, token: string, redirectUri?: string): Promise<any>;
  disconnectGoogleAnalytics(token: string): Promise<void>;
  testGoogleAnalytics(token: string): Promise<TestResponse>;

  // --- Google Workspace (Unified OAuth) ---
  getGoogleWorkspaceAuthUrl(token: string): Promise<{ url: string; state: string }>;
  connectGoogleWorkspace(code: string, token: string): Promise<{ status: string; email: string }>;
  getGoogleWorkspaceStatus(token: string): Promise<{
    is_connected: boolean;
    email?: string;
    services: Record<string, { is_active: boolean; has_credentials: boolean }>;
  }>;
  toggleGoogleWorkspaceService(service: string, isActive: boolean, token: string): Promise<void>;
  disconnectGoogleWorkspace(token: string): Promise<void>;

  // --- Meta (Facebook/Instagram) ---
  getMetaStatus(token: string): Promise<MetaStatusResponse>;
  getMetaAuthUrl(token: string, redirectUri?: string): Promise<{ url: string; state: string }>;
  connectMeta(code: string, token: string, redirectUri?: string): Promise<any>;
  disconnectMeta(token: string): Promise<void>;
  testMeta(token: string): Promise<TestResponse>;

  // --- Telegram ---
  getTelegramStatus(token: string): Promise<ChannelStatusResponse>;
  connectTelegram(data: TelegramConnectRequest, token: string): Promise<any>;
  testTelegram(token: string): Promise<TestResponse>;
  disconnectTelegram(token: string): Promise<void>;

  // --- Shopify ---
  getShopifyStatus(token: string): Promise<ShopifyStatusResponse>;
  generateShopifyAuthUrl(data: ShopifyAuthUrlRequest, token: string): Promise<{ auth_url: string }>;
  connectShopify(data: ShopifyConnectRequest, token: string): Promise<any>;
  testShopify(token: string): Promise<TestResponse>;
  disconnectShopify(token: string): Promise<void>;

  // --- MailerLite ---
  getMailerLiteStatus(token: string): Promise<MailerliteStatusResponse>;
  connectMailerLite(data: MailerliteConnectRequest, token: string): Promise<any>;
  testMailerLite(token: string): Promise<TestResponse>;
  disconnectMailerLite(token: string): Promise<void>;

  // --- ManyChat ---
  getManyChatStatus(token: string): Promise<ManyChatStatusResponse>;
  connectManyChat(data: ManyChatConnectRequest, token: string): Promise<any>;
  testManyChat(token: string): Promise<TestResponse>;
  disconnectManyChat(token: string): Promise<void>;

  // --- YouTube ---
  getYoutubeStatus(token: string): Promise<YoutubeStatusResponse>;
  getYoutubeAuthUrl(token: string, redirectUri?: string): Promise<{ url: string; state: string }>;
  connectYoutube(code: string, token: string, redirectUri?: string): Promise<any>;
  disconnectYoutube(token: string): Promise<void>;
  testYoutube(token: string): Promise<TestResponse>;
  configureYoutube(token: string, clientId: string, clientSecret: string): Promise<any>;
};
```

---

## `crmDashboardApi` — CRM Sales Dashboard

```typescript { .api }
import { crmDashboardApi } from "@/lib/api/crm-dashboard-api";
import type { PipelineItem, AgendaItem, TickerItem } from "@/lib/api/crm-dashboard-api";

interface PipelineItem {
  id: string;
  full_name: string | null;
  intent_score: number;       // 0–100 lead scoring
  temperature: string;        // e.g. "hot", "warm", "cold"
  last_interaction: string | null; // ISO datetime
  channel: string | null;     // e.g. "whatsapp", "email"
  avatar_url?: string | null;
}

interface AgendaItem {
  id: string;
  summary: string;
  start_time: string;   // ISO datetime
  end_time: string;     // ISO datetime
  status: string;
  lead_name?: string | null;
  meeting_link?: string | null;
}

interface TickerItem {
  id: string;
  amount: number;
  currency: string;
  customer_name?: string | null;
  stage: string;
  occurred_at: string;  // ISO datetime
  offer_name?: string | null;
}

const crmDashboardApi: {
  /** Get hot leads pipeline, filtered by minimum intent score */
  getPipeline(token: string, minScore?: number, limit?: number): Promise<PipelineItem[]>;
  /** Get upcoming agenda items for today or this week */
  getAgenda(token: string, range?: "today" | "week"): Promise<AgendaItem[]>;
  /** Get sales activity ticker (returns [] on error) */
  getTicker(token: string, range?: "today" | "week" | "30d" | "all"): Promise<TickerItem[]>;
};
```

---

## `eventTypesApi` — Scheduling Event Types

```typescript { .api }
import { eventTypesApi } from "@/lib/api/event-types";
import type { EventType, EventTypeUpdate, SchedulingLimits, BookingConfig } from "@/lib/api/event-types";

interface SchedulingLimits {
  max_advance_days: number;
  min_advance_hours: number;
}

interface BookingConfig {
  buffer_minutes: number;
  max_per_day: number | null;
  guest_permissions: string[];
}

interface EventType {
  id: string;
  slug: string;
  title: string;
  description?: string;
  duration_minutes: number;
  is_active: boolean;
  scheduling_limits: SchedulingLimits;
  booking_config: BookingConfig;
  // Plus additional fields
}

type EventTypeUpdate = Partial<EventType>;

const eventTypesApi: {
  listEventTypes(token: string): Promise<EventType[]>;
  createEventType(data: Omit<EventType, "id">, token: string): Promise<EventType>;
  updateEventType(id: string, data: EventTypeUpdate, token: string): Promise<EventType>;
  deleteEventType(id: string, token: string): Promise<void>;
};
```

---

## `leadsApi` — CRM Leads

```typescript { .api }
import { leadsApi } from "@/lib/api/leads";
import type { Lead } from "@/lib/api/leads";

interface Lead {
  id: string;
  full_name: string;
  email: string;
  phone: string;
}

const leadsApi: {
  search(q: string, token: string): Promise<Lead[]>;
};
```

---

## `offerGalleryApi` — Offer Image Gallery

```typescript { .api }
import { offerGalleryApi } from "@/lib/api/offer-gallery";
import type { OfferGalleryImage } from "@/lib/api/offer-gallery";

interface OfferGalleryImage {
  id: string;
  tenant_id: string;
  offer_id: string;
  public_url: string;
  user_description: string;
  ai_description: string;
  ai_colors: string[];      // hex color strings extracted by AI
  status: "processing" | "completed" | "failed";
  created_at: string;       // ISO datetime
}

const offerGalleryApi: {
  upload(token: string, offerId: string, file: File, description: string): Promise<OfferGalleryImage>;
  list(token: string, offerId: string): Promise<OfferGalleryImage[]>;
  delete(token: string, offerId: string, imageId: string): Promise<void>;
};
```

---

## `publicApi` — Public Booking (No Auth Required)

```typescript { .api }
import { publicApi } from "@/lib/api/public";
import type {
  LinkResolveResponse,
  BookingLinkResolveResponse,
  Slot,
  BookingRequest,
  EventTypeResolveResponse,
} from "@/lib/api/public";

interface Slot {
  start: string; // ISO datetime
  end: string;   // ISO datetime
}

interface BookingRequest {
  // booking form data
  name: string;
  email: string;
  start_time: string;
  timezone: string;
  notes?: string;
}

interface LinkResolveResponse {
  valid: boolean;
  type: string;
  tenant_name: string;
  params: Record<string, any>;
}

interface BookingLinkResolveResponse {
  // booking link metadata with lead data
  valid: boolean;
  lead?: {
    id: string;
    full_name: string;
    email: string;
  };
  event_type?: EventTypeResolveResponse;
}

interface EventTypeResolveResponse {
  title: string;
  duration_minutes: number;
  description?: string;
  slug: string;
  tenant_slug: string;
}

const publicApi: {
  resolveLink(token: string): Promise<LinkResolveResponse>;
  resolveBookingLink(token: string): Promise<BookingLinkResolveResponse>;
  getSlots(token: string, date?: string): Promise<Slot[]>;
  bookMeeting(token: string, data: BookingRequest): Promise<any>;
  resolveEventType(tenantSlug: string, eventSlug: string): Promise<EventTypeResolveResponse>;
  getEventTypeSlots(tenantSlug: string, eventSlug: string, date?: string): Promise<Slot[]>;
  bookEventType(tenantSlug: string, eventSlug: string, data: BookingRequest): Promise<any>;
};
```

---

## `whatsappApi` — WhatsApp Integration

```typescript { .api }
import { whatsappApi } from "@/lib/api/whatsapp";
import type { WhatsAppDashboardStatus, WhatsAppProviderStatus, WhatsAppQR } from "@/lib/api/whatsapp";

interface WhatsAppProviderStatus {
  status: "connected" | "disconnected" | "connecting" | "error";
  profile?: {
    first_name?: string;
    remote_jid?: string;
    [key: string]: any;
  };
  detail?: string;
}

interface WhatsAppDashboardStatus {
  evolution: WhatsAppProviderStatus;
  meta: WhatsAppProviderStatus;
}

interface WhatsAppQR {
  code?: string;       // base64 encoded QR image
  pairingCode?: string;
  status?: string;
  count?: number;
  detail?: string;
}

const whatsappApi: {
  getStatus(token: string): Promise<WhatsAppDashboardStatus>;
  createSession(token: string, provider?: "evolution" | "meta"): Promise<void>;
  getQR(token: string): Promise<WhatsAppQR>;
  disconnect(token: string, provider?: "evolution" | "meta"): Promise<void>;
};
```

---

## `aiActionsApi` — AI-Powered Actions

```typescript { .api }
import { aiActionsApi } from "@/lib/api/ai-actions";
import type {
  OfferPsychologyPayload,
  OfferPsychologyResult,
  BrandExtractPayload,
  FullBrandExtractInput,
} from "@/lib/api/ai-actions";

interface BrandExtractPayload {
  url?: string;
  text?: string;
  // Additional extraction options
}

// FullBrandExtractInput can be FormData (for file upload) or a plain object
type FullBrandExtractInput = FormData | BrandExtractPayload;

interface OfferPsychologyPayload {
  offer_id: string;
  // Additional psychology generation params
}

interface OfferPsychologyResult {
  // Generated psychology content
  [key: string]: any;
}

const aiActionsApi: {
  /** Extract brand identity from URL or text */
  extractBrandIdentity(data: BrandExtractPayload, token: string): Promise<any>;
  /** Full brand extraction (supports file upload via FormData) */
  extractFullBrand(data: FullBrandExtractInput, token: string): Promise<any>;
  /** Generate psychological framing for an offer */
  generateOfferPsychology(data: OfferPsychologyPayload, token: string): Promise<OfferPsychologyResult>;
};
```
