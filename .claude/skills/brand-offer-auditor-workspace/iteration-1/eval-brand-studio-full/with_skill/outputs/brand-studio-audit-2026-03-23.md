# Brand Studio Audit Report
> **Scope:** Brand Studio (Full)
> **Date:** 2026-03-23
> **Frameworks Applied:** Aaker (PRIMARY), Keller (PRIMARY), Gad 4D (PRIMARY), Neumeier (PRIMARY), Brand Love Key (PRIMARY), StoryBrand (PRIMARY), Hormozi (SECONDARY), WbD (SECONDARY), Casel (SECONDARY)

## Executive Summary

The Brand Studio has solid foundational coverage of the Brand Love Key (Positioning) and StoryBrand (Narrative) frameworks -- both are implemented with proper atomic decomposition and dedicated extraction prompts. However, the system has a **critical bridge failure**: the SDR agent template (`agent_identity.j2`) only consumes `positioning.unique_value_proposition` from the entire Brand Love Key framework and **zero fields from BrandNarrative** -- meaning the richly captured positioning and narrative data never reaches the sales conversation. The single most impactful fix is wiring the existing brand data into the SDR prompt template.

Beyond the bridge failure, the primary gaps are: (1) no capture of the brand's social/community dimension (Gad, Keller Resonance), (2) no structured emotional feelings taxonomy (Keller Level 3), (3) the Avatar model is too shallow to serve as a real ICP profile, and (4) the Onliness Statement cannot be synthesized because the schema lacks the "moment/situation" trigger field.

## Findings

### CRITICAL -- System Cannot Function Without This

- [ ] **[C-01] SDR Agent Does Not Consume Brand Positioning Data** (Framework: Brand Love Key, StoryBrand, all)
  - **Gap**: The `agent_identity.j2` template receives the full `positioning` dict but only renders `positioning.unique_value_proposition`. It does NOT render: `discriminator`, `brand_essence`, `competitive_environment` (enemies), `insight` (consumer tension), `benefits` (functional/emotional), `values`, or `reasons_to_believe`. The entire BrandNarrative (hero, problem, guide, plan, CTA, outcome, one_liner) is not even passed to the template -- `narrative` is never extracted in `knowledge_builder.py`.
  - **Impact**: The SDR has no access to: who the enemy is (can't position against competitors), what the consumer tension is (can't build empathy), what the emotional benefits are (can't connect emotionally), what the brand's story arc is (can't guide the customer through the hero journey), what the failure consequence is (can't create urgency). The SDR operates as a generic product-feature lister instead of a brand storyteller.
  - **Recommendation**:
    1. In `knowledge_builder.py`, extract `narrative = brand_data.get("narrative", {}) or {}` and pass it to the template render call.
    2. In `agent_identity.j2`, add sections that render: positioning enemies, consumer insight tension, brand benefits, discriminator, brand essence, narrative hero/problem/guide/outcome/one_liner.
    3. Example template additions:
       - `{% if positioning.discriminator %}**Lo que nos hace unicos:** {{ positioning.discriminator }}{% endif %}`
       - `{% if positioning.competitive_environment %}**Enemigo tecnico:** {{ positioning.competitive_environment.technical_enemy }}{% endif %}`
       - `{% if narrative and narrative.one_liner %}**Nuestra historia en una frase:** {{ narrative.one_liner }}{% endif %}`
       - `{% if narrative and narrative.outcome %}**Si no actuan:** {{ narrative.outcome.failure_consequence }}{% endif %}`
  - **Affected files**:
    - `/home/chris/AISALESHT/backend/src/modules/sales_agent/application/services/knowledge_builder.py` (lines 63, 78-98)
    - `/home/chris/AISALESHT/backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2` (lines 10-27)

- [ ] **[C-02] Avatar Model Too Shallow for ICP Profiling** (Framework: Aaker Brand-as-Product users, Keller Imagery, Gad Social, Neumeier Target Audience)
  - **Gap**: The `Avatar` entity has only 4 meaningful fields: `name`, `icp_description` (free text blob), `anti_avatar` (free text blob), and `scope`. There is no structured demographic data, no psychographic profile, no behavioral triggers, no purchase occasion mapping, no emotional drivers. The frontend form (`avatar-form.tsx`) confirms this -- it's just a name, a textarea for ICP, and a textarea for anti-avatar.
  - **Impact**: The SDR gets a vague text description of "who to talk to" but cannot: segment by behavior (purchase triggers), identify psychological drivers (fears, aspirations), adapt language to psychographic profile, or recognize disqualification signals with specificity. The AI has to guess what "Emprendedores Tech" means psychographically.
  - **Recommendation**: Restructure `Avatar` entity with structured fields:
    - `demographics`: age_range, gender, location, income_level, education
    - `psychographics`: fears[], aspirations[], values[], identity_labels[] ("I am a...")
    - `behavioral_triggers`: purchase_occasions[], decision_criteria[], information_sources[]
    - `communication_preferences`: preferred_channel, formality_level, response_speed_expectation
    - Keep `icp_description` as a synthesis field, but add structured sub-fields the SDR can query programmatically.
  - **Affected files**:
    - `/home/chris/AISALESHT/backend/src/modules/brand/domain/entities.py` (Avatar class, lines 11-23)
    - `/home/chris/AISALESHT/frontend/src/features/brand/sections/avatars/avatar-form.tsx`
    - `/home/chris/AISALESHT/frontend/src/features/brand/types/index.ts` (no Avatar type defined in brand types)

### HIGH -- Significant Quality Degradation

- [ ] **[H-01] No Community/Social Dimension Captured** (Framework: Gad 4D Social, Keller Resonance)
  - **Gap**: There is no field anywhere in the Brand Studio schema that captures what the brand says about its users to others (social signaling), community membership/belonging, or active audience engagement patterns. Gad's Social dimension ("What does the brand say about me?") and Keller's Resonance level (community, active engagement, behavioral loyalty) are completely absent.
  - **Impact**: For creator/infoproductor brands (Nicolify's target user), the social dimension is arguably the most important -- the audience's identity is tied to the creator. The SDR cannot leverage "join the tribe" or "become part of the community" selling angles because no data exists to define what that community looks like.
  - **Recommendation**: Add to `BrandPositioning` or as a new top-level section:
    - `community_identity`: What being part of this brand's audience says about you (1-2 sentences)
    - `tribe_name`: Optional name for the community (e.g., "Los Visionarios", "The 5AM Club")
    - `engagement_rituals`: How the community participates (weekly calls, Slack channel, hashtags)
    - `social_proof_metric`: Quantified community size ("5,000+ miembros activos")
    - Add extraction logic to the positioning or narrative prompt.
  - **Affected files**:
    - `/home/chris/AISALESHT/backend/src/modules/brand/domain/positioning.py` or new file
    - `/home/chris/AISALESHT/frontend/src/features/brand/types/index.ts`

- [ ] **[H-02] No Structured Feelings Taxonomy** (Framework: Keller Level 3 -- Feelings)
  - **Gap**: Keller's Resonance pyramid Level 3 distinguishes **Judgments** (rational evaluation: quality, credibility, consideration, superiority) from **Feelings** (emotional response: warmth, fun, excitement, security, social approval, self-respect). The system captures `emotional_benefits` in BrandPositioning but these are output-oriented ("what you get emotionally") rather than brand-association-oriented ("what you feel ABOUT the brand"). There is no explicit field for the feelings the brand evokes in people.
  - **Impact**: The SDR cannot modulate its emotional register. When someone says "I feel overwhelmed", the SDR doesn't know if the brand's emotional territory is "warmth and security" or "excitement and empowerment" -- two very different empathetic responses.
  - **Recommendation**: Add `brand_feelings: List[str]` to `BrandPositioning.values` or as a sibling field. Use Keller's taxonomy as guidance labels: warmth, fun, excitement, security, social_approval, self_respect. The extraction prompt should ask: "What emotions does someone feel when they think about this brand? Not what the brand delivers, but how the brand makes them FEEL."
  - **Affected files**:
    - `/home/chris/AISALESHT/backend/src/modules/brand/domain/positioning.py` (BrandValues class)
    - `/home/chris/AISALESHT/backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_positioning.j2`

- [ ] **[H-03] Voice Tone is a Single Unstructured String** (Framework: Aaker Brand-as-Person, Keller Imagery personality)
  - **Gap**: `BrandIdentity.voice_tone` is `Optional[str]` with description "Voice tone descriptors (e.g. 'conversacional, aspiracional')". The extraction prompt asks for "2-3 adjetivos separados por coma". Meanwhile, the Voice Clone feature (`voice-form.tsx`, `style.py`) generates a rich `style_profile` (tone, signature_phrases, response_structure) and `custom_system_instruction` -- but this is stored on the **User** model, not the brand. These two voice systems are disconnected.
  - **Impact**: The SDR receives `identity.voice_tone` as a vague string like "conversacional, aspiracional" which is not actionable. The rich style profile from the Voice Clone feature (signature phrases, response structure) is NOT passed to the SDR -- it's stored per-user, not per-brand.
  - **Recommendation**:
    1. Restructure `voice_tone` into a `BrandVoice` value object: `tone_adjectives: List[str]`, `signature_phrases: List[str]`, `communication_style: str`, `formality_level: str` (formal/casual/mixed), `response_structure: str`.
    2. Bridge the Voice Clone output (`style_profile`) to `BrandSettings` so the style analysis feeds the brand, not just the user.
    3. Pass the full voice profile to the SDR template.
  - **Affected files**:
    - `/home/chris/AISALESHT/backend/src/modules/brand/domain/identity.py` (BrandIdentity.voice_tone)
    - `/home/chris/AISALESHT/backend/src/modules/brand/api/style.py` (saves to User, not Brand)
    - `/home/chris/AISALESHT/backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2`

- [ ] **[H-04] No "Moment/Situation" Trigger Field** (Framework: Neumeier Onliness, WbD Critical Event)
  - **Gap**: Neumeier's Onliness Statement requires a "during [MOMENT/SITUATION]" element -- the circumstance that makes someone need this brand right now. WbD's Critical Event maps to the same concept. Neither exists in the brand schema. The `ConsumerInsight.tension` captures a psychological truth but not a temporal/situational trigger.
  - **Impact**: The system cannot generate a proper Onliness Statement. More critically, the SDR has no concept of WHEN someone needs this brand -- it can't reference life events, business milestones, or seasonal triggers that create urgency at the brand level (offer-level critical events are a separate gap).
  - **Recommendation**: Add `purchase_trigger_moments: List[str]` to `BrandPositioning` or `ConsumerInsight`. Prompt guidance: "What life events, business moments, or situations make someone suddenly need this brand? Examples: 'launching their first online course', 'hitting a revenue ceiling', 'losing a key employee'."
  - **Affected files**:
    - `/home/chris/AISALESHT/backend/src/modules/brand/domain/positioning.py` (ConsumerInsight or BrandPositioning)
    - `/home/chris/AISALESHT/backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_positioning.j2`

- [ ] **[H-05] Strategy/Mission is Disconnected from StoryBrand Guide** (Framework: StoryBrand, Aaker Brand-as-Organization)
  - **Gap**: `BrandStory.mission` and `BrandStory.vision` live in the Story section, while `StoryBrandGuide.empathy_statement` and `authority_statement` live in Narrative. Both describe "who the brand is as a guide" but from different angles. The SDR template renders `strategy.mission` (from BrandStory) but NOT the guide statements from BrandNarrative. There is no cross-reference or synthesis.
  - **Impact**: The brand has two disconnected self-descriptions: one strategic (mission/vision) and one narrative (guide empathy/authority). Neither is complete alone. The SDR gets the strategic mission (formal, abstract) but not the empathetic guide voice (warm, relatable) -- exactly the wrong choice for sales conversations.
  - **Recommendation**: The SDR template should prioritize the StoryBrand Guide statements over the formal mission for sales conversations. Add to `agent_identity.j2`: `{% if narrative.guide %}**Empatia:** {{ narrative.guide.empathy_statement }} / **Autoridad:** {{ narrative.guide.authority_statement }}{% endif %}`. Keep mission for formal contexts (landing pages, about pages).
  - **Affected files**:
    - `/home/chris/AISALESHT/backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2`

### MEDIUM -- Improvement Opportunity

- [ ] **[M-01] No Brand Code Synthesis** (Framework: Gad 4D)
  - **Gap**: Gad's 4D model produces a "Brand Code" -- a single sentence synthesizing all four dimensions (functional, social, mental, spiritual). The system has `brand_essence` (2-3 words) and `unique_value_proposition` but nothing that captures the brand's total meaning across all dimensions in one synthesized concept.
  - **Impact**: `brand_essence` is too short to carry the full brand meaning. The UVP is capability-focused. A Brand Code would give the SDR a north-star phrase for every interaction. Low urgency because `brand_essence` + `one_liner` partially cover this need.
  - **Recommendation**: Consider enriching the extraction prompt for `brand_essence` to ask for a synthesis across all four dimensions rather than just "the soul of the brand". Alternatively, add a `brand_code: Optional[str]` field (one sentence, not 2-3 words) that captures the intersection of functional utility, social signaling, mental transformation, and spiritual purpose.
  - **Affected files**:
    - `/home/chris/AISALESHT/backend/src/modules/brand/domain/positioning.py`
    - `/home/chris/AISALESHT/backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_positioning.j2`

- [ ] **[M-02] Value Proposition Lacks Three-Benefit Structure** (Framework: Aaker Value Proposition)
  - **Gap**: Aaker's Value Proposition has three dimensions: functional benefits, emotional benefits, and **self-expressive benefits** ("what does using this brand say about me?"). The system captures functional and emotional benefits in `BrandBenefits` but lacks self-expressive benefits -- the identity signal that using this brand sends to others.
  - **Impact**: For creator brands, self-expressive benefits are powerful: "I'm part of [Creator]'s community" signals identity. Without this, the SDR can only sell on utility and feelings, missing the identity/status angle.
  - **Recommendation**: Add `self_expressive_benefits: List[str]` to `BrandBenefits`. Prompt guidance: "What does being a customer of this brand say about someone? What identity does it signal?"
  - **Affected files**:
    - `/home/chris/AISALESHT/backend/src/modules/brand/domain/positioning.py` (BrandBenefits class)
    - `/home/chris/AISALESHT/backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_positioning.j2`

- [ ] **[M-03] Methodology/Strategy Pillar Extraction Lacks Connection to Narrative Plan** (Framework: StoryBrand Plan, Casel Workflow)
  - **Gap**: `BrandStrategy.methodology_pillars` captures the brand's proprietary framework, and `BrandNarrative.plan` captures the StoryBrand 3-4 step plan. Both describe "how the brand works" but from different angles. There is no connection between them, and the SDR template renders neither -- it only gets `strategy.mission` which moved to `story`.
  - **Impact**: Low urgency. The methodology is for authority-building (landing pages, about sections), while the plan is for sales conversations. But the SDR should ideally reference the plan steps when explaining "how it works."
  - **Recommendation**: Ensure the SDR template renders `narrative.plan` steps. The methodology and plan can remain separate -- they serve different audiences.
  - **Affected files**:
    - `/home/chris/AISALESHT/backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2`

- [ ] **[M-04] Authority Vault and Testimonials Not Structurally Connected to RTBs** (Framework: Keller Judgments, Brand Love Key RTBs)
  - **Gap**: The system has three separate proof mechanisms: `BrandPositioning.reasons_to_believe` (RTBs with type/statement/proof_url), `BrandSettings.authority_vault` (institutional authority items), and `BrandSettings.testimonials` (customer social proof). These are stored and managed independently with no cross-reference.
  - **Impact**: The SDR template renders testimonials separately and does not render RTBs at all. An RTB like "500+ negocios automatizados" overlaps with a testimonial of type "brand impact number". The SDR may cite the same proof twice or miss the strongest proof entirely.
  - **Recommendation**: Conceptually, these are three facets of one proof system. For now, ensure the SDR template renders RTBs alongside testimonials. Longer term, consider a unified `ProofStack` that categorizes all proof by type (social, institutional, data, process) for the SDR to draw from contextually.
  - **Affected files**:
    - `/home/chris/AISALESHT/backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2`
    - `/home/chris/AISALESHT/backend/src/modules/brand/domain/positioning.py` (ReasonToBelieve)

- [ ] **[M-05] Extraction Prompt for Consumer Insight Could Be Deeper** (Framework: Brand Love Key)
  - **Gap**: The positioning extraction prompt asks for `tension` as "La verdad incomoda que el consumidor siente pero no articula" with the format "[Audiencia] quiere [deseo] pero [barrera real]." This is good but tends to produce surface-level tensions. The prompt doesn't push for the emotional DEPTH of the tension -- the difference between "quiere crecer pero no tiene tiempo" (surface) and "quiere sentirse competente en un mundo digital que cambia mas rapido de lo que puede aprender" (deep).
  - **Impact**: Surface-level insights produce surface-level SDR empathy. The difference between a generic and a great sales conversation is the depth of the opening insight.
  - **Recommendation**: Enhance the insight extraction prompt to include: "La tension debe revelar un CONFLICTO EMOCIONAL, no solo una barrera practica. Buscar la contradiccion entre lo que el consumidor CREE de si mismo y lo que EXPERIMENTA en la realidad. Ejemplo: 'Se ven como expertos en su campo, pero se sienten impostores cuando tienen que vender.'"
  - **Affected files**:
    - `/home/chris/AISALESHT/backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_positioning.j2`

- [ ] **[M-06] No Core vs Extended Identity Separation** (Framework: Aaker)
  - **Gap**: Aaker distinguishes Core Identity (2-4 timeless, immutable attributes) from Extended Identity (evolving texture: tagline, sub-brands, sensory elements). The BrandIdentity model mixes both in a flat structure. Keywords, tagline, archetype, voice_tone, and description coexist without a hierarchy of permanence.
  - **Impact**: When the brand evolves (new tagline, new visuals), there is no guidance on what MUST stay the same. An AI asset generator might change the archetype during a "refresh" because it doesn't know it's core identity. Low immediate impact on SDR but affects long-term brand consistency.
  - **Recommendation**: Consider adding `core_identity_attributes: List[str]` (2-4 items the user marks as immutable) to BrandIdentity or BrandPositioning. This is low-effort and gives the system a "don't touch this" signal for extraction updates.
  - **Affected files**:
    - `/home/chris/AISALESHT/backend/src/modules/brand/domain/identity.py`

## Deduplication Opportunities

| Concept | Current Fields | Frameworks | Recommendation |
|---------|---------------|------------|----------------|
| **Archetype** | `BrandIdentity.archetype`, `BrandValues.archetype` | Aaker (Person), Brand Love Key (Values) | Unify into `BrandValues.archetype` only. Remove from `BrandIdentity` or make it a read-through that delegates to positioning.values.archetype. Currently both can hold different values. |
| **Voice/Personality** | `BrandIdentity.voice_tone` (string), `BrandValues.personality_traits` (list), `KeyFigure.communication_style` (per-person string), User.style_profile (from Voice Clone) | Aaker (Person), Keller (Imagery), Gad (Social) | These are legitimately different: brand-level tone, brand personality traits, individual team member style, and AI-cloned style. Keep separate but ensure the SDR template has a clear priority: Voice Clone > brand voice_tone > personality_traits as fallback. |
| **Mission/Vision** | `BrandStory.mission`, `BrandStory.vision` | Aaker (Org), Gad (Spiritual) | Keep in BrandStory. These serve the story/about context. The StoryBrand Guide serves sales context. No duplication -- different lenses. |
| **Pain/Problem** | `StoryBrandProblem.external_problem`, `StoryBrandProblem.internal_problem`, `StoryBrandProblem.philosophical_problem`, `ConsumerInsight.tension` | StoryBrand, Brand Love Key, Hormozi (in offers) | These are complementary, not duplicative. StoryBrand decomposes pain into 3 layers. ConsumerInsight captures the market-level tension. Keep all but ensure the SDR template surfaces the internal_problem (most emotionally resonant for sales) alongside the tension. |
| **Proof** | `ReasonToBelieve[]`, `BrandAuthorityItem[]`, `BrandTestimonial[]` | Keller (Judgments), Brand Love Key (RTBs), StoryBrand (Authority) | Three facets of proof: rational (RTBs), institutional (Authority), social (Testimonials). Keep separate but build a unified SDR proof section that draws from all three. |

## Methodology Coverage Matrix

| Framework | Weight | Coverage | Key Gaps |
|-----------|--------|----------|----------|
| **Aaker (Brand Identity)** | PRIMARY | 5/7 atomic elements | Missing: Core vs Extended separation, Self-expressive benefits, Brand-as-Organization attributes (beyond mission/vision) |
| **Keller (Brand Resonance)** | PRIMARY | 3/6 pyramid levels fully | Missing: Feelings taxonomy (Level 3), Community/Resonance (Level 4), Superiority judgment (Level 3). Salience partially covered by identity keywords. |
| **Gad (4D Branding Code)** | PRIMARY | 2/4 dimensions | Functional: YES (benefits). Spiritual: PARTIAL (mission/vision). Social: NO (community, tribe, identity signal). Mental: PARTIAL (success_transformation covers transformation). No Brand Code synthesis. |
| **Neumeier (Onliness)** | PRIMARY | 5/7 template slots | Missing: Moment/Situation trigger, Category frame (industry is too generic). Discriminator + UVP cover the core but can't synthesize a full Onliness Statement without temporal trigger. |
| **Brand Love Key** | PRIMARY | 8/8 elements | FULLY COVERED in schema. Main issue: extraction prompt depth (insight) and SDR consumption (only UVP reaches the agent). |
| **StoryBrand** | PRIMARY | 7/7 elements | FULLY COVERED in schema. Main issue: SDR does not consume ANY narrative data. |
| **Hormozi (Grand Slam)** | SECONDARY | N/A (offer domain) | Brand-level light check: brand proof feeds perceived likelihood -- partially covered via RTBs and testimonials. |
| **WbD (Impact/Critical Event)** | SECONDARY | 0/6 at brand level | No brand-level critical event or urgency trigger. This is primarily an offer concern, but the brand should have a "moment/situation" field per Neumeier. |
| **Casel (Productization)** | SECONDARY | N/A (offer domain) | Not applicable at brand level. |

## SDR Readiness Score

| SDR Question | Answerable? | Source Field(s) | Gap |
|-------------|-------------|-----------------|-----|
| "Who am I talking to?" | PARTIAL | `Avatar.name`, `Avatar.icp_description` (free text) | Avatar is unstructured. No demographics, psychographics, or behavioral triggers. SDR gets a vague description. |
| "What's their trigger to buy NOW?" | NO | -- | No critical event or purchase trigger moment at brand level. |
| "What's at stake if they don't act?" | PARTIAL | `BrandNarrative.outcome.failure_consequence` exists in schema | But SDR template does NOT render it. Data exists, bridge is broken. |
| "What am I actually selling?" | YES | `BrandIdentity.description`, `positioning.unique_value_proposition` | SDR gets the UVP. Could be richer with discriminator. |
| "Why should they believe this works?" | PARTIAL | `testimonials[]` rendered in SDR template, `authority_vault[]` NOT rendered, `reasons_to_believe[]` NOT rendered | SDR only sees testimonials. Authority and RTBs are invisible to the agent. |
| "What objections will they raise?" | NO (brand level) | -- | Objections are offer-level, not brand-level. Acceptable -- the offer audit should cover this. |
| "How do I create urgency?" | NO | -- | No urgency/scarcity fields at brand level. No purchase trigger moments. |
| "What's the process after yes?" | PARTIAL | `BrandNarrative.plan` (3-4 steps) exists in schema | But SDR template does NOT render it. Data exists, bridge is broken. |
| "How does this brand talk?" | PARTIAL | `BrandIdentity.voice_tone` (vague string) | Voice Clone style_profile is richer but lives on User model, not Brand. SDR gets "conversacional, aspiracional" -- not enough to modulate tone. |

**Overall SDR Readiness: 1.5/9 questions fully answerable** (only "What am I selling?" is solid; partial credit for testimonials)

The devastating finding is that several questions are PARTIAL not because data is missing from the schema, but because **existing data is not wired to the SDR template**. Fixing C-01 alone would jump readiness to ~5/9.

## Brand Essence Bridge

This is a Brand Studio audit, so the full bridge table applies to Offer/Specific Type audits. However, the intra-brand bridge between Brand Studio sections and the SDR is critical:

| Bridge | Connected? | How | Gap |
|--------|-----------|-----|-----|
| Voice inheritance | PARTIAL | `identity.voice_tone` string passed to SDR template | Voice Clone profile (style_profile, signature_phrases) stored on User, not Brand. Not available to SDR. |
| Story inheritance | NO | `story.origin_story` rendered, but StoryBrand narrative NOT rendered | `knowledge_builder.py` extracts `strategy` (which has no mission -- it migrated to story) but NOT `narrative` |
| Positioning inheritance | MINIMAL | Only `positioning.unique_value_proposition` rendered | Discriminator, brand_essence, enemies, insight, benefits, values, RTBs -- all ignored by SDR template |
| Proof inheritance | PARTIAL | Testimonials rendered with legacy field names (`t.quote`, `t.author`) | Authority vault not rendered. RTBs not rendered. Testimonial template uses legacy fields that may not match current schema (`content` vs `quote`, `author_name` vs `author`). |
| Avatar consistency | YES | Avatars passed to SDR template with ICP description and anti-avatar | Avatar data is shallow but correctly bridged. |

## Next Steps (Prioritized)

1. **[C-01] Wire existing brand data to SDR template** -- Highest ROI fix. The data already exists in the schema; it just needs to flow through `knowledge_builder.py` and `agent_identity.j2`. This is a ~2-hour task that immediately jumps SDR readiness from 1.5/9 to ~5/9.
2. **[C-01 sub-task] Fix testimonial legacy field mismatch** -- The SDR template uses `t.quote` and `t.author` but the current schema uses `content` and `author_name`. This means testimonials may render as empty even though data exists.
3. **[H-04] Add purchase_trigger_moments field** -- Enables the Onliness Statement synthesis and gives the SDR temporal context for urgency.
4. **[H-03] Bridge Voice Clone output to Brand** -- Connect the rich style analysis to BrandSettings so the SDR speaks in the brand's actual voice, not a vague tone descriptor.
5. **[C-02] Restructure Avatar model** -- Add structured psychographic/behavioral fields so the SDR can segment and adapt.
6. **[H-01] Add community/social dimension** -- Critical for creator brands, enables "join the tribe" selling angles.
7. **[H-02] Add brand_feelings taxonomy** -- Enables emotionally calibrated SDR responses.
8. **[M-02] Add self-expressive benefits** -- Enables identity-based selling ("being our customer means you are...").
