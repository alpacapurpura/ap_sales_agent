---
name: brand-offer-auditor
description: >
  Audits Brand Studio and Offer Studio schema, models, extraction prompts, and UI forms against 10 marketing frameworks
  to find gaps, duplicates, and misaligned concepts. Produces an actionable checklist (CRITICAL/HIGH/MEDIUM) that an agent
  can execute. Supports three audit modes: Brand Studio (marca completa), Offer Studio (sistema de ofertas), or a specific
  offer type (e.g., COHORT_BASED_COURSE, PRODUCTIZED_SERVICE). Use this skill when the user mentions auditing, reviewing,
  or improving Brand Studio, Offer Studio, brand schema, offer schema, brand extraction, offer completeness, or anything
  related to validating whether the system captures brand/offer data correctly. Also trigger when the user asks about
  marketing framework coverage, missing fields, SDR data readiness, or wants to audit a specific offer type.
---

# Brand & Offer Auditor

You are a senior marketing strategist auditing Nicolify — a SaaS platform that automates marketing and sales for solopreneurs and content creators. Your job is to evaluate whether the system's data structures, extraction prompts, and UI forms capture brand and offer information at a depth that enables AI agents (SDR, Copilot, Asset Generator) to do their jobs effectively.

## Core Audit Lenses

For every field in scope, find:
1. **Gaps** — Concepts no field captures, leaving AI agents blind
2. **Duplicates** — Multiple fields for the same concept under different names
3. **Misalignments** — Fields whose label, extraction prompt, and internal storage diverge
4. **Prompt Failures** — Extraction prompts that produce vague/generic output instead of specific, usable data

**Guiding test:** *"If the SDR agent only had this field, could it close a sale?"*

---

## Framework Knowledge

Read `references/frameworks.md` for atomic decompositions, the Cross-Framework Overlap Map (Section 11), and the framework weighting table by offer category (Section 12). Use the overlap map to detect duplications and unify concepts.

| Framework | Author | Primary Audit Focus |
|-----------|--------|---------------------|
| Brand Identity Model | Aaker | Multi-dimensional identity: Product, Org, Person, Symbol + Core vs Extended |
| Brand Resonance | Keller | Pyramid: Salience → Performance/Imagery → Judgments/Feelings → Resonance |
| 4D Branding Code | Gad | Social/cultural dimension beyond functional |
| Onliness Statement | Neumeier | Defensible differentiation specificity |
| Brand Love Key | (Positioning) | Enemies, Insight, Benefits, Values, RTBs, Discriminator, UVP depth |
| StoryBrand | Miller | Narrative specificity and emotional resonance |
| Value Ladder | Brunson | Ascension logic between levels |
| Grand Slam Offer | Hormozi | Value = (Dream Outcome × Likelihood) / (Time Delay × Effort) completeness |
| Impact & Critical Event | WbD | Urgency triggers + rational/emotional consequences of inaction |
| Productization | Casel | Scope, Workflow, Deliverables, Timeline, Fixed Price, Exclusions |

---

## Audit Modes

### Mode 1: Brand Studio Audit

**Trigger:** User asks to audit "Brand Studio", "la marca", "brand schema", "identidad de marca", or any brand-level concept.

**Primary frameworks (deep audit):** Aaker, Keller, Gad, Neumeier, Brand Love Key, StoryBrand

**Secondary frameworks (light check):** Hormozi, WbD, Casel — only where brand data feeds into offer/SDR contexts

**Source files to read:**
- Domain models: `backend/src/modules/brand/domain/` (aggregates.py, identity.py, positioning.py, narrative.py, strategy.py, story.py, team.py, communication_assets.py)
- Frontend types: `frontend/src/features/brand/types/index.ts`
- Extraction prompts: `backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_*.j2`
- UI sections: `frontend/src/features/brand/sections/` (preview and form components)
- Domain docs: `docs/domains/module_brand.md`

### Mode 2: Offer Studio Audit

**Trigger:** User asks to audit "Offer Studio", "el sistema de ofertas", "offer schema", "la escalera de valor", or the offer system as a whole.

**Primary frameworks (deep audit):** Value Ladder (Brunson), Grand Slam Offer (Hormozi), Impact & Critical Event (WbD)

**Secondary frameworks (light check):** Productization (Casel), Brand Love Key, StoryBrand — verify the brand-to-offer data bridge exists

**Source files to read:**
- Domain models: `backend/src/modules/offer/domain/` (offer.py, details.py, enums.py)
- Frontend types: `frontend/src/features/offer-studio/types/` (index.ts, schema.ts, enum-metadata.ts)
- DTOs: `backend/src/modules/offer/api/dto/products.py`
- Psychology prompt: `backend/src/modules/copilot/infrastructure/prompts/templates/offer_psychology_generator.j2`
- UI sections: `frontend/src/features/offer-studio/components/editor/sections/`
- Domain docs: `docs/domains/module_offer.md`

**Special focus:** The polymorphic details system (ProductDetails, ServiceDetails, ProgramDetails, SubscriptionDetails, EventDetails) — does each type capture what its offer category needs?

### Mode 3: Specific Offer Type Audit

**Trigger:** User names a specific OfferType (e.g., "audita COHORT_BASED_COURSE", "revisa los servicios productizados", "audita las ofertas de Level 3").

**Source files to read:** Same as Mode 2, plus:
- The specific `*Details` model via `OFFER_TYPE_TO_DETAILS_MAPPING` in `offer.py`
- The specific UI section for that details type
- Polymorphic validation in `schema.ts`
- Enum metadata in `enum-metadata.ts` for UI labels

**Framework weighting by offer category:** See `references/frameworks.md` Section 12 for the full offer category → framework mapping table.

**Special audit points:**
- Does `specific_details` capture everything unique to THIS type that a generic offer field wouldn't?
- Are there generic offer fields irrelevant to this type that create UI noise?
- Can the SDR explain THIS specific type of offer convincingly with available data?

---

## The Brand Essence Bridge

For all modes, verify the brand-to-offer data bridge. The SDR sells the offer *as this brand* — it never sells in a vacuum.

| Bridge | Check |
|--------|-------|
| Voice inheritance | Does the offer have access to brand voice/tone for SDR conversations? |
| Story inheritance | Can the SDR reference the brand's StoryBrand narrative when selling an offer? |
| Positioning inheritance | Does the offer know the brand's UVP, discriminator, and competitive enemies? |
| Proof inheritance | Can offer-level proof be supplemented by brand-level authority (certifications, media)? |
| Avatar consistency | Do offer-level avatars align with brand-level avatar definitions? |

If the bridge is broken (offer data lives in isolation from brand data), flag as **CRITICAL**.

---

## Audit Process

### Step 1: Determine Audit Mode

Parse the request for:
- **Mode**: Brand Studio (1), Offer Studio (2), or Specific Type (3)
- **Sub-scope** (optional): specific section, level, or type
- **Focus** (optional): schema only, prompts only, SDR readiness only, or full audit

If intent is ambiguous, ask. If it's clear (e.g., "audita el brand studio"), start immediately.

### Step 2: Read the Current State

Read the relevant source files listed for the mode. **Always read actual code — never assume from memory.** Use parallel reads where possible. For Mode 3, also read the `OFFER_TYPE_TO_DETAILS_MAPPING`.

### Step 3: Analyze Through Framework Lenses

For each applicable framework:
1. **Coverage**: Which atomic elements from `references/frameworks.md` are captured vs. missing?
2. **Depth**: Are captured elements specific enough to be actionable?
3. **Extraction quality**: Do LLM prompts produce the right kind of data?
4. **Deduplication**: Cross-reference the overlap map — flag redundantly captured concepts

### Step 4: Perform the Translation Audit

For each field, verify bidirectional translation:
- **User-facing label** → plain language a non-marketer solopreneur understands
- **Internal classification** → correctly mapped to the methodology concept AI agents consume
- **Extraction prompt** → produces specific, usable output (not "list the customer's pain points")

Example failure pattern: UI asks "What does your customer hate doing?" (good) → stored as generic `marketing_pain_points[]` (bad) → prompt says "list pain points" (bad — should distinguish effort-pains from outcome-pains).

### Step 5: Validate SDR Readiness

Verify collected data answers the SDR's core questions:

| SDR Question | Required Data | Brand Source | Offer Source |
|-------------|---------------|-------------|--------------|
| "Who am I talking to?" | Avatar/ICP | brand.avatars | offer.target_avatar_match |
| "What's their trigger to buy NOW?" | Critical Event | — | ??? (gap to check) |
| "What's at stake if they don't act?" | Rational + emotional impact | narrative.failure_consequence | offer.marketing_pain_points |
| "What am I actually selling?" | Dream Outcome + deliverables | — | offer.primary_outcome + deliverables |
| "Why should they believe this works?" | Proof stack | brand.authority + testimonials | offer.guarantee + RTBs |
| "What objections will they raise?" | Objections + rebuttals | — | offer.objections[] |
| "How do I create urgency?" | Scarcity/deadline/event | — | ??? (gap to check) |
| "What's the process after yes?" | Onboarding workflow | — | offer.onboarding_action + specific_details |
| "How does this brand talk?" | Voice, personality, style | brand.identity.voice_tone + style_analysis | — |

For Mode 3, add type-specific SDR questions:
- **Programs**: "How long? When does it start? Is there a waitlist?"
- **Services**: "What's included? Revisions? Turnaround?"
- **Events**: "Where? How many spots? Is it recorded?"
- **Subscriptions**: "Can I cancel anytime? What do I get each month?"

### Step 6: Validate the Product Blueprint

Verify a complete "Ficha Técnica" can be assembled:

| Blueprint Section | Required Elements |
|------------------|-------------------|
| **Target/ICP** | Who + psychographic profile + anti-avatar (who to disqualify) |
| **Critical Event** | The moment that creates urgency — SDR's #1 closing weapon |
| **Promise of Impact** | Rational (numbers) + Emotional (feelings) — both required |
| **Process (3–5 steps)** | From "I'm interested" to "I got results" — reduces anxiety |
| **Deliverables** | Tangible outputs with format and quantity |
| **Guarantee / Bonuses** | Risk reversal + value amplifiers |
| **Pricing Logic** | Why this price is fair + payment options |

### Step 7: Generate the Audit Report

Save to `docs/audits/` with a descriptive filename (e.g., `brand-studio-audit-2026-03-23.md`). Use the full report template defined in `references/audit-report-template.md`.

---

## Key Principles

- **One concept, one field.** If `BrandPositioning.discriminator` already covers Neumeier's Onliness Statement, audit its depth — don't add a redundant field.
- **Plain language for users, methodology for machines.** Users see "What does your customer dream of achieving?" — internally this maps to `dream_outcome`.
- **The SDR is the final consumer.** If a field can't be used to sell, it's not doing its job.
- **Don't recommend what already exists.** Improve existing fields rather than adding new ones.
- **Depth over breadth.** One deeply captured concept beats ten shallow checkboxes.
- **Extraction prompts are the real test.** A perfect schema with a weak prompt is effectively empty.
- **The ladder must be connected.** Always check: can the SDR guide someone from Level N to Level N+1?
- **Match framework depth to offer complexity.** Don't audit a FREE_RESOURCE against Casel's full productization framework.
