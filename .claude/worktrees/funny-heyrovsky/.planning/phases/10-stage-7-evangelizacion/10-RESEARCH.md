# Phase 10: Stage 7 Evangelizacion - Research

**Researched:** 2026-03-16
**Domain:** Viral growth metrics, NPS surveys, referral tracking, WhatsApp conversational surveys
**Confidence:** HIGH (established codebase patterns) / MEDIUM (NPS & WhatsApp survey design)

## Summary

Phase 10 builds the Evangelization detail panel (Stage 7) of the Growth Studio metrics dashboard. This phase is unique among the 8 stages because it introduces **new domain models** (ReferralCode, NpsSurvey, NpsResponse) and **write operations** (promote evangelist, trigger survey, submit NPS response) in addition to the standard read-only metrics panel pattern established in Phases 4-9. The backend endpoint `/metrics/evangelization` follows the exact same MetricsService + DTO + cache pattern, but new CRM models and services are required to support referral code management, NPS survey lifecycle, and evangelist promotion workflow.

The frontend follows the established detail panel pattern (EvangelizationDetail.tsx matching AdoptionDetail/ExpansionDetail structure) with the addition of interactive elements (promote button, survey trigger dialog) that require mutation hooks alongside the standard query hook. The UI-SPEC is already approved and provides precise component contracts.

Research into NPS survey best practices, WhatsApp conversational survey patterns, K-Factor calculation, audio testimonial capture, and Shopify discount code extraction confirms all features are achievable with the existing stack. No new external libraries are needed -- only new API integrations (Shopify Admin API for discount code read, WhatsApp Business API interactive messages for conversational NPS).

**Primary recommendation:** Follow the established Phase 5-9 pattern exactly for the metrics panel, layer new CRM models (ReferralCode, NpsSurvey, NpsResponse) with Alembic migrations, and implement NPS as a 3-question conversational flow (score + open feedback + testimonial consent) with channel-agnostic delivery via universal link + WhatsApp interactive buttons.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Referral Tracking (Multi-Source)**: Combined tracking: Shopify coupon codes (high confidence) + UTM parameters (broader reach). K-Factor uses combined data. Source-agnostic design: ReferralCode model supports `source` field (internal, shopify, external)
- **Referral Code Management**: Auto-generated codes per customer. Owner decides WHO gets a referral code (manual assignment). Shopify extraction read-only (Admin API read, do NOT push codes). ReferralCode model in CRM module
- **Panel Structure (Two Groups)**: Group 1 Referidos (referral conversions, revenue, top referrer cards) + Group 2 Reputacion (NPS score, promoter count, UGC/testimonials). Evangelist cards (not rows). Candidatos a Evangelista section for NPS >= 9 customers
- **Header KPIs (3+2)**: Primary: K-Factor | Referidos Convertidos | NPS Score. Secondary: Revenue Referido | Evangelistas Activos
- **MiniFunnel**: Clientes Activos (N) -> Evangelistas (M) = X%
- **NPS Survey System**: Channel-agnostic delivery. Two initial mechanisms: universal link + WhatsApp conversational native. Owner triggers surveys per offer or per customer. Must include testimonial capture (written or audio). Consent mechanism for public use
- **NPS scoring on CRM profile**: Each customer's NPS response mapped to their profile
- **Evangelist Triggers**: NPS >= 9 auto-suggests in Candidatos section. Owner manually promotes. Permanent status (once EVANGELIST, always EVANGELIST unless CHURNED)
- **Bottleneck Visualization**: Low K-Factor + Low NPS response rate

### Claude's Discretion
- Evangelist card component design (spacing, shadows, badge styling)
- Referral code format (alphanumeric, length, prefix)
- NPS survey form visual design (web page for universal link)
- WhatsApp interactive message structure (buttons vs list vs quick replies)
- Bottleneck threshold calibration
- UGC display format in Reputacion group
- Error/empty states for evangelization-specific scenarios
- K-Factor formula implementation details
- Audio testimonial storage approach

### Deferred Ideas (OUT OF SCOPE)
- Full CRM profile edit for provenance
- Push referral codes TO Shopify
- WooCommerce coupon extraction
- Sales Agent as survey delivery channel
- Social media mention tracking as UGC
- Automated survey scheduling
- Revenue trend indicators (Phase 11)
- Configurable bottleneck thresholds per tenant
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| EVA-01 | Detail panel showing referral conversions, UGC count, and K-Factor | Established detail panel pattern from Phases 5-9, UI-SPEC approved, two-group layout with evangelist cards and NPS summary |
| EVA-02 | `/metrics/evangelization` endpoint tracking referral-attributed sales and evangelist profiles | MetricsService pattern with evangelization_repository.py querying SaleModel + ReferralCodeModel + CustomerProfileModel |
| EVA-03 | K-Factor calculation: (referrals sent per customer) x (conversion rate of referrals) | Standard viral coefficient formula confirmed by multiple sources. K = avg_invites_per_user x conversion_rate |
| EVA-04 | NPS integration via Mailerlite surveys -- identify promoters (score 9-10) as potential evangelists | NPS model stores responses directly in CRM. Promoter detection via score >= 9 query. Channel-agnostic delivery (universal link + WhatsApp) |
</phase_requirements>

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | Current | API endpoints for evangelization metrics + survey management | Existing project stack |
| SQLAlchemy 2.0 | Current | Async ORM for new CRM models (ReferralCode, NpsSurvey, NpsResponse) | Existing project stack |
| Alembic | Current | Database migrations for new tables | Existing project stack |
| Pydantic v2 | Current | DTOs (EvangelizationDetailDTO, NpsSurveyDTO, etc.) | Existing project stack |
| React 18 + Next.js 14 | Current | Frontend detail panel components | Existing project stack |
| @tanstack/react-query | Current | Data fetching hooks (useEvangelizationDetail) | Existing project stack |
| shadcn/ui | Current | Card, Badge, Button, Dialog, Skeleton, Tooltip components | Existing project stack, UI-SPEC approved |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Redis (redis-py) | Current | MetricsCache with 300s TTL for evangelization stage | Cache evangelization metrics (same as other stages) |
| httpx | Current | Shopify Admin API calls for discount code extraction | Read discount codes from Shopify via existing ShopifyConnector pattern |
| sonner | Current | Toast notifications for promote/survey actions | Already in project for user feedback |

### No New Libraries Required
This phase requires NO new npm or pip packages. All functionality is achievable with the existing stack.

**Installation:** None needed -- all dependencies already in project.

## Architecture Patterns

### Recommended Project Structure

```
backend/src/modules/
├── analytics/
│   ├── api/metrics.py                          # Add GET /metrics/evangelization endpoint
│   ├── application/
│   │   ├── dto/evangelization_dto.py            # NEW: EvangelizationDetailDTO + sub-DTOs
│   │   └── services/
│   │       ├── metrics_service.py               # Add get_evangelization_metrics() method
│   │       └── channel_registry.py              # Add "evangelization" to STAGE_CHANNEL_MAP
│   └── infrastructure/
│       └── repositories/evangelization_repository.py  # NEW: CRM queries for referral + NPS data
├── crm/
│   ├── api/
│   │   ├── referral.py                          # NEW: POST /referrals/promote, GET /referrals
│   │   └── nps.py                               # NEW: POST /nps/surveys, GET /nps/survey/:token
│   ├── application/services/
│   │   ├── referral_service.py                  # NEW: code generation, Shopify extraction
│   │   ├── nps_service.py                       # NEW: survey creation, response handling
│   │   └── lifecycle_service.py                 # ADD: evangelist promotion logic
│   ├── domain/enums.py                          # LifecycleStage.EVANGELIST already exists
│   └── infrastructure/models/
│       ├── referral_code_model.py               # NEW: ReferralCodeModel
│       └── nps_models.py                        # NEW: NpsSurveyModel, NpsResponseModel
frontend/src/features/marketing-studio/
├── components/metrics-dashboard/
│   ├── detail-panels/EvangelizationDetail.tsx   # NEW: Main panel orchestrator
│   └── channel-widgets/
│       ├── EvangelistCard.tsx                   # NEW: Per-evangelist referral card
│       ├── NpsSummaryCard.tsx                   # NEW: NPS score + bar breakdown
│       └── CandidatosBanner.tsx                 # NEW: NPS >= 9 promote section
├── hooks/
│   ├── useEvangelizationDetail.ts               # NEW: Query hook
│   └── useEvangelizationMutations.ts            # NEW: Mutation hooks (promote, survey)
├── types/metrics.ts                             # ADD: EvangelizationDetail types
├── api/metrics-api.ts                           # ADD: getEvangelizationDetail + mutations
└── api/metrics-mock-data.ts                     # ADD: MOCK_EVANGELIZATION_DETAIL
```

### Pattern 1: Metrics Panel (Established Phase 5-9 Pattern)
**What:** Every stage detail panel follows the same architecture: DTO -> Repository -> Service -> API -> Hook -> Component
**When to use:** The `/metrics/evangelization` endpoint and `EvangelizationDetail.tsx`

Backend flow:
```python
# 1. DTO (evangelization_dto.py)
class EvangelizationHeaderKpisDTO(BaseModel):
    k_factor: float
    referral_conversions: int
    nps_score: Optional[float] = None
    referral_revenue: float
    referral_revenue_usd: Optional[float] = None
    currency: str
    active_evangelists: int

class EvangelistDTO(BaseModel):
    customer_id: str
    full_name: str
    referral_code: str
    referrals_sent: int
    conversions: int
    revenue_attributed: float
    currency: str
    usd_revenue: Optional[float] = None
    is_active: bool

class NpsSummaryDTO(BaseModel):
    nps_score: Optional[float] = None  # -100 to 100 scale (standard NPS) or 0-10 simplified
    promoter_count: int    # 9-10
    passive_count: int     # 7-8
    detractor_count: int   # 0-6
    total_responses: int
    surveys_sent: int
    response_rate_pct: float

class CandidatoDTO(BaseModel):
    customer_id: str
    full_name: str
    nps_score: int
    responded_at: Optional[str] = None

class EvangelizationDetailDTO(BaseModel):
    header_kpis: EvangelizationHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # Reuse from capture_dto
    referidos: List[EvangelistDTO]
    candidatos: List[CandidatoDTO]
    nps_summary: NpsSummaryDTO
    ugc_count: int  # total testimonials collected
    ugc_written: int
    ugc_audio: int
    bottlenecks: List[BottleneckDTO] = []  # Reuse from opportunity_dto
    period: str = "last_30_days"
    last_updated: Optional[str] = None

# 2. API endpoint (metrics.py)
@router.get("/evangelization", response_model=EvangelizationDetailDTO)
async def get_evangelization_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    offer_port = OfferReadPortImpl(db)
    service = MetricsService(db, cache=cache, connection_port=connection_port, offer_port=offer_port)
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=30)
    return await service.get_evangelization_metrics(user.tenant_id, start_date, now)
```

Frontend flow:
```typescript
// Hook (useEvangelizationDetail.ts) - exact pattern from useAdoptionDetail
export function useEvangelizationDetail() {
  const { getToken } = useAuth();
  return useQuery<EvangelizationDetail>({
    queryKey: ['evangelization-detail'],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.getEvangelizationDetail(token);
    },
    staleTime: 1000 * 60 * 5,
  });
}
```

### Pattern 2: New CRM Models (ReferralCode + NPS)
**What:** New SQLAlchemy models in the CRM module for referral codes and NPS surveys
**When to use:** Storing referral attribution data and NPS survey responses

```python
# referral_code_model.py
class ReferralCodeModel(Base):
    __tablename__ = "referral_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer_profiles.id"), nullable=False, index=True)
    code = Column(String, nullable=False, unique=True, index=True)
    source = Column(String, default="internal")  # internal | shopify | external
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# nps_models.py
class NpsSurveyModel(Base):
    __tablename__ = "nps_surveys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token = Column(String, nullable=False, unique=True, index=True)  # unique survey link token
    offer_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)  # null = individual
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer_profiles.id"), nullable=True)
    delivery_channel = Column(String, default="universal_link")  # universal_link | whatsapp
    status = Column(String, default="pending")  # pending | sent | responded | expired
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

class NpsResponseModel(Base):
    __tablename__ = "nps_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    survey_id = Column(UUID(as_uuid=True), ForeignKey("nps_surveys.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer_profiles.id"), nullable=False, index=True)
    score = Column(Integer, nullable=False)  # 0-10
    feedback_text = Column(String, nullable=True)  # open-ended response
    testimonial_text = Column(String, nullable=True)  # written testimonial
    testimonial_audio_url = Column(String, nullable=True)  # S3/storage URL for audio
    consent_public_use = Column(Boolean, default=False)  # consent to use publicly
    responded_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Pattern 3: Mutation Hooks (New for Phase 10)
**What:** Phase 10 introduces write operations (promote evangelist, trigger survey) alongside read-only metrics
**When to use:** Interactive CTA buttons in the evangelization panel

```typescript
// useEvangelizationMutations.ts
export function usePromoteEvangelist() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (customerId: string) => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      // POST /api/v1/crm/referrals/promote
      return metricsApi.promoteToEvangelist(token, customerId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evangelization-detail'] });
      toast.success('Cliente promovido a Evangelista');
    },
  });
}
```

### Pattern 4: K-Factor Calculation
**What:** Viral coefficient computed from referral data
**Formula:** K = (total_referrals_sent / total_customers_with_codes) x (referral_conversions / total_referrals_sent)
**Simplified:** K = referral_conversions / total_customers_with_codes
**When to use:** Header KPI and bottleneck evaluation

```python
# In evangelization_repository.py
def calculate_k_factor(self, tenant_id: UUID, start_date, end_date) -> float:
    """K-Factor = avg referrals per evangelist x conversion rate of referrals."""
    # Count active evangelists with referral codes
    evangelists_with_codes = self._count_active_referral_codes(tenant_id)
    if evangelists_with_codes == 0:
        return 0.0

    # Count total referrals sent (sales with referral attribution)
    total_referrals_sent = self._count_referrals_sent(tenant_id, start_date, end_date)
    # Count referral conversions (completed sales with referral source)
    referral_conversions = self._count_referral_conversions(tenant_id, start_date, end_date)

    if total_referrals_sent == 0:
        return 0.0

    avg_referrals_per_evangelist = total_referrals_sent / evangelists_with_codes
    conversion_rate = referral_conversions / total_referrals_sent

    return round(avg_referrals_per_evangelist * conversion_rate, 2)
```

### Anti-Patterns to Avoid
- **Direct ORM joins across modules**: Use ports/adapters pattern (ConnectionPort, OfferReadPort) for cross-module data access. Evangelization repository queries CRM models directly (same module).
- **Hardcoding referral sources**: Use the `source` field on ReferralCodeModel to keep referral tracking platform-agnostic.
- **NPS calculation on the fly without caching**: Cache NPS aggregations with other evangelization metrics (300s TTL).
- **Mixing survey delivery logic with survey content**: Keep NPS survey creation separate from delivery channel (universal link vs WhatsApp). The NpsSurveyModel stores the survey; delivery is handled by separate adapters.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Referral code generation | Custom random string generator | `secrets.token_urlsafe(6)` with prefix | Cryptographically secure, avoids collisions |
| NPS score calculation | Manual averaging | Standard NPS formula: `((promoters - detractors) / total_responses) * 100` | Industry standard, well-defined |
| Dual currency formatting | Custom formatter | `Intl.NumberFormat` with es-MX/en-US (already in project) | Proven from Phase 8-9 |
| Survey token generation | UUID exposed in URL | `secrets.token_urlsafe(32)` | URL-safe, non-guessable |
| Proportional bar (NPS breakdown) | Canvas/SVG chart | CSS proportional widths (same as HealthBar in Phase 9) | Consistent with existing pattern, no chart library needed |
| Toast notifications | Custom toast system | sonner (already in project) | Consistent with existing UI |

**Key insight:** This phase's novelty is the NPS survey system and referral models, not the metrics panel itself. The panel follows an established 6-phase pattern. Focus implementation effort on the new CRM models and survey lifecycle.

## Common Pitfalls

### Pitfall 1: Referral Attribution Ambiguity
**What goes wrong:** Sales with referral codes are not properly linked to the referrer customer, leading to inaccurate K-Factor.
**Why it happens:** SaleModel.source field is a free-text string. Need a structured way to track referral attribution.
**How to avoid:** Add `referral_code_id` or store referral code in `metadata_info` JSONB on SaleModel. Query referral attributions via `metadata_info->>'referral_code'` or via a separate `referral_attributions` table.
**Warning signs:** K-Factor always shows 0.0 despite having referral codes and sales.

### Pitfall 2: NPS Score Scale Confusion
**What goes wrong:** Mixing up the 0-10 individual response scale with the -100 to +100 NPS score.
**Why it happens:** "NPS Score" means different things at individual vs aggregate level.
**How to avoid:** Individual responses: 0-10 (stored as `score` on NpsResponseModel). Aggregate NPS: `((promoters - detractors) / total) * 100` yields -100 to +100. Display aggregate as 0-10 average in the header KPI (simpler for micro-business owners) with the standard NPS in tooltip.
**Warning signs:** NPS showing as negative number confuses non-technical business owners.

### Pitfall 3: Evangelist Promotion Without Referral Code
**What goes wrong:** Promoting a customer to EVANGELIST lifecycle stage but forgetting to auto-generate a referral code.
**Why it happens:** Promotion and code generation are separate operations.
**How to avoid:** The `promote_to_evangelist` service method MUST atomically: (1) transition lifecycle to EVANGELIST, (2) generate referral code, (3) return both in response.
**Warning signs:** Evangelist count in header doesn't match referral code count.

### Pitfall 4: WhatsApp Template Approval Lag
**What goes wrong:** WhatsApp Business API requires pre-approved message templates. Survey messages won't send without approval.
**Why it happens:** Meta reviews all WhatsApp templates before allowing sending (can take hours to days).
**How to avoid:** Design the WhatsApp NPS template with standard structure (text body + quick reply buttons for score). Submit template for approval early. Universal link works immediately as fallback.
**Warning signs:** WhatsApp delivery fails with "template not approved" error.

### Pitfall 5: Alembic Migration for New Tables
**What goes wrong:** Migration conflicts or missing imports when adding 3 new tables (referral_codes, nps_surveys, nps_responses).
**Why it happens:** Phase 5 already encountered duplicate revision ID issues.
**How to avoid:** Create migration manually if auto-generation fails. Verify revision chain with `alembic history`. Test migration with `alembic upgrade head` in Docker container.
**Warning signs:** Alembic `heads` shows multiple heads (branched history).

### Pitfall 6: Empty Panel State Management
**What goes wrong:** Panel shows loading spinner forever or crashes when no evangelists, no NPS data, or no referral codes exist.
**Why it happens:** Multiple partial data states (evangelists exist but no NPS, NPS exists but no evangelists, etc.)
**How to avoid:** UI-SPEC defines 4 distinct states: loading, error, empty (no data at all), partial (some data). Handle each explicitly in EvangelizationDetail.tsx.
**Warning signs:** White screen or infinite spinner on new tenants.

## Code Examples

### K-Factor Calculation (Backend)
```python
# Source: Standard viral coefficient formula
# K = i * c where i = avg invitations per user, c = conversion rate
def calculate_k_factor(
    evangelists_count: int,
    total_referrals_sent: int,
    referral_conversions: int,
) -> float:
    if evangelists_count == 0 or total_referrals_sent == 0:
        return 0.0
    i = total_referrals_sent / evangelists_count  # avg invitations per evangelist
    c = referral_conversions / total_referrals_sent  # conversion rate
    return round(i * c, 2)
```

### NPS Score Calculation (Backend)
```python
# Source: Standard NPS formula
def calculate_nps_score(scores: list[int]) -> Optional[float]:
    """Calculate NPS from list of 0-10 scores.
    Returns average score (0-10) for display simplicity.
    Standard NPS (-100 to +100) available via calculate_standard_nps().
    """
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)

def calculate_standard_nps(scores: list[int]) -> Optional[float]:
    """Standard NPS = ((promoters - detractors) / total) * 100."""
    if not scores:
        return None
    total = len(scores)
    promoters = sum(1 for s in scores if s >= 9)
    detractors = sum(1 for s in scores if s <= 6)
    return round(((promoters - detractors) / total) * 100, 1)

def categorize_nps(score: int) -> str:
    """Categorize individual NPS response."""
    if score >= 9:
        return "promoter"
    elif score >= 7:
        return "passive"
    return "detractor"
```

### Referral Code Generation (Backend)
```python
# Source: Python secrets module for URL-safe tokens
import secrets

def generate_referral_code(prefix: str = "REF") -> str:
    """Generate unique referral code: REF-XXXXXX (6 alphanumeric chars)."""
    suffix = secrets.token_urlsafe(4).replace("-", "").replace("_", "")[:6].upper()
    return f"{prefix}-{suffix}"
```

### Shopify Discount Code Extraction (Backend)
```python
# Source: Shopify Admin REST API
# Endpoint: GET /admin/api/2026-01/price_rules/{id}/discount_codes.json
# Or GraphQL: codeDiscountNodes query
async def extract_shopify_discount_codes(
    shop_domain: str, access_token: str
) -> list[dict]:
    """Read existing discount codes from Shopify (read-only)."""
    async with httpx.AsyncClient() as client:
        # Use GraphQL for simpler pagination
        query = """
        {
            codeDiscountNodes(first: 50) {
                nodes {
                    id
                    codeDiscount {
                        ... on DiscountCodeBasic {
                            title
                            codes(first: 10) {
                                nodes { code }
                            }
                            status
                        }
                    }
                }
            }
        }
        """
        response = await client.post(
            f"https://{shop_domain}/admin/api/2026-01/graphql.json",
            headers={
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json",
            },
            json={"query": query},
        )
        data = response.json()
        # Extract codes from response
        return _parse_discount_nodes(data)
```

### WhatsApp Interactive NPS Survey Message Structure
```python
# Source: WhatsApp Business API interactive message template
# Maximum 3 quick reply buttons per template (WhatsApp limitation for quick replies)
# For 0-10 NPS scale, use List Message (up to 10 items in a section)

WHATSAPP_NPS_TEMPLATE = {
    "type": "interactive",
    "interactive": {
        "type": "list",
        "header": {"type": "text", "text": "Encuesta de Satisfaccion"},
        "body": {
            "text": "Hola {customer_name}! Nos encantaria saber tu opinion sobre {offer_name}. Del 0 al 10, que tan probable es que nos recomiendes?"
        },
        "footer": {"text": "Tu respuesta nos ayuda a mejorar"},
        "action": {
            "button": "Seleccionar calificacion",
            "sections": [
                {
                    "title": "Calificacion",
                    "rows": [
                        {"id": "nps_10", "title": "10 - Excelente"},
                        {"id": "nps_9", "title": "9 - Muy bueno"},
                        {"id": "nps_8", "title": "8 - Bueno"},
                        {"id": "nps_7", "title": "7 - Regular"},
                        {"id": "nps_6", "title": "6 - Podria mejorar"},
                        {"id": "nps_5", "title": "5"},
                        {"id": "nps_4", "title": "4"},
                        {"id": "nps_3", "title": "3"},
                        {"id": "nps_2", "title": "2"},
                        {"id": "nps_1", "title": "1"},
                        # Note: WhatsApp list sections support up to 10 rows
                        # Score 0 handled via follow-up or text response
                    ],
                }
            ],
        },
    },
}
```

### NPS Survey Form Fields (Universal Link)
```
Based on SurveySparrow conversational pattern + Delighted simplicity:

Question 1 (Required): NPS Score
  "Del 0 al 10, que tan probable es que nos recomiendes a un amigo?"
  [0] [1] [2] [3] [4] [5] [6] [7] [8] [9] [10]
  Visual: Clickable number buttons, promoter range (9-10) in green

Question 2 (Optional): Open Feedback
  "Que es lo que mas te gusta de nuestro servicio?" (for 9-10)
  "Como podriamos mejorar?" (for 0-8)
  [Text area, max 500 chars]

Question 3 (Optional): Testimonial
  "Te gustaria compartir unas palabras que podamos usar en nuestra web?"
  [Text area for written testimonial]
  OR
  [Record Audio button] - uses MediaRecorder API for browser recording

  Consent checkbox: "Autorizo el uso de mi testimonio en la web y materiales de marketing de {business_name}"
```

### Audio Testimonial Capture Approach
```
Recommended: Browser MediaRecorder API for universal link surveys

- No external library needed
- MediaRecorder API supported in all modern browsers (Chrome, Firefox, Safari, Edge)
- Record as webm/opus (default) or mp3
- Upload to existing file storage (S3 or equivalent)
- Store URL in NpsResponseModel.testimonial_audio_url
- Max duration: 60 seconds (enforced client-side)
- Fallback: text-only testimonial if MediaRecorder not supported

For WhatsApp: WhatsApp natively supports voice messages
- After NPS score selection, prompt: "Si quieres, envianos un audio con tu testimonio"
- Customer sends voice note naturally
- Capture via WhatsApp webhook -> store audio URL
```

### UGC Definition for Micro-Business Context
```
What counts as UGC in this system (Phase 10 scope):

1. Written testimonials from NPS surveys (consent_public_use = true)
2. Audio testimonials from NPS surveys (consent_public_use = true)

Future (deferred):
- Social media mentions (requires social listening)
- Google/Yelp reviews (requires API integration)
- Customer photos/videos (requires upload infrastructure)

Tracking: UGC count = count of NpsResponseModel where
  (testimonial_text IS NOT NULL OR testimonial_audio_url IS NOT NULL)
  AND consent_public_use = true
```

## Bottleneck Threshold Calibration

Based on research into K-Factor benchmarks and NPS response rates:

| Metric | Warning Threshold | Critical Threshold | Source |
|--------|-------------------|-------------------|--------|
| K-Factor | < 1.0 | < 0.5 | Industry standard: K >= 1.0 = viral growth. Most businesses 0.1-0.5 |
| NPS Response Rate | < 30% | < 15% | SurveySparrow/Delighted benchmarks: 30-50% is healthy for WhatsApp |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Email-only NPS surveys | Multi-channel (WhatsApp + universal link) | 2024-2025 | WhatsApp achieves 98% open rate vs 21% email |
| Separate NPS tool (Delighted, etc.) | Built-in NPS with CRM integration | 2025 (Delighted shutting down) | NPS score on customer profile enables service differentiation |
| Manual testimonial collection | Integrated in NPS flow | 2024-2025 | Captures testimonials at peak satisfaction moment (score 9-10) |
| REST API for Shopify discounts | GraphQL Admin API | 2024+ | Shopify pushing GraphQL; REST still supported but pagination easier with GraphQL |

**Deprecated/outdated:**
- Delighted (acquired by Qualtrics, shutting down) -- do not reference as integration target
- Shopify REST PriceRule API -- migrating to GraphQL `codeDiscountNodes`

## Open Questions

1. **Referral Attribution on SaleModel**
   - What we know: SaleModel has `source` field (String) and `metadata_info` (JSONB)
   - What's unclear: Whether to add a `referral_code_id` FK column or use `metadata_info->>'referral_code'` for attribution
   - Recommendation: Use `metadata_info` JSONB to avoid migration on existing table. Store `{"referral_code": "REF-XXXX", "referrer_id": "uuid"}` in metadata_info. This is consistent with how Phase 9 stores `event_name` in metadata_info.

2. **NPS Display Scale**
   - What we know: Standard NPS is -100 to +100. Individual scores are 0-10.
   - What's unclear: Whether to show standard NPS or simplified 0-10 average to micro-business owners
   - Recommendation: Show 0-10 average in header KPI (intuitive for target audience). Show standard NPS in tooltip for power users. UI-SPEC says "NPS Score" format is "X.X (1 decimal, 0-10 scale)" confirming 0-10 display.

3. **WhatsApp NPS Implementation Timing**
   - What we know: WhatsApp integration requires template approval and webhook handling
   - What's unclear: Whether WhatsApp delivery should be fully functional in Phase 10 or stubbed
   - Recommendation: Implement universal link fully. WhatsApp delivery as model + API endpoint (ready for integration) but with "Proximamente" badge if WhatsApp connection not active. The WhatsApp interactive message structure is documented above for when the Sales Agent channel becomes available.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (inside Docker container) |
| Config file | `backend/pytest.ini` or `pyproject.toml` |
| Quick run command | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/analytics/ -x -q` |
| Full suite command | `docker exec -t visionarias_brain_dev pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EVA-01 | Evangelization panel renders with correct groups and KPIs | integration | Frontend manual verification (component renders) | -- Wave 0 |
| EVA-02 | `/metrics/evangelization` returns correct DTO with referral + NPS data | unit | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/analytics/test_evangelization_metrics.py -x` | -- Wave 0 |
| EVA-03 | K-Factor calculated correctly from referral data | unit | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/analytics/test_k_factor.py -x` | -- Wave 0 |
| EVA-04 | NPS responses stored and promoters identified for evangelist candidacy | unit | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/crm/test_nps_service.py -x` | -- Wave 0 |

### Sampling Rate
- **Per task commit:** `docker exec -t visionarias_brain_dev pytest backend/tests/modules/analytics/ -x -q`
- **Per wave merge:** `docker exec -t visionarias_brain_dev pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/modules/analytics/test_evangelization_metrics.py` -- covers EVA-02, EVA-03
- [ ] `backend/tests/modules/analytics/test_k_factor.py` -- covers EVA-03 specifically
- [ ] `backend/tests/modules/crm/test_nps_service.py` -- covers EVA-04
- [ ] `backend/tests/modules/crm/test_referral_service.py` -- covers referral code generation and Shopify extraction

## Sources

### Primary (HIGH confidence)
- Existing codebase: `analytics/application/dto/expansion_dto.py`, `adoption_dto.py`, `sales_dto.py` -- established DTO patterns
- Existing codebase: `analytics/api/metrics.py` -- all endpoint patterns
- Existing codebase: `crm/domain/enums.py` -- LifecycleStage.EVANGELIST already defined
- Existing codebase: `crm/application/services/lifecycle_service.py` -- promotion logic foundation
- Existing codebase: `connections/infrastructure/marketing_connectors/shopify.py` -- Shopify connector with API version 2026-01
- UI-SPEC: `.planning/phases/10-stage-7-evangelizacion/10-UI-SPEC.md` -- approved visual contract

### Secondary (MEDIUM confidence)
- [K-Factor formula](https://www.wallstreetprep.com/knowledge/viral-coefficient/) -- K = invitations x conversion rate
- [WhatsApp Interactive Messages](https://www.delightchat.io/blog/whatsapp-list-message-reply-buttons-interactive-message) -- List messages support up to 10 rows per section
- [Shopify GraphQL codeDiscountNodes](https://shopify.dev/docs/api/admin-graphql/latest/queries/codeDiscountNodes) -- query for listing discount codes
- [SurveySparrow conversational NPS](https://surveysparrow.com/blog/nps-software-for-saas/) -- conversational survey pattern reference
- [WhatsApp survey best practices](https://wasenderapi.com/blog/whatsapp-api-for-customer-feedback-automate-surveys-triple-response-rates) -- 98% open rate, keep to 3-5 questions

### Tertiary (LOW confidence)
- Audio testimonial approach via MediaRecorder API -- based on general web capabilities, not verified for this specific use case. Needs validation during implementation.
- WhatsApp template approval timeline -- varies by Meta review queue, cannot guarantee timing.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - exact same stack as Phases 4-9, no new libraries
- Architecture: HIGH - follows established 6-phase pattern for metrics panel
- New CRM models: HIGH - straightforward SQLAlchemy models following existing patterns
- NPS survey design: MEDIUM - based on research into best practices, not production-tested
- WhatsApp delivery: MEDIUM - API structure documented but template approval process is external dependency
- Audio testimonials: LOW - MediaRecorder API approach reasonable but untested in this codebase
- K-Factor calculation: HIGH - standard formula, well-documented

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable patterns, no fast-moving dependencies)
