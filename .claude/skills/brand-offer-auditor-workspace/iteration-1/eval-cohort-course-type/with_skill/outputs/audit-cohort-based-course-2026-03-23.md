# Specific Offer Type Audit: COHORT_BASED_COURSE

> **Scope:** OfferType: COHORT_BASED_COURSE (Level 2 — Mid-Ticket Program)
> **Date:** 2026-03-23
> **Frameworks Applied:**
> - Hormozi (Grand Slam Offer) — PRIMARY
> - WbD (Impact & Critical Event) — PRIMARY
> - Casel (Productization Architecture) — PRIMARY (curriculum = productized workflow)
> - Brunson (Value Ladder) — SECONDARY
> - Brand Love Key / StoryBrand — SECONDARY (brand inheritance check)
> - Keller (Brand Resonance) — SECONDARY (community/belonging)

## Executive Summary

The COHORT_BASED_COURSE type maps to `ProgramDetails` and has a solid structural foundation: curriculum builder, session scheduling, cohort limits, dates, community platform, and certification. However, the system has critical gaps in three areas that directly cripple the SDR's ability to sell a mid-ticket cohort program: (1) there is no `critical_event` field anywhere in the offer schema, meaning the SDR cannot identify WHY the prospect should enroll NOW instead of "next cohort"; (2) there is no explicit field for customer effort/commitment required, leaving the Hormozi Value Equation incomplete; and (3) the `specific_details` data (curriculum, schedule, cohort_limit, start_date) is completely absent from the `agent_identity.j2` template that feeds the SDR, rendering all program-specific data invisible to the sales agent.

## Findings

### CRITICAL — System Cannot Function Without This

- [ ] **[C-01] SDR is blind to ProgramDetails — specific_details not rendered in agent identity** (Framework: All)
  - **Gap**: The `agent_identity.j2` template iterates over `offer.deliverables`, `offer.marketing_pain_points`, `offer.objections`, etc., but **never reads `offer.specific_details`**. For a COHORT_BASED_COURSE, this means the SDR has zero knowledge of: curriculum modules, session schedule, cohort start date, cohort limit, seats remaining, community platform, whether certification exists, or whether homework is required.
  - **Impact**: When a prospect asks "What topics does the program cover?", "When does it start?", "How many people are in the cohort?", or "Is there a certificate?", the SDR literally cannot answer. It only knows the generic offer fields (name, price, promise). This is fatal for a mid-ticket program sale where the prospect needs specifics before committing.
  - **Recommendation**: Add a `{% if offer.specific_details %}` block to `agent_identity.j2` that renders program-specific fields. At minimum: `curriculum` (module titles + descriptions), `start_date`, `end_date`, `duration_weeks`, `cohort_limit`, `current_enrollment_count`, `interaction_type`, `schedule`, `community_platform`, `has_certification`. Consider a conditional block per details type (ProgramDetails, ServiceDetails, etc.).
  - **Affected files**:
    - `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2`
    - `backend/src/modules/sales_agent/application/services/knowledge_builder.py` (data already flows via `model_dump`, but template doesn't use it)

- [ ] **[C-02] No Critical Event field — SDR cannot create urgency** (Framework: WbD — Impact & Critical Event)
  - **Gap**: There is no `critical_event` field in the `Offer` model or in `ProgramDetails`. The WbD framework defines the critical event as the external trigger that makes someone need to act NOW (e.g., "My launch is in 4 weeks", "I just got fired", "My competitor just launched a course"). For a cohort-based course, urgency is everything — there's a start date, a registration deadline, and limited spots. But the SDR has no language for WHY THIS COHORT matters to THIS prospect.
  - **Impact**: The SDR can mention the start date (if C-01 is fixed), but cannot connect it to the prospect's personal situation. Without a critical event, the SDR defaults to generic pressure ("spots are filling up") instead of targeted urgency ("You mentioned your launch is next quarter — if you don't have this skill by then, what happens?"). This is the #1 tool for closing mid-ticket sales.
  - **Recommendation**: Add `critical_event: Optional[str]` to the `Offer` model (not ProgramDetails, since this is relevant to ALL offer types). UI label: "Que situacion de vida hace que alguien NECESITE esto ahora?" with examples. Also add `impact_rational: Optional[str]` and `impact_emotional: Optional[str]` to separate the two impact dimensions currently conflated in `marketing_pain_points`.
  - **Affected files**:
    - `backend/src/modules/offer/domain/offer.py` — add fields to `Offer` and `OfferPsychologyUpdate`
    - `frontend/src/features/offer-studio/types/index.ts` — add to `Offer` interface
    - `frontend/src/features/offer-studio/types/schema.ts` — add to `OfferSchema`
    - `frontend/src/features/offer-studio/components/editor/sections/psychology/psychology-form.tsx` — add UI fields

- [ ] **[C-03] No customer effort/commitment field — Hormozi Value Equation is 50% missing** (Framework: Hormozi — Grand Slam Offer)
  - **Gap**: The Hormozi Value Equation has four variables: Dream Outcome, Perceived Likelihood, Time Delay, and Effort & Sacrifice. The system captures Dream Outcome (`primary_outcome`), partially captures Time Delay (`time_to_value`), and partially captures Perceived Likelihood (`guarantee_type`, `objections`). But there is NO field for Effort & Sacrifice — what the student must DO and GIVE UP. For a cohort course, this is critical: "You need to dedicate 5 hours/week and attend all live sessions" vs. "Just watch the videos when you can."
  - **Impact**: The SDR cannot set expectations or preempt the "I don't have time" objection (the #1 objection for mid-ticket programs). If the program requires 10 hours/week and the SDR doesn't know this, it will oversell to people who can't commit, leading to refund requests and bad reviews. Conversely, if the effort is LOW, the SDR can't use that as a selling point.
  - **Recommendation**: Add `student_effort_description: Optional[str]` and `weekly_time_commitment_hours: Optional[float]` to `ProgramDetails`. UI label: "Cuanto tiempo por semana necesita dedicar el alumno?" and "Que tiene que hacer el alumno? (tareas, asistencia, etc.)". These fields directly feed the Hormozi equation: lower perceived effort = higher perceived value.
  - **Affected files**:
    - `backend/src/modules/offer/domain/details.py` — add to `ProgramDetails`
    - `frontend/src/features/offer-studio/types/schema.ts` — add to `ProgramDetailsSchema`
    - `frontend/src/features/offer-studio/components/editor/sections/program-details/program-form.tsx` — add UI fields

### HIGH — Significant Quality Degradation

- [ ] **[H-01] No urgency/scarcity mechanism beyond cohort_limit** (Framework: Hormozi — Urgency + Brunson — Ascension)
  - **Gap**: `ProgramDetails` has `cohort_limit` and `current_enrollment_count`, which can theoretically express scarcity ("3 spots left"). But there is no explicit scarcity/urgency messaging field, no `waitlist_enabled` flag, no `early_bird_deadline`, and no `bonus_deadline` (e.g., "Enroll by March 30 and get a free 1:1 session"). The `OfferStatus` enum has `WAITLIST` and `SOLD_OUT`, but these are static states, not dynamic urgency triggers.
  - **Impact**: The SDR cannot say "Only 3 spots left" because `current_enrollment_count` isn't rendered in the agent identity (see C-01). Even if fixed, there's no mechanism for time-based urgency (early-bird pricing, bonus deadlines). For mid-ticket, urgency is what converts "I'll think about it" into "Let me sign up."
  - **Recommendation**: Add to `ProgramDetails`: `waitlist_enabled: bool = False`, `early_bird_deadline: Optional[datetime] = None`, `early_bird_pricing_label: Optional[str] = None`. Add to `Offer` (generic, all types): `scarcity_message: Optional[str] = None` (free text the SDR can use, e.g., "Solo quedan 5 lugares para esta cohorte"). Consider a computed property: `spots_remaining = cohort_limit - current_enrollment_count`.
  - **Affected files**:
    - `backend/src/modules/offer/domain/details.py` — add early_bird fields to `ProgramDetails`
    - `backend/src/modules/offer/domain/offer.py` — add `scarcity_message` to `Offer`

- [ ] **[H-02] Bonuses not distinguishable from core deliverables** (Framework: Hormozi — Offer Stack)
  - **Gap**: The Hormozi Offer Stack explicitly separates Core Offer from Bonuses. Bonuses are value amplifiers that increase perceived value without raising price. Currently, `deliverables: List[DeliverableItem]` treats everything equally — there is no `is_bonus: bool` flag on `DeliverableItem`. The SDR cannot differentiate "This is what you're paying for" from "And you ALSO get these bonuses worth $X."
  - **Impact**: The value stack pitch loses its power. Instead of "The program is worth $2,000, but you ALSO get $3,000 in bonuses for free," the SDR just lists everything as a flat list. The psychological impact of bonuses is destroyed.
  - **Recommendation**: Add `is_bonus: bool = False` to `DeliverableItem` in the backend model and frontend schema. In the UI, visually separate bonuses from core deliverables. In the agent identity template, render them in two sections: "Incluye:" and "Bonuses adicionales:".
  - **Affected files**:
    - `backend/src/modules/offer/domain/offer.py` — add `is_bonus` to `DeliverableItem`
    - `frontend/src/features/offer-studio/types/schema.ts` — add to `DeliverableItemSchema`
    - `frontend/src/features/offer-studio/components/editor/sections/value-stack/value-stack-form.tsx` — add toggle
    - `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2` — split rendering

- [ ] **[H-03] marketing_pain_points conflates rational and emotional impact** (Framework: WbD — Impact)
  - **Gap**: `marketing_pain_points: List[str]` is a flat list of strings. WbD requires separating rational impact (measurable: money lost, time wasted, opportunity cost) from emotional impact (stress, embarrassment, fear). The psychology generator prompt asks for "dolores viscerales" but doesn't distinguish types. The SDR needs both: rational impact to convince, emotional impact to convert.
  - **Impact**: Pain points tend to be surface-level and all the same tone. The SDR uses them interchangeably instead of strategically — rational when the prospect is analytical ("Every month you delay costs you $X in lost revenue"), emotional when the prospect is hesitant ("How does it feel watching your competitors succeed while you're stuck?").
  - **Recommendation**: Either split into `pain_points_rational: List[str]` and `pain_points_emotional: List[str]`, or add a `type` field to each pain point (similar to how `ObjectionItem` has a `type`). Update the psychology generator prompt to explicitly produce both categories. Simpler approach: keep the flat list but update the prompt to produce alternating rational/emotional entries with clear labels.
  - **Affected files**:
    - `backend/src/modules/offer/domain/offer.py` — consider structured pain model
    - `backend/src/modules/copilot/infrastructure/prompts/templates/offer_psychology_generator.j2` — update instructions
    - `frontend/src/features/offer-studio/components/editor/sections/psychology/psychology-form.tsx`

- [ ] **[H-04] ProgramDetails lacks exclusions — what's NOT included** (Framework: Casel — Productization)
  - **Gap**: Casel's productization framework requires explicit exclusions. `ProgramDetails` captures what IS included (curriculum, sessions, community) but has no field for what is NOT included. For a cohort course, common exclusions are: "1:1 private sessions are not included", "The program does not include done-for-you implementation", "Access to recordings expires after 6 months."
  - **Impact**: The SDR cannot handle "Does this include personal mentoring?" definitively. Without exclusions, the SDR either guesses (dangerous) or says "let me check" (kills momentum). Explicit exclusions also protect against scope creep and refund disputes.
  - **Recommendation**: Add `exclusions: List[str] = []` to `ProgramDetails`. UI label: "Que NO incluye el programa? (Esto protege contra malentendidos y refunds)". Render in agent identity under a "No incluye:" section.
  - **Affected files**:
    - `backend/src/modules/offer/domain/details.py` — add to `ProgramDetails`
    - `frontend/src/features/offer-studio/types/schema.ts` — add to `ProgramDetailsSchema`
    - `frontend/src/features/offer-studio/components/editor/sections/program-details/program-form.tsx`

### MEDIUM — Improvement Opportunity

- [ ] **[M-01] No success_metrics field — SDR cannot set measurable expectations** (Framework: WbD — Metrics)
  - **Gap**: `primary_outcome` captures the dream result, but there's no field for how the student MEASURES success. For a cohort course teaching marketing, is success "10 new clients" or "a complete funnel built" or "100 email subscribers"? The SDR needs specific metrics to anchor the promise.
  - **Impact**: Without measurable outcomes, the promise feels vague. The SDR says "You'll transform your business" instead of "By week 8, you'll have a complete sales funnel generating at least 3 qualified leads per week." Specific metrics increase perceived likelihood (Hormozi).
  - **Recommendation**: Add `success_metrics: List[str] = []` to `Offer` (generic, all types). UI label: "Como mide el alumno que tuvo exito? (Ej: Primer cliente en 30 dias, Funnel construido y en produccion)".
  - **Affected files**:
    - `backend/src/modules/offer/domain/offer.py` — add to `Offer`
    - `frontend/src/features/offer-studio/types/schema.ts` — add to `OfferSchema`

- [ ] **[M-02] ProgramModule lacks learning_outcome — curriculum is structurally shallow** (Framework: Casel — Workflow)
  - **Gap**: `ProgramModule` has `title`, `description`, and `topics: List[str]`. But there's no `learning_outcome` or `student_will_be_able_to` field per module. The SDR sees "Module 3: Marketing Funnels" but cannot say "After this module, you'll have a complete funnel live and generating leads."
  - **Impact**: The curriculum looks like a table of contents instead of a journey of transformation. Each module should communicate its micro-transformation so the SDR can sell the progression, not just the content.
  - **Recommendation**: Add `learning_outcome: Optional[str] = None` to `ProgramModule`. UI placeholder: "Al completar este modulo, el alumno podra..." This also feeds landing page generation.
  - **Affected files**:
    - `backend/src/modules/offer/domain/details.py` — add to `ProgramModule`
    - `frontend/src/features/offer-studio/types/schema.ts` — add to `ProgramModuleSchema`
    - `frontend/src/features/offer-studio/components/editor/sections/program-details/curriculum-builder.tsx`

- [ ] **[M-03] No transformation_before / transformation_after fields** (Framework: StoryBrand — Success Transformation + Hormozi — Dream Outcome)
  - **Gap**: `primary_outcome` is a single text field. StoryBrand's Success Transformation and Hormozi's Dream Outcome work best as a before/after contrast: "Before: Struggling to get 2 clients per month. After: Fully booked with a waitlist." The contrast is what creates desire.
  - **Impact**: The SDR can only describe the destination, not the journey. A before/after pair is far more powerful in sales conversations: "Right now you're doing X. After the program, you'll be doing Y. Can you imagine that?"
  - **Recommendation**: Add `transformation_before: Optional[str] = None` and `transformation_after: Optional[str] = None` to `Offer`. Keep `primary_outcome` as the synthesized version. UI label: "Describe el ANTES y DESPUES de tu alumno."
  - **Affected files**:
    - `backend/src/modules/offer/domain/offer.py` — add to `Offer`

- [ ] **[M-04] GuaranteeType enum mismatch between backend and frontend** (Framework: Hormozi — Guarantee)
  - **Gap**: Backend `GuaranteeType` has: `NONE`, `CONDITIONAL_ACTION_BASED`, `UNCONDITIONAL_30_DAY`, `DOUBLE_MONEY_BACK`, `SATISFACTION_OR_FREE_WORK`. Frontend has: `UNCONDITIONAL_X_DAY`, `CONDITIONAL_ACTION_BASED`, `EXCHANGE_ONLY`, `NO_REFUNDS`. These are different sets with different values. The backend has `DOUBLE_MONEY_BACK` (not in frontend), frontend has `EXCHANGE_ONLY` (not in backend).
  - **Impact**: Data may not serialize/deserialize correctly between frontend and backend. Hormozi recommends a spectrum of guarantee types; the system should have ONE canonical enum shared between both.
  - **Recommendation**: Unify the enum. Recommended unified set: `NONE`/`NO_REFUNDS`, `UNCONDITIONAL_X_DAY`, `CONDITIONAL_ACTION_BASED`, `EXCHANGE_ONLY`, `DOUBLE_MONEY_BACK`, `SATISFACTION_OR_FREE_WORK`. Ensure values match on both sides.
  - **Affected files**:
    - `backend/src/modules/offer/domain/enums.py`
    - `frontend/src/features/offer-studio/types/index.ts`

- [ ] **[M-05] `live_schedule_description` is redundant with `schedule: List[SessionDetails]`** (Deduplication)
  - **Gap**: `ProgramDetails` has both `live_schedule_description: Optional[str]` (free text) and `schedule: List[SessionDetails]` (structured). The structured `schedule` field has `title`, `day_of_week`, `time`, `duration_minutes`. The free text field seems redundant but might serve as a human-readable summary.
  - **Impact**: Potential confusion about which to fill. If the user fills only `live_schedule_description` but not `schedule`, the SDR gets unstructured text. If they fill both, there may be contradictions.
  - **Recommendation**: Keep `schedule` as the source of truth and auto-generate `live_schedule_description` from it (or remove it). In the UI, the `SessionScheduleBuilder` already provides the structured input; the description field could be a computed summary.
  - **Affected files**:
    - `backend/src/modules/offer/domain/details.py`
    - `frontend/src/features/offer-studio/components/editor/sections/program-details/program-form.tsx`

## Deduplication Opportunities

| Concept | Current Fields | Frameworks | Recommendation |
|---------|---------------|------------|----------------|
| Pain/suffering | `marketing_pain_points[]`, StoryBrand `external_problem` + `internal_problem` (brand level) | WbD, StoryBrand, Hormozi | Keep `marketing_pain_points` at offer level but structure with type (rational/emotional). Brand narrative problems inform the tone; offer pains are specific to the product. No duplication issue. |
| Dream result | `primary_outcome`, `headline_promise`, StoryBrand `success_transformation` (brand level) | Hormozi, StoryBrand | `primary_outcome` = specific measurable result. `headline_promise` = the marketing-friendly version. Keep both — they serve different purposes. Add before/after to `primary_outcome` for richer contrast. |
| Schedule description | `live_schedule_description`, `schedule: List[SessionDetails]` | Casel (workflow) | Unify: auto-generate the description from structured data. Remove free-text redundancy. |
| Access/duration | `access_duration` + `access_duration_text` (Offer), `duration_weeks` + `start_date`/`end_date` (ProgramDetails) | Casel (timeline) | These are different concepts. `access_duration` = how long they can access content post-program. `duration_weeks` = how long the program runs. Keep both; they answer different SDR questions. |

## Methodology Coverage Matrix

| Framework | Weight | Coverage | Key Gaps |
|-----------|--------|----------|----------|
| **Hormozi (Grand Slam Offer)** | PRIMARY | 3/5 atomic elements | Missing: Effort & Sacrifice (no field), Urgency/Scarcity (partial — cohort_limit exists but no messaging), Bonus distinction (no is_bonus flag) |
| **WbD (Impact & Critical Event)** | PRIMARY | 1/6 atomic elements | Missing: Critical Event (no field), Rational Impact (conflated), Emotional Impact (conflated), Decision Criteria (no field), Success Metrics (no field) |
| **Casel (Productization)** | PRIMARY | 4/6 atomic elements | Covered: Scope (curriculum), Workflow (schedule/modules), Deliverables, Timeline (dates/duration). Missing: Exclusions, Fixed Price justification narrative |
| **Brunson (Value Ladder)** | SECONDARY | 4/5 atomic elements | Covered: Level assignment, upsell/downsell links, pricing, includes_offers. Missing: Ascension messaging (WHY go to Level 3 after this?) |
| **Brand Love Key** | SECONDARY | N/A (brand-level) | Covered at brand level. Bridge to offer is functional via knowledge_builder.py |
| **StoryBrand** | SECONDARY | N/A (brand-level) | Covered at brand level. Story inheritance works. Missing: offer-level before/after contrast |
| **Keller (Resonance)** | SECONDARY | 2/4 relevant elements | Community (community_platform exists), Belonging signal. Missing: Social identity ("what does enrolling say about you?") |

## SDR Readiness Score

| SDR Question | Answerable? | Source Field(s) | Gap |
|-------------|-------------|-----------------|-----|
| "Who am I talking to?" | YES | `brand.avatars`, `offer.target_avatar_match` | None |
| "What's their trigger to buy NOW?" | NO | (no field) | No `critical_event` field exists anywhere |
| "What's at stake if they don't act?" | PARTIAL | `offer.marketing_pain_points` | Pains are unsorted (rational vs emotional), no explicit impact framing |
| "What am I actually selling?" | PARTIAL | `offer.primary_outcome`, `offer.deliverables` | Deliverables visible, but specific_details (curriculum, schedule) invisible to SDR (C-01) |
| "Why should they believe this works?" | PARTIAL | `brand.testimonials`, `offer.guarantee_type` | Testimonials and guarantee work. No offer-level case studies or cohort completion rates |
| "What objections will they raise?" | YES | `offer.objections[]` with type, strategy, rebuttal, trigger_phrases | Well-implemented with SemanticRouter integration |
| "How do I create urgency?" | NO | (no field rendered) | `cohort_limit` and `registration_end_date` exist in ProgramDetails but are not rendered in agent_identity.j2 |
| "What's the process after yes?" | PARTIAL | `offer.onboarding_action`, `offer.onboarding_url` | Onboarding mechanism exists, but post-enrollment flow (access LMS, join community, first session) not described for SDR |
| "How does this brand talk?" | YES | `brand.identity.voice_tone`, `brand.identity.communication_style` | Fully rendered in agent identity |
| "How long is the program? When does it start?" | NO (SDR-invisible) | `ProgramDetails.duration_weeks`, `start_date`, `end_date` | Data exists in the model but is NOT rendered in agent_identity.j2 |
| "Is there a waitlist?" | PARTIAL | `OfferStatus.WAITLIST` exists as a status | But it's a static state, not a dynamic SDR tool |
| "What topics are covered?" | NO (SDR-invisible) | `ProgramDetails.curriculum` | Data exists but not rendered to SDR |

**Overall SDR Readiness: 3/9 core questions fully answerable (with 4 PARTIAL and 2 NO)**

For a mid-ticket cohort program, this score is insufficient. The SDR can handle brand context, objections, and avatar matching well, but is crippled on the program-specific questions that prospects actually ask before enrolling in a cohort.

## Brand Essence Bridge

| Bridge | Connected? | How | Gap |
|--------|-----------|-----|-----|
| Voice inheritance | Yes | `knowledge_builder.py` loads brand identity, `agent_identity.j2` renders `identity.voice_tone` and `identity.communication_style` | None |
| Story inheritance | Partial | `story.origin_story` is rendered. Positioning UVP is rendered. But StoryBrand narrative (hero, villain, plan) is NOT rendered. | Add `brand.narrative` rendering to `agent_identity.j2` — the SDR should know the hero's journey to sell the transformation |
| Positioning inheritance | Partial | `positioning.unique_value_proposition` is rendered. But `discriminator`, `consumer_insight`, `competitive_environment` (enemies) are NOT rendered. | The SDR should know the competitive landscape to handle "how is this different from X?" |
| Proof inheritance | Yes | `testimonials` array is rendered with quote, author, role | Could be enhanced with offer-specific testimonials vs brand-level ones |
| Avatar consistency | Yes | `brand.avatars` and `offer.target_avatar_match` both exist. Builder loads both. | The offer-level `target_avatar_match` is an enum list (BEGINNER/INTERMEDIATE/etc.), not a reference to brand avatars. Consider linking by avatar_id for richer data. |

## Next Steps (Prioritized)

1. **[C-01] Render specific_details in agent_identity.j2** — This is the highest-ROI fix. The data already exists in the database and already flows through `model_dump()` in `knowledge_builder.py`. The template just needs to read it. A few hours of work unlocks curriculum, schedule, dates, cohort limits, and community info for the SDR. This single fix converts 4 SDR questions from NO to YES.

2. **[C-02] Add critical_event field to Offer** — This is the #1 sales weapon for cohort programs. A single text field in the schema + a card in the Psychology form + a line in the agent identity template. Low effort, massive sales impact.

3. **[C-03] Add effort/commitment fields to ProgramDetails** — `weekly_time_commitment_hours` and `student_effort_description`. Two fields that complete the Hormozi equation and preempt the top objection for mid-ticket programs.

4. **[H-04] Add exclusions to ProgramDetails** — A simple `List[str]` that protects against misunderstandings and gives the SDR definitive answers to "Does this include X?" questions.

5. **[H-01] Add scarcity_message and early_bird_deadline** — Urgency mechanisms that convert "I'll think about it" into action.

6. **[H-02] Add is_bonus flag to DeliverableItem** — Small change, big impact on value stack presentation.

7. **[M-04] Unify GuaranteeType enum** — Backend/frontend mismatch is a ticking time bomb for data integrity.
