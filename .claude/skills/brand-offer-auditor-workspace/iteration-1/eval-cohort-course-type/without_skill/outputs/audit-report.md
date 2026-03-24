# Audit Report: COHORT_BASED_COURSE Offer Type

**Date:** 2026-03-23
**Scope:** End-to-end audit of the `COHORT_BASED_COURSE` offer type — from domain model to SDR prompt injection.
**Goal:** Ensure the system captures everything an AI Sales Agent needs to sell a cohort-based course effectively.

---

## 1. Current State Summary

### Classification
| Property | Value |
|---|---|
| Enum | `OfferType.COHORT_BASED_COURSE` |
| Value Level | Level 2 — Mid Ticket ($297-$997) |
| Default Delivery | DWY (Done With You) |
| Details Class | `ProgramDetails` |
| Frontend Sections | identity, strategy, psychology, promise, program_details, instructors, value_stack, resources, gallery, pricing, closing |

### Data Model (`ProgramDetails` — backend)
| Field | Type | Default | Captured? |
|---|---|---|---|
| `curriculum` | List[ProgramModule] | [] | Yes |
| `structure_type` | ProgramStructure | None | Yes |
| `start_date` | datetime | None | Yes |
| `registration_end_date` | datetime | None | Yes |
| `end_date` | datetime | None | Yes |
| `is_end_date_estimated` | bool | False | Yes |
| `duration_weeks` | int | None | Yes |
| `cohort_limit` | int | None | Yes |
| `current_enrollment_count` | int | 0 | Yes |
| `is_application_required` | bool | False | Yes |
| `interaction_type` | LiveInteractionType | None | Yes |
| `live_schedule_description` | str | None | Yes |
| `schedule` | List[SessionDetails] | [] | Yes |
| `lms_url` | HttpUrl | None | Yes |
| `community_platform` | CommunityPlatform | None | Yes |
| `community_invite_link` | HttpUrl | None | Yes |
| `has_certification` | bool | False | Yes |
| `homework_submission_required` | bool | False | Yes |

### What the SDR Currently Receives (via `agent_identity.j2`)
The template renders these fields per offer:
- `public_name`, `type`, `headline_promise`, `primary_outcome`, `time_to_value`
- `pricing_options` (label, amount, installments)
- `guarantee_type` + `guarantee_terms`
- `deliverables` (name, format, quantity)
- `marketing_pain_points`, `marketing_desires`
- `objections` (type, strategy, rebuttal)
- `checkout_page_url`, `calendar_type_id`

---

## 2. CRITICAL Gaps (SDR Cannot Sell Effectively)

### GAP-01: `specific_details` is NOT injected into the SDR prompt
**Severity: CRITICAL**

The `agent_identity.j2` template iterates over `offer.*` top-level fields but **never accesses `offer.specific_details`**. This means the SDR has zero visibility into:

- **Start/end dates** of the cohort (cannot create urgency: "We start April 15th, only 3 spots left")
- **Cohort capacity** and current enrollment (cannot use scarcity)
- **Curriculum / modules** (cannot answer "What will I learn in Week 3?")
- **Session schedule** (cannot answer "What days are the live calls?")
- **Community platform** (cannot answer "Where do we interact?")
- **Whether certification is included** (cannot use it as a value lever)
- **Registration deadline** (cannot enforce urgency)
- **LMS URL** (cannot explain the learning experience)

The `model_dump(mode="json")` in `knowledge_builder.py` does serialize `specific_details` into the offers dict, so the data IS available — but the Jinja template simply never renders it.

**Recommendation:** Add a `specific_details` block to `agent_identity.j2` inside the offer loop. For `ProgramDetails`, render at minimum: `start_date`, `end_date`, `registration_end_date`, `cohort_limit`, `current_enrollment_count`, `curriculum` (titles), `schedule`, `community_platform`, `has_certification`.

### GAP-02: No cohort availability / scarcity data point
**Severity: CRITICAL**

Even if `cohort_limit` and `current_enrollment_count` exist in the model, there is **no computed `spots_remaining` field** and no mechanism to keep `current_enrollment_count` in sync with actual purchases. The SDR cannot truthfully say "We only have 5 spots left" because:

1. The count is manually entered via the form (not synced to payment or CRM events).
2. No webhook or event triggers an update when a sale closes.

**Recommendation:**
- Add a computed property or template helper: `spots_remaining = cohort_limit - current_enrollment_count`.
- Integrate with payment/CRM events to auto-increment `current_enrollment_count` on confirmed purchase.

### GAP-03: No `cohort_name` or `cohort_edition` identifier
**Severity: HIGH**

Creators who run recurring cohorts (e.g., "Cohorte 7 - Abril 2026") need a way to distinguish editions. Currently the only identifier is `public_name`, which is the general offer name. The SDR has no way to say "You're joining Cohort 7" or "The Spring 2026 edition."

**Recommendation:** Add `cohort_name` (or `edition_label`) as an optional string field to `ProgramDetails`.

---

## 3. HIGH Gaps (SDR Effectiveness Reduced)

### GAP-04: `interaction_type` is silently coerced in the repository
**Severity: HIGH**

In `offer_repository.py` line 173-174, `LIVE_PROGRAM_DELIVERY` is hardcoded to map to `group_q_and_a`:
```python
if details_json["interaction_type"] == "LIVE_PROGRAM_DELIVERY":
    details_json["interaction_type"] = "group_q_and_a"
```

This means every cohort course saved from the frontend as "Programa dictado en vivo" (`LIVE_PROGRAM_DELIVERY`) silently becomes "Q&A grupal" on the backend. If the SDR were to receive this data, it would misrepresent the actual delivery format. This is a **data integrity bug**.

**Recommendation:** Fix the enum mapping. Either add `LIVE_PROGRAM_DELIVERY` as a valid value in the backend `LiveInteractionType` enum, or map it to a semantically accurate value.

### GAP-05: `community_platform` = `ZOOM` is coerced to `none`
**Severity: HIGH**

In `offer_repository.py` line 176-177:
```python
if details_json["community_platform"] == "ZOOM":
    details_json["community_platform"] = "none"
```

Many cohort courses use Zoom as their primary interaction platform. This coercion erases that information. The SDR would not know to mention "Live Zoom sessions every Tuesday."

**Recommendation:** Add `ZOOM` (and `GOOGLE_MEETS`) as valid values in the backend `CommunityPlatform` enum, since the frontend already defines them.

### GAP-06: Frontend/Backend enum value mismatch (systematic)
**Severity: HIGH**

The frontend and backend use different string values for the same concepts:

| Concept | Frontend Value | Backend Value |
|---|---|---|
| ProgramStructure.FIXED_COHORT | `"FIXED_COHORT"` | `"fixed_cohort"` |
| LiveInteractionType.GROUP_Q_AND_A | `"GROUP_Q&A"` | `"group_q_and_a"` |
| LiveInteractionType.LIVE_PROGRAM_DELIVERY | `"LIVE_PROGRAM_DELIVERY"` | **does not exist** |
| CommunityPlatform.ZOOM | `"ZOOM"` | **does not exist** |
| CommunityPlatform.GOOGLE_MEETS | `"GOOGLE_MEETS"` | **does not exist** |
| GuaranteeType.NO_REFUNDS | `"NO_REFUNDS"` | coerced to `"none"` |
| GuaranteeType.UNCONDITIONAL_X_DAY | `"UNCONDITIONAL_X_DAY"` | `"unconditional_30_day"` |
| GuaranteeType.EXCHANGE_ONLY | `"EXCHANGE_ONLY"` | **does not exist** |
| DeliverableFormat | 5 values (FE) | 9 values (BE) — different names |

The repository `_to_domain` method contains ad-hoc coercions (lines 170-183) that patch over these mismatches, but they are lossy and incomplete. This affects ALL offer types, but it is especially damaging for cohort courses because `ProgramDetails` has more enum fields than other detail types.

**Recommendation:** Align enum values across frontend and backend. Introduce a shared enum contract (e.g., a JSON schema or shared constants file) and write a migration to normalize existing DB values.

### GAP-07: No early-bird / launch pricing concept
**Severity: MEDIUM-HIGH**

Cohort courses almost universally use time-sensitive pricing (early bird, launch price, last-chance). The `PricingStructure` model supports multiple pricing options with labels, but there is no `valid_until` date or `is_early_bird` flag. The SDR cannot say "The early bird price of $297 ends Friday" because there is no temporal dimension to pricing.

**Recommendation:** Add `valid_from` / `valid_until` (optional datetime) to `PricingStructure`. This enables the SDR to create time-based urgency with truthful data.

---

## 4. MEDIUM Gaps (Nice-to-Have for Better Selling)

### GAP-08: No `timezone` field in the SDR prompt context
**Severity: MEDIUM**

The frontend form captures timezone, and `ProgramDetails` has a `timezone` field defaulting to `"UTC"`. But since `specific_details` is not rendered in the prompt (GAP-01), the SDR cannot localize session times for the prospect.

**Recommendation:** When GAP-01 is resolved, ensure timezone is rendered alongside the schedule.

### GAP-09: No success metrics / completion rate data
**Severity: MEDIUM**

Cohort courses benefit from social proof specific to program outcomes: "92% of graduates complete the program" or "Average ROI of 3x within 60 days." There is no field for cohort-level success metrics.

**Recommendation:** Add an optional `success_metrics` (List[str] or Dict) field to `ProgramDetails` for data like completion rate, average outcome, NPS score.

### GAP-10: No `next_cohort_date` for waitlist/pre-launch state
**Severity: MEDIUM**

When an offer is in `WAITLIST` or `SOLD_OUT` status, the SDR needs to know when the next cohort opens. Currently there is no `next_cohort_start_date` field. The SDR cannot say "The current cohort is full, but Cohort 8 starts June 1st — want me to reserve your spot?"

**Recommendation:** Add `next_cohort_start_date` to `ProgramDetails` (or handle this at the Offer level via a related "next edition" offer linked by `upsell_offer_id`).

### GAP-11: `curriculum` is not summarized for the SDR
**Severity: MEDIUM**

Even when GAP-01 is fixed, dumping the full curriculum (module titles, descriptions, topics for potentially 8-12 modules) into the prompt could consume significant context window. There is no `curriculum_summary` field that gives the SDR a digestible overview.

**Recommendation:** Either add a `curriculum_summary` (str) field, or generate one via AI at save time. The template should render the summary, not the full module tree.

### GAP-12: `homework_submission_required` exists but has no SDR value without context
**Severity: LOW**

The boolean `homework_submission_required` is captured, but the SDR has no description of what homework looks like, how it is reviewed, or what accountability mechanism exists. For a "Done-With-You" program, homework accountability is a strong selling point.

**Recommendation:** Add `homework_description` (str) alongside the boolean.

---

## 5. Enum Completeness Check

### `ProgramStructure` — Adequate for COHORT_BASED_COURSE
`FIXED_COHORT` is the correct structure type. `ROLLING_ADMISSION` and `CHALLENGE` are also available for other program types. No gaps here.

### `LiveInteractionType` — Missing backend values
Frontend offers `LIVE_PROGRAM_DELIVERY` and `HYBRID` which are critical for cohort courses (many are taught live, not just Q&A). Backend silently discards these.

### `CommunityPlatform` — Missing backend values
Frontend offers `ZOOM` and `GOOGLE_MEETS` which are the two most common platforms for live cohort delivery. Backend silently discards these.

### `DeliverableFormat` — Semantic mismatch
Backend uses granular format names (`pdf`, `video`, `audio`, `live_session`, etc.) while frontend uses higher-level names (`LIVE_GROUP_CALL`, `1ON1_CALL`, `RECORDED_CONTENT`, `DFY_ASSET`, `PHYSICAL_SHIPMENT`). This means deliverables saved from the frontend may not parse correctly on the backend.

---

## 6. Frontend Form Completeness

The `ProgramDetailsForm` component is well-built for COHORT_BASED_COURSE:
- Structure type selector with smart interaction-type filtering
- Full calendar picker for start/end/registration dates (conditionally shown for FIXED_COHORT)
- Timezone selector
- Session schedule builder
- Curriculum builder (modules + topics)
- Community platform selector
- Application required toggle

**Missing from the form:**
- `cohort_limit` — Not visible in the form (exists in schema but no form field renders it)
- `current_enrollment_count` — Not visible in the form
- `lms_url` — Not visible in the form
- `has_certification` — Not visible in the form
- `homework_submission_required` — Not visible in the form
- `live_schedule_description` — Not visible in the form

These 6 fields exist in `ProgramDetailsSchema` (Zod) and `ProgramDetails` (Pydantic) but have no corresponding form inputs in `program-form.tsx`. They are effectively dead fields for this offer type.

---

## 7. Prioritized Action Plan

| Priority | Gap | Effort | Impact |
|---|---|---|---|
| P0 | GAP-01: Inject `specific_details` into `agent_identity.j2` | Small (template edit) | Unlocks ALL cohort data for SDR |
| P0 | GAP-04: Fix `LIVE_PROGRAM_DELIVERY` coercion bug | Small (enum + repo fix) | Prevents data corruption |
| P0 | GAP-05: Fix `ZOOM`/`GOOGLE_MEETS` coercion bug | Small (enum + repo fix) | Prevents data corruption |
| P1 | GAP-06: Align FE/BE enum values | Medium (migration + code) | Systemic fix, prevents future bugs |
| P1 | GAP-02: Auto-sync enrollment count + spots_remaining | Medium (event integration) | Enables truthful scarcity |
| P1 | Form: Add missing fields (cohort_limit, lms_url, certification, homework) | Small (form fields) | Captures data that already has schema support |
| P2 | GAP-03: Add `cohort_name` / `edition_label` | Small (model + form field) | Better SDR personalization |
| P2 | GAP-07: Time-bound pricing (`valid_until`) | Medium (model + form + template) | Enables urgency |
| P2 | GAP-10: `next_cohort_start_date` for waitlist | Small (model field) | Better waitlist handling |
| P3 | GAP-09: Success metrics | Small (model field) | Better social proof |
| P3 | GAP-11: Curriculum summary | Small (model field or AI gen) | Cleaner SDR context |
| P3 | GAP-12: Homework description | Small (model field) | Minor selling point |

---

## 8. Conclusion

The data model for `COHORT_BASED_COURSE` is reasonably comprehensive at the schema level -- `ProgramDetails` captures most of what a cohort course needs. However, **the critical bottleneck is that none of this data reaches the SDR**. The `agent_identity.j2` template does not render `specific_details`, which means the AI Sales Agent sells cohort courses with the same generic information it uses for any other offer type: name, price, promise, deliverables.

The secondary issue is a **systematic frontend-backend enum mismatch** that causes silent data loss through coercions in the repository layer. Fields like `interaction_type` and `community_platform` — which are essential for describing the cohort experience — are corrupted before they even reach the domain model.

Fixing GAP-01 (template) + GAP-04/05 (enum coercions) + adding the 6 missing form fields would transform the SDR's ability to sell cohort courses from "generic pitch" to "informed, specific, urgency-driven conversation."
