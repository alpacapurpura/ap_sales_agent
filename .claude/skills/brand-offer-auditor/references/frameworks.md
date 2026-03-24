# Framework Knowledge Base

This document contains the atomic decomposition of each marketing/branding framework that Nicolify's Brand Studio and Offer Studio should capture. The auditor uses this as ground truth to validate schema completeness.

## Table of Contents

1. [Brand Identity Model (Aaker)](#1-brand-identity-model-aaker)
2. [Brand Resonance Model (Keller)](#2-brand-resonance-model-keller)
3. [4D Branding Code (Gad)](#3-4d-branding-code-gad)
4. [The Onliness Statement (Neumeier)](#4-the-onliness-statement-neumeier)
5. [Brand Love Key (Positioning Framework)](#5-brand-love-key-positioning-framework)
6. [StoryBrand (Donald Miller)](#6-storybrand-donald-miller)
7. [Value Ladder (Russell Brunson)](#7-value-ladder-russell-brunson)
8. [Grand Slam Offer (Alex Hormozi)](#8-grand-slam-offer-alex-hormozi)
9. [Impact & Critical Event (Winning by Design)](#9-impact--critical-event-winning-by-design)
10. [Productization Architecture (Brian Casel)](#10-productization-architecture-brian-casel)
11. [Cross-Framework Overlap Map](#11-cross-framework-overlap-map)

---

## 1. Brand Identity Model (Aaker)

**Purpose:** Define what the brand IS — its essence as perceived by the market.
**Use in Nicolify:** Drives visual design, tone of voice, and positioning consistency.

### Atomic Elements

| Element | Description | Why it matters |
|---------|-------------|----------------|
| **Brand as Product** | Product scope, attributes, quality/value, uses, users, country of origin | Grounds the brand in tangible associations — "what do you actually sell?" |
| **Brand as Organization** | Organizational attributes (innovation, trustworthiness), local vs global | Signals whether the brand stands for something beyond its product |
| **Brand as Person** | Personality traits (sincere, exciting, competent, sophisticated, rugged), brand-customer relationship | Determines voice tone, visual mood, and how the brand "speaks" |
| **Brand as Symbol** | Visual imagery/metaphors, brand heritage | The shorthand — logos, colors, and recurring visual motifs |
| **Core Identity** | 2-4 timeless attributes that define the brand regardless of market/product changes | The unchanging DNA; if you remove this, the brand dies |
| **Extended Identity** | Additional attributes that add texture (tagline, sub-brands, sensory elements) | Fills in the picture but can evolve over time |
| **Value Proposition** | Functional benefits + emotional benefits + self-expressive benefits | The answer to "why should I choose you?" from three angles |

### What to audit
- Does the schema capture the brand's personality as distinct traits (not just a text blob)?
- Is there a separation between core identity (immutable) and extended identity (evolvable)?
- Does the value proposition capture all three benefit types (functional, emotional, self-expressive)?
- Can the system distinguish "Brand as Organization" attributes from "Brand as Product" attributes?

---

## 2. Brand Resonance Model (Keller)

**Purpose:** Build brand equity through a pyramid of customer relationship depth.
**Use in Nicolify:** Ensures the brand captures data at every level of customer connection, from awareness to loyalty.

### The Pyramid (bottom to top)

| Level | Pillar | Atomic Elements | Purpose |
|-------|--------|-----------------|---------|
| 1 - Identity | **Salience** | Category identification, needs satisfied, purchase/consumption occasions | "Who are you?" — Can the customer recall the brand in the right moments? |
| 2 - Meaning | **Performance** | Product reliability, service effectiveness, style/design, price, durability | "What are you?" — Functional associations |
| 2 - Meaning | **Imagery** | User profiles (demographic, psychographic), purchase/usage situations, personality/values, heritage | "What are you?" — Abstract associations and who uses you |
| 3 - Response | **Judgments** | Perceived quality, credibility (expertise, trustworthiness, likability), consideration, superiority | "What do I think about you?" — Rational evaluation |
| 3 - Response | **Feelings** | Warmth, fun, excitement, security, social approval, self-respect | "What do I feel about you?" — Emotional reaction |
| 4 - Relationship | **Resonance** | Behavioral loyalty (repeat purchase), attitudinal attachment ("love brand"), sense of community, active engagement (advocacy, co-creation) | "What about you and me?" — Deep connection |

### What to audit
- Does the brand schema capture data that maps to each pyramid level?
- Particularly: does the system capture **feelings** the brand evokes (not just functional benefits)?
- Is there a concept of **community** or **active engagement** — how the brand's audience participates?
- Does the schema distinguish between **judgments** (rational proof) and **feelings** (emotional response)?
- The Authority Vault partially covers "credibility" — but does the system capture the other judgment dimensions (consideration, superiority)?

---

## 3. 4D Branding Code (Thomas Gad)

**Purpose:** Define the brand through four experiential dimensions to create a culture, not just a product.
**Use in Nicolify:** Ensures the brand definition goes beyond features into community and identity territory.

### The Four Dimensions

| Dimension | Core Question | Atomic Elements |
|-----------|---------------|-----------------|
| **Functional** | "What does the brand do for me?" | Key benefit, differentiation, product/service attributes, practical utility |
| **Social** | "What does the brand say about me?" | Social identity signal, tribe/community membership, status/belonging, shared values |
| **Mental** | "How does the brand make me think differently?" | Mental models changed, knowledge/skills transferred, personal transformation, new perspective |
| **Spiritual** | "What larger purpose does the brand serve?" | Cause/mission beyond profit, ethical stance, societal contribution, the "why" behind the business |

### The Brand Code (synthesis)
The intersection of all 4 dimensions produces a **Brand Code** — a single sentence or phrase that captures the brand's total meaning. Example: Nike's brand code isn't "athletic shoes" — it's "authentic athletic performance."

### What to audit
- The **Social dimension** is often missing in brand tools — does the schema capture what the brand says about its users to others? This is critical for creator/infoproductor brands where the audience's identity is tied to the creator.
- The **Mental dimension** maps to transformation — does the system capture how the brand changes the customer's thinking?
- The **Spiritual dimension** should connect to mission/vision but go deeper — what systemic change does the brand stand for?
- Is there a synthesized "Brand Code" or equivalent that combines all four dimensions into one usable concept?

---

## 4. The Onliness Statement (Marty Neumeier)

**Purpose:** Force radical differentiation by filling in a single sentence template.
**Use in Nicolify:** The ultimate test of whether the brand has a defensible position.

### The Template

> Our [OFFERING TYPE] is the only [CATEGORY] that [UNIQUE BENEFIT/DIFFERENTIATOR] for [TARGET AUDIENCE] who [SPECIFIC NEED/CONTEXT] during [MOMENT/SITUATION] because [REASON TO BELIEVE].

### Atomic Elements

| Element | Description | Example |
|---------|-------------|---------|
| **Offering Type** | What you sell (product, service, platform, program) | "AI-powered sales automation platform" |
| **Category** | The competitive frame of reference | "marketing SaaS for solopreneurs" |
| **Unique Benefit** | The one thing ONLY you do | "replaces an entire sales team with one AI agent" |
| **Target Audience** | Who specifically benefits | "content creators and infoproductors" |
| **Specific Need** | The pain/desire that drives them | "who need to sell but hate cold outreach" |
| **Moment/Situation** | When the need is most acute | "when they're scaling beyond 1-on-1 sales" |
| **Reason to Believe** | Proof or mechanism that makes it credible | "because our agent learns their brand voice and closes like they would" |

### What to audit
- Does the `discriminator` field in BrandPositioning capture this level of specificity, or is it too vague?
- Is there a field for the **competitive category frame** (not just "industry")?
- Does the system capture the **moment/situation** — the trigger that makes someone need this brand?
- The Onliness Statement is the synthesis of positioning — does the system have a way to generate/validate this from the atomic data?

---

## 5. Brand Love Key (Positioning Framework)

**Purpose:** Map the brand's competitive position through emotional and rational lenses.
**Use in Nicolify:** Already implemented as `BrandPositioning` — this is the primary positioning framework.

### Atomic Elements (already in system)

| Element | Subelements |
|---------|-------------|
| **Competitive Environment** | technical_enemy, philosophical_enemy, direct_competitors[], indirect_competitors[] |
| **Consumer Insight** | tension, observation, implication |
| **Brand Benefits** | functional_benefits[], emotional_benefits[] |
| **Brand Values** | core_values[], personality_traits[], archetype |
| **Reasons to Believe** | type (dato/caso_exito/certificacion/tecnologia/proceso), statement, proof_url |
| **Discriminator** | The unique irreplaceable factor |
| **Brand Essence** | 2-3 words capturing the soul |
| **UVP** | "Solo nosotros [capacidad] porque [razon]" |

### What to audit
- This is well-implemented. Main concern: does the `Consumer Insight` go deep enough? The tension-observation-implication triad should capture a real psychological conflict, not just a surface pain point.
- Are `emotional_benefits` truly emotional (feelings) or disguised functional benefits?
- Does the `philosophical_enemy` capture a genuine worldview opposition (not just a competitor critique)?

---

## 6. StoryBrand (Donald Miller)

**Purpose:** Position the customer as the hero and the brand as the guide in a narrative framework.
**Use in Nicolify:** Already implemented as `BrandNarrative`.

### Atomic Elements (already in system)

| Element | Subelements |
|---------|-------------|
| **Hero** | identity (who the customer is), desire (what they want) |
| **Problem** | villain, external_problem, internal_problem, philosophical_problem |
| **Guide** | empathy_statement, authority_statement |
| **Plan** | 3-4 steps with step_number, title, description |
| **Call to Action** | direct_cta, transitional_cta |
| **Success** | success_transformation |
| **Failure** | failure_consequence |
| **One-liner** | Single sentence story |

### What to audit
- Does the `villain` represent a systemic force (not just "lack of time")? Good villains are specific: "the complexity of modern marketing tools that were designed for agencies, not creators."
- Is `internal_problem` truly internal (an emotion/belief) vs just another external problem rephrased?
- Does `success_transformation` paint a vivid after-picture, or is it generic ("grow your business")?
- The `philosophical_problem` should connect to a larger injustice — "It's not fair that..."

---

## 7. Value Ladder (Russell Brunson)

**Purpose:** Structure offers in ascending value/price to move customers through the funnel.
**Use in Nicolify:** Implemented as `OfferValueLevel` (N0 through N6) with 21 offer types.

### The Ladder

| Level | Purpose | Price Range | Relationship |
|-------|---------|-------------|--------------|
| **Level 0 (Free)** | Lead magnet — exchange value for attention/contact | $0 | Gateway to trust |
| **Level 1 (Low-ticket)** | Tripwire — convert freebie users into paying customers | $7-$97 | Proof of value |
| **Level 2 (Mid-ticket)** | Core offer — the main transformation | $97-$997 | Main revenue driver |
| **Level 3 (High-ticket)** | Premium access — personalized attention | $997-$5,000 | Deep engagement |
| **Level 4 (Productized)** | Done-for-you or retainer — recurring revenue | $2,000-$10,000/mo | Ongoing relationship |
| **Level 5 (Elite)** | Exclusive experience — mastermind/retreat | $10,000-$50,000 | Inner circle |
| **Level 6 (Enterprise)** | Custom/corporate — highest value | $50,000+ | Strategic partnership |

### What to audit
- Does each level have a clear **ascension mechanism** — how does someone move from Level N to Level N+1?
- Is there a `downsell_offer_id` and `upsell_offer_id` for every offer? The ladder only works if the rungs are connected.
- Does the system enforce that Level 0 offers exist? Without a free entry point, the funnel is broken.
- Are **tripwire offers** (Level 1) priced to cover ad costs, not to profit? The system should understand this intent.

---

## 8. Grand Slam Offer (Alex Hormozi)

**Purpose:** Make the offer so good that people feel stupid saying no.
**Use in Nicolify:** Partially implemented across offer fields. This is the most important framework for offer construction.

### The Value Equation

```
Value = (Dream Outcome × Perceived Likelihood of Achievement) / (Time Delay × Effort & Sacrifice)
```

### Atomic Elements

| Element | Description | What to capture |
|---------|-------------|-----------------|
| **Dream Outcome** | The ideal end state the customer wants | Not "learn marketing" but "wake up to sales notifications while you sleep" |
| **Perceived Likelihood** | How confident the customer is it will work FOR THEM | Proof, guarantees, case studies, specificity of promise |
| **Time Delay** | How long until they see results | "First results in 48 hours" vs "Results in 6 months" |
| **Effort & Sacrifice** | What the customer has to DO and GIVE UP | "Just answer 10 questions" vs "Rebuild your entire website" |

### Offer Stack Components

| Component | Description | Purpose |
|-----------|-------------|---------|
| **Core Offer** | The main thing you're selling | The transformation |
| **Bonuses** | Additional items that reduce effort/time | Increase perceived value without raising price |
| **Urgency** | Deadline or scarcity | Compress decision time |
| **Guarantee** | Risk reversal | Increase perceived likelihood |
| **Naming** | The offer name itself | "The 90-Day Revenue Machine" > "Marketing Course" |

### What to audit
- **CRITICAL**: Does the schema have explicit fields for dream outcome vs primary_outcome? `primary_outcome` exists but is it framed as a DREAM (aspirational, vivid) or as a feature?
- Is `time_to_value` captured and specific (e.g., "7 days") or vague?
- **GAP**: There's no explicit field for "effort & sacrifice required from the customer" — what do they need to DO?
- **GAP**: There's no explicit field for "perceived likelihood" mechanisms — beyond guarantee, what increases confidence?
- Are bonuses structured as separate items in `deliverables` or `includes_offers`? The system should distinguish between core deliverables and bonuses.
- Does the `guarantee_type` enum cover Hormozi's spectrum? (Unconditional, Conditional, Anti-Guarantee, Performance-Based)
- Is there a field for **urgency/scarcity** (limited spots, deadline, cohort size)?

---

## 9. Impact & Critical Event (Winning by Design)

**Purpose:** Understand what triggers a buyer to act NOW and what happens if they don't.
**Use in Nicolify:** Critical for the SDR agent to know WHEN to push for a close.

### Atomic Elements

| Element | Description | SDR Usage |
|---------|-------------|-----------|
| **Critical Event** | The external event that creates urgency (deadline, season, life change, competitor move) | "Your launch is in 3 weeks and you still don't have a sales funnel?" |
| **Impact (Rational)** | Measurable business consequences of inaction — money lost, time wasted, opportunity cost | "Every month without this, you're leaving $X on the table" |
| **Impact (Emotional)** | Personal/emotional consequences — stress, embarrassment, fear, frustration | "How does it feel to watch competitors close the deals you should be closing?" |
| **Required Capabilities** | What the buyer needs to solve the problem (maps to your offer's features) | Bridges "I have a problem" to "your product solves it" |
| **Decision Criteria** | How the buyer evaluates solutions (price, speed, simplicity, proof) | Tells the SDR what objections to preempt |
| **Metrics** | How the buyer measures success after purchase | Aligns expectations and reduces churn |

### What to audit
- **CRITICAL GAP**: There's no `critical_event` field in the offer schema. The SDR cannot know WHEN to push urgency without this.
- **GAP**: `Impact` is partially covered by `marketing_pain_points` but there's no separation between rational impact (numbers) and emotional impact (feelings).
- Does the system capture `decision_criteria` for the buyer? This directly feeds objection handling.
- Are there fields for post-purchase `success_metrics`? Without these, the SDR can't set proper expectations.

---

## 10. Productization Architecture (Brian Casel)

**Purpose:** Transform custom services into repeatable, scalable offerings with clear boundaries.
**Use in Nicolify:** Essential for service-based offers (Levels 3-6) to avoid scope creep and enable AI selling.

### Atomic Elements

| Element | Description | Why it matters for AI |
|---------|-------------|----------------------|
| **Scope** | Exactly what's included AND what's not included | The SDR must be able to say "this includes X but not Y" without ambiguity |
| **Workflow** | Step-by-step process from purchase to delivery | Reduces buyer anxiety: "Here's exactly what happens after you pay" |
| **Deliverables** | Tangible outputs the customer receives (formats, quantities) | Makes abstract services concrete: "You'll receive 3 videos, 1 PDF, and 2 live calls" |
| **Timeline** | Expected duration from start to completion | Sets expectations: "4 weeks from kickoff to final delivery" |
| **Fixed Price** | A single, non-negotiable price (or clear tiers) | Eliminates the "how much will this cost me?" anxiety |
| **Exclusions** | What's explicitly NOT included | Prevents scope creep: "Revisions beyond 2 rounds are billed separately" |

### What to audit
- Does the offer schema capture **exclusions** (what's NOT included)? This is as important as inclusions for the SDR.
- Is there a structured **workflow** field (ordered steps from purchase to delivery)?
- The `deliverables` list exists but — is each deliverable specific enough? "1 video" vs "1 professionally edited 10-minute training video in MP4 format"
- Does `time_to_value` map to Casel's timeline, or is it a different concept? (time_to_value = when results show, timeline = when delivery completes — these are different)
- Are exclusions/limitations documented for the SDR to handle "does it include X?" questions?

---

## 11. Cross-Framework Overlap Map

This is the critical reference for avoiding duplication. Many frameworks describe the same concept with different names.

### Concept → Framework Mapping

| Unified Concept | Aaker | Keller | Gad 4D | Neumeier | Brand Love Key | StoryBrand | Hormozi | WbD | Casel |
|-----------------|-------|--------|--------|----------|---------------|------------|---------|-----|-------|
| **Who we are (identity)** | Core Identity | Salience | Functional | Offering Type | Brand Essence | Guide | - | - | - |
| **What we believe (values)** | Brand as Org | - | Spiritual | - | Brand Values | Phil. Problem | - | - | - |
| **How we're different** | Value Prop | Superiority | - | Onliness | Discriminator + UVP | - | - | - | - |
| **Who we serve** | Brand as Product (users) | Imagery (user profiles) | Social | Target Audience | Consumer Insight | Hero Identity | - | - | - |
| **Their pain** | - | - | - | Specific Need | Consumer Insight (tension) | External Problem | - | Impact (emotional) | - |
| **Their deeper pain** | - | - | Mental | - | - | Internal Problem | Effort & Sacrifice | Impact (emotional) | - |
| **The dream result** | - | Feelings | Mental | - | Emotional Benefits | Success Transform | Dream Outcome | - | - |
| **Why us (proof)** | - | Judgments (credibility) | - | Reason to Believe | Reasons to Believe | Authority | Perc. Likelihood | - | - |
| **Community/tribe** | - | Resonance (community) | Social | - | - | - | - | - | - |
| **Personality/voice** | Brand as Person | Imagery (personality) | Social | - | Personality Traits | - | - | - | - |
| **Urgency trigger** | - | - | - | Moment/Situation | - | - | Urgency | Critical Event | - |
| **What they get** | - | Performance | Functional | - | Functional Benefits | Plan | Core Offer + Bonuses | Required Capabilities | Deliverables |
| **How it works** | - | - | - | - | - | Plan (steps) | - | - | Workflow |
| **Risk reversal** | - | - | - | - | - | - | Guarantee | - | - |
| **Price justification** | - | Judgments (quality/value) | - | - | - | - | Value Equation | - | Fixed Price |
| **Post-purchase vision** | - | Resonance (loyalty) | - | - | - | Success Transform | Dream Outcome | Metrics | Timeline |

### Key Deduplication Rules

1. **"Pain" appears in 5 frameworks** — the system should have ONE atomic pain model with facets (external, internal, philosophical, rational impact, emotional impact), not 5 separate pain fields.
2. **"Differentiation" appears in 4 frameworks** — Aaker's Value Prop, Keller's Superiority, Neumeier's Onliness, and Brand Love Key's Discriminator are all the same concept at different zoom levels. One field with depth, not four shallow fields.
3. **"Proof/credibility" appears in 3 frameworks** — Keller's Judgments, Brand Love Key's RTBs, and Hormozi's Perceived Likelihood all need social proof. One unified proof system.
4. **"Transformation" is shared** — StoryBrand's Success Transformation, Hormozi's Dream Outcome, and Gad's Mental dimension all describe the after-state. One vivid description, used everywhere.
5. **"Urgency" has two homes** — Neumeier's Moment/Situation and WbD's Critical Event both describe WHEN someone needs this. The SDR needs this to time outreach.
