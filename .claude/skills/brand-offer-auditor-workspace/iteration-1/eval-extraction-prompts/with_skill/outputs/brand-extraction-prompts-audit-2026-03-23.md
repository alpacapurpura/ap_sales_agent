# Brand Studio Extraction Prompts Audit Report
> **Scope:** Brand Studio — Extraction Prompts (brand_extract_*.j2)
> **Date:** 2026-03-23
> **Focus:** Prompt-level analysis — Do the extraction prompts capture information at the correct atomic level, or do they produce generic data?
> **Frameworks Applied:** Aaker (PRIMARY), Keller (PRIMARY), Gad 4D (PRIMARY), Neumeier (PRIMARY), Brand Love Key (PRIMARY), StoryBrand (PRIMARY), Hormozi/WbD/Casel (SECONDARY — brand-to-offer bridge check)

## Executive Summary

The extraction prompts are **structurally well-designed** and demonstrate strong alignment with Brand Love Key and StoryBrand frameworks. The positioning and narrative prompts in particular ask for the right atomic elements and include formatting guidance that discourages generic output (e.g., "Formular como: '[Audiencia] quiere [deseo] pero [barrera real]'"). However, there are **four significant gaps** where prompts either miss critical framework concepts entirely, or where their instructions are too loose to prevent the LLM from producing vague, unusable data. The single most important finding is that **the identity extraction prompt captures voice_tone as a flat string of 2-3 adjectives**, which is far too shallow for Aaker's "Brand as Person" dimension and fails to give the SDR enough to replicate the brand's personality in conversations.

---

## Findings

### CRITICAL -- System Cannot Function Without This

- [ ] **[C-01] Identity prompt produces a flat voice_tone string instead of a structured personality profile** (Frameworks: Aaker "Brand as Person", Keller "Imagery/personality", Gad "Social dimension")
  - **Gap**: `brand_extract_identity.j2` field #11 asks for "2-3 adjetivos separados por coma" for `voice_tone`. This collapses the entire "Brand as Person" dimension (Aaker) into a trivial string like "conversacional, aspiracional, empatico". The prompt has no guidance on distinguishing *how the brand speaks* (tone) from *who the brand is* (personality), nor does it capture the brand-customer relationship type (mentor, friend, authority figure, co-conspirator).
  - **Impact**: The SDR agent receives "conversacional, aspiracional" and has no idea HOW to actually embody that voice. It cannot distinguish between a "conversacional" brand that uses slang and emojis vs. one that is warm but professional. Asset generation produces generic copy because the voice profile is too thin. Every downstream consumer of this field (SDR prompts, email generation, landing page copy) is working with an essentially empty personality definition.
  - **Recommendation**: Restructure voice_tone extraction into a multi-faceted personality object. The prompt should ask for:
    - `voice_adjectives`: 3-5 descriptors (current behavior, keep)
    - `voice_examples`: 2-3 actual phrases/sentences from the site that exemplify the tone (evidence-based, not inferred)
    - `communication_style`: How the brand addresses its audience (tuteo vs. usted, first person vs. third, imperative vs. invitational)
    - `personality_archetype_rationale`: Why the chosen archetype fits (forces specificity)
    - `brand_relationship_type`: What role the brand plays for the customer (mentor, friend, coach, authority) -- maps directly to Aaker's brand-customer relationship
  - **Affected files**: `backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_identity.j2` (prompt), `backend/src/modules/brand/domain/identity.py` (schema — `voice_tone` field)

- [ ] **[C-02] No extraction prompt captures the Social dimension — what the brand says about its users** (Framework: Gad 4D "Social", Keller "Resonance/community")
  - **Gap**: None of the 10 extraction prompts asks: "What does it signal about someone to be a customer of this brand?" or "What community/tribe does this brand represent?" The Gad Social dimension ("What does the brand say about me to others?") and Keller's Resonance level (community, active engagement) are completely absent from extraction. This is especially critical for creator/infoproductor brands where the audience's identity IS tied to the creator.
  - **Impact**: The SDR cannot use social proof as identity signaling ("Join 500+ creators who..."). The brand cannot be positioned as a tribe/movement. Asset generation cannot create TOFU content that appeals to belonging/identity needs, which is the #1 driver for high-ticket creator programs.
  - **Recommendation**: Add extraction instructions to `brand_extract_positioning.j2` under a new section or enrich the `insight` section:
    - `social_identity_signal`: "What does it say about someone that they are a customer of this brand?" (e.g., "They're serious about scaling, not hobbyists")
    - `community_markers`: Evidence of community (Facebook groups, Discord, alumni networks, hashtags, member counts)
    - `tribe_language`: Specific words/phrases the brand uses to define its in-group (e.g., "Visionarias", "Alpacas", "Our crew")
  - **Affected files**: `brand_extract_positioning.j2` or new prompt, `backend/src/modules/brand/domain/positioning.py` (schema gap)

- [ ] **[C-03] No prompt captures self-expressive benefits — only functional and emotional** (Framework: Aaker "Value Proposition", Keller "Feelings/self-respect")
  - **Gap**: `brand_extract_positioning.j2` field #3 asks for `functional_benefits` and `emotional_benefits`, which maps well to Brand Love Key. But Aaker's Value Proposition has THREE components: functional, emotional, AND self-expressive benefits. Self-expressive benefits answer "What does this brand let me say about myself?" (e.g., "I'm the kind of person who invests in AI-powered systems" vs. "I feel calm"). This is distinct from emotional benefits (how I feel) and from the Social dimension (how others see me). The prompt gives no guidance to the LLM to distinguish these.
  - **Impact**: Emotional benefits extracted by the LLM will be a mix of actual feelings ("paz mental") and disguised self-expression ("me siento profesional" — which is really about identity, not emotion). The SDR uses emotional benefits in closing arguments but misapplies self-expression as emotion, weakening the argument.
  - **Recommendation**: Either add `self_expressive_benefits` as a third list in the positioning prompt with clear guidance ("Benefits that let the customer express who they ARE or who they want to BECOME — identity statements, not feelings"), or add a clarifying instruction in the emotional_benefits section: "Emotional benefits are FEELINGS (paz mental, alivio, confianza). Identity benefits like 'me siento profesional' are self-expressive — list those separately."
  - **Affected files**: `brand_extract_positioning.j2`, `backend/src/modules/brand/domain/positioning.py` (BrandBenefits model)

### HIGH -- Significant Quality Degradation

- [ ] **[H-01] Positioning prompt allows generic consumer insight tension** (Framework: Brand Love Key "Consumer Insight")
  - **Gap**: The prompt says `tension` should be "La verdad incomoda que el consumidor siente pero no articula" and gives a format: "[Audiencia] quiere [deseo] pero [barrera real]." This is good structure, but the prompt lacks examples of BAD vs GOOD tensions to calibrate the LLM. Without negative examples, the LLM will produce surface-level tensions like "Los emprendedores quieren vender mas pero no tienen tiempo" instead of deep psychological conflicts like "Los creadores de contenido quieren monetizar su expertise pero sienten que cobrar caro los hace menos autenticos."
  - **Impact**: A shallow tension produces shallow positioning downstream. The SDR's empathy statements won't resonate because they address symptoms, not the real psychological barrier. The entire Brand Love Key framework rests on the insight quality.
  - **Recommendation**: Add 2 negative examples and 2 positive examples to the prompt:
    - BAD: "Quieren crecer pero no tienen recursos" (too generic, applies to everyone)
    - BAD: "Quieren vender online pero no saben marketing" (symptom, not tension)
    - GOOD: "Los coaches quieren escalar mas alla de 1-a-1 pero sienten que al masificar pierden la conexion personal que los hace buenos" (specific audience + real psychological conflict)
    - GOOD: "Los infoproductores saben que deben usar IA pero temen que su audiencia los perciba como menos autenticos" (timely + identity-level tension)
  - **Affected files**: `brand_extract_positioning.j2`

- [ ] **[H-02] Narrative prompt's success_transformation and failure_consequence lack specificity guidance** (Framework: StoryBrand "Success/Failure")
  - **Gap**: `brand_extract_narrative.j2` field #6 says `success_transformation` should be "Como se ve el EXITO — la vida del heroe despues de usar la solucion. Ser especifico y emocional." and `failure_consequence` should be "honesto pero no manipulador." These instructions are directionally correct but don't enforce the level of vivid specificity that StoryBrand demands. The LLM will produce "Tendra un negocio exitoso y podra disfrutar de su tiempo libre" — which is generic and won't move anyone.
  - **Impact**: The SDR's closing arguments use success/failure scenarios. Generic ones sound like every other sales pitch. The one-liner (field #7) synthesizes the entire narrative, but if the success transformation is generic, the one-liner will be too.
  - **Recommendation**: Add specificity constraints:
    - For success: "Describe a SPECIFIC SCENE, not an abstract state. Bad: 'tendra exito en su negocio'. Good: 'Abre su laptop el lunes por la manana y ve 3 ventas cerradas mientras dormia — su agente de IA lo hizo todo.'"
    - For failure: "Name the SPECIFIC emotional state and its consequences. Bad: 'seguira frustrado'. Good: 'Seguira siendo la persona que responde DMs a las 11pm, pierde clientes por no contestar a tiempo, y siente que trabaja mas que nadie pero gana menos de lo que merece.'"
  - **Affected files**: `brand_extract_narrative.j2`

- [ ] **[H-03] Identity prompt's archetype field is inferred without depth — no rationale or behavioral implications** (Framework: Aaker "Brand as Person", Gad "4D Branding Code")
  - **Gap**: `brand_extract_identity.j2` field #9 says "SIEMPRE inferir el arquetipo Jungiano dominante" and lists the 12 options. But it only asks for the name. It doesn't ask WHY this archetype fits, what behaviors it implies for communication, or whether there's a secondary archetype. The archetype is supposed to drive tone, visual style, and messaging strategy, but a bare label ("Hero") is useless without context.
  - **Impact**: The archetype field in `BrandIdentity` and the duplicate in `BrandValues` (positioning) may produce conflicting results because neither prompt requires justification. The archetype becomes a decorative label instead of an operational tool.
  - **Recommendation**: The archetype is already captured in BOTH `brand_extract_identity.j2` and `brand_extract_positioning.j2` (field #4 in values). This is a deduplication opportunity (see Deduplication section). Whichever prompt owns it should ask for: (1) primary archetype, (2) secondary archetype if detectable, (3) 1-sentence rationale based on observed evidence, (4) communication implication ("As a Rebel brand, the tone should challenge conventions and use provocative questions").
  - **Affected files**: `brand_extract_identity.j2`, `brand_extract_positioning.j2`, `backend/src/modules/brand/domain/identity.py`, `backend/src/modules/brand/domain/positioning.py`

- [ ] **[H-04] Strategy prompt is too narrow — captures only proprietary methodology, misses the Mental dimension entirely** (Framework: Gad 4D "Mental", Keller "Performance")
  - **Gap**: `brand_extract_strategy.j2` ONLY extracts a proprietary methodology (name + pillars). Many brands don't have a named methodology but DO have a unique approach, philosophy, or transformational framework. The prompt correctly notes "Si no hay metodologia, devolver null" — but this means the entire Strategy section returns empty for brands that describe their approach without naming it as a "method." More importantly, Gad's Mental dimension ("How does the brand make me think differently?") has no home in ANY extraction prompt.
  - **Impact**: For brands without a named "Method X", the strategy section is always null — wasting a section. The Mental dimension (what new perspective/knowledge the brand gives customers) is a powerful SDR tool ("We don't just give you a tool, we change how you think about sales") that is never captured.
  - **Recommendation**: Expand the strategy prompt to also extract:
    - `core_philosophy`: The brand's unique belief about how things SHOULD work (even without a named method)
    - `transformation_paradigm`: What mental model shift the brand creates in its customers (Gad Mental dimension)
    - Lower the bar: Instead of requiring a "named methodology", ask "Does the brand describe a specific approach, process, or way of doing things — even if not formally named?"
  - **Affected files**: `brand_extract_strategy.j2`, `backend/src/modules/brand/domain/strategy.py`

- [ ] **[H-05] Communication assets prompt is generative, not extractive — but lacks brand voice constraints** (Frameworks: Aaker "Brand as Person", StoryBrand)
  - **Gap**: `brand_extract_communication_assets.j2` is correctly designed as a generative prompt (it creates content ideas, not extracts). However, while it receives `positioning_context` and `narrative_context` as inputs, it has no explicit instruction to match the brand's voice_tone, archetype, or communication style. The instruction "Los copies deben sonar NATURALES, como si la marca hablara" is too vague — the LLM has no concrete voice profile to work with (especially given C-01 above).
  - **Impact**: Generated assets will have a generic "marketing agency" voice instead of sounding like the actual brand. For a "Rebel" brand, the copy should be provocative; for a "Caregiver" brand, it should be nurturing. Without explicit voice constraints, all brands get the same generic output.
  - **Recommendation**: Add an explicit instruction: "Before generating any copy, analyze the brand's voice_tone, archetype, and personality_traits from the positioning context. Every copy_draft MUST reflect these traits. If the brand is 'Directa e Irreverente', the copies should challenge, provoke, and use informal language. If the brand is 'Empatica y Profesional', the copies should be warm but polished." Also consider receiving identity_context (which contains voice_tone) as an additional input.
  - **Affected files**: `brand_extract_communication_assets.j2`

### MEDIUM -- Improvement Opportunity

- [ ] **[M-01] Positioning prompt's discriminator field allows 2-3 sentence freeform — no Onliness Statement structure** (Framework: Neumeier "Onliness Statement")
  - **Gap**: `brand_extract_positioning.j2` field #6 asks for "El diferenciador unico en 2-3 frases. Que hace a esta marca IRREMPLAZABLE." This is good intent but lacks structure. Neumeier's Onliness Statement template ("The only [X] that [Y] for [Z] who [N] during [M] because [R]") forces a level of specificity that freeform text does not. The current prompt will produce "Es la unica plataforma que automatiza ventas con IA" — which sounds differentiated but is actually vague (no audience, no moment, no proof).
  - **Impact**: The discriminator is the heart of competitive positioning. A vague one means the SDR can't explain WHY this brand vs. competitors. The UVP (field #8) partially overlaps with the discriminator, creating potential confusion.
  - **Recommendation**: Add Neumeier's template as a formatting guide for the discriminator: "Formular como: 'La unica [tipo de oferta] que [beneficio unico] para [audiencia especifica] que [necesidad especifica] en el momento que [situacion/trigger] porque [razon para creer].' No todos los slots necesitan llenarse, pero cada uno que se llene agrega especificidad." Keep the UVP as a separate field (it serves a different purpose — the "Solo nosotros..." format is more about competitive moat than positioning statement).
  - **Affected files**: `brand_extract_positioning.j2`

- [ ] **[M-02] Authority prompt captures proof but doesn't classify by Keller's credibility dimensions** (Framework: Keller "Judgments")
  - **Gap**: `brand_extract_authority.j2` classifies authority items by source type (Prensa, Certificacion, Partner, Premio, Cliente) which is practical. But Keller's Judgments pillar has four dimensions: perceived quality, credibility (expertise + trustworthiness + likability), consideration, and superiority. The prompt captures credibility well but misses the other three. There's no extraction of "Why should I choose THIS brand over alternatives?" (superiority) or "Is this brand worth considering at all?" (consideration trigger).
  - **Impact**: The authority vault becomes a collection of logos and badges, which is good for landing pages but insufficient for SDR arguments. The SDR needs superiority claims ("We're the only platform that does X while competitors only do Y") and consideration triggers ("If you're spending more than 10 hours/week on manual sales, you should evaluate this").
  - **Recommendation**: Add to the authority prompt OR to the positioning prompt: (1) `superiority_claim`: What makes this brand clearly better than the next best alternative? (2) `consideration_trigger`: What situation or threshold should make someone evaluate this brand? These map to Keller's Judgments dimensions and directly feed SDR qualification logic.
  - **Affected files**: `brand_extract_authority.j2` or `brand_extract_positioning.j2`

- [ ] **[M-03] Story prompt's origin_story has good structure but no guidance on emotional arc calibration** (Framework: StoryBrand "Guide empathy")
  - **Gap**: `brand_extract_story.j2` field #1 asks for a narrative with "Incidente detonante → Punto de dolor → Punto de giro → Resolucion" — excellent dramatic arc structure. However, the prompt doesn't guide the LLM on emotional calibration. The origin story serves a specific purpose in the StoryBrand framework: it establishes the Guide's empathy ("I've been where you are") and authority ("and here's how I got out"). Without this framing, the LLM may produce a corporate history ("Founded in 2020 by Maria, the company grew to serve 500 clients") instead of an emotionally resonant founder journey.
  - **Impact**: The origin story is used in "About" sections, email sequences, and SDR warmup messages. A flat corporate history doesn't build emotional connection. A story that mirrors the customer's struggle does.
  - **Recommendation**: Add framing to the origin_story instructions: "The origin story should mirror the CUSTOMER'S journey — the founder experienced a version of the same problem the customer faces. The story should make the reader think 'they understand me.' Frame: What problem did the founder face? How did they feel? What did they discover? How did that become this brand? The emotional peak should be the REALIZATION moment, not the business milestone."
  - **Affected files**: `brand_extract_story.j2`

- [ ] **[M-04] Visuals prompt is excellent but the brand_mood field should feed back into voice extraction** (Framework: Aaker "Brand as Symbol", Gad "Functional")
  - **Gap**: `brand_extract_visuals.j2` is the most thoroughly designed prompt in the set — the color, typography, and design system extraction protocols are comprehensive and specific. The `brand_mood` field (adjectives + energy level) captures visual personality well. However, this visual personality data exists in isolation from the verbal personality (voice_tone in identity). A brand whose visual mood is "audaz, vibrante, energetico" with "high" energy but whose voice_tone is "empatico, profesional" has an inconsistency that no prompt catches.
  - **Impact**: Asset generation may produce visually bold designs with timid copy, or vice versa. The system has no mechanism to flag brand inconsistency between visual and verbal identity.
  - **Recommendation**: This is more of a system-level recommendation than a prompt fix: consider a post-extraction validation step that compares `brand_mood` adjectives with `voice_tone` adjectives and flags misalignment. Alternatively, add a brief instruction to the visuals prompt: "If the visual personality contradicts the stated voice_tone, note the discrepancy in visual_references."
  - **Affected files**: `brand_extract_visuals.j2` (minor), system-level concern

- [ ] **[M-05] People/Contact prompt captures team but misses the "Brand as Organization" dimension** (Framework: Aaker "Brand as Organization")
  - **Gap**: `brand_extract_people_contact.j2` captures key_leadership (people), culture_vibe (1-2 sentences), locations, and contact info. The `culture_vibe` field is the closest thing to Aaker's "Brand as Organization" (organizational attributes like innovation, trustworthiness, local vs. global), but it's a single freeform string that typically produces something like "Startup remota con enfoque en innovacion." This doesn't capture whether the organization signals trust, innovation, social responsibility, or local expertise.
  - **Impact**: For B2B or high-ticket sales, organizational credibility matters. The SDR needs to communicate "This is a serious organization" or "This is a nimble, innovative team" — and the current field is too thin to distinguish these.
  - **Recommendation**: Expand `culture_vibe` or add structured sub-fields: `org_attributes` (list: innovative, trustworthy, community-driven, global, local-expert, etc.), `org_size_signal` (solo, small team, growing company, established), `org_credibility_markers` (years in business, team size, client count — inferred from site).
  - **Affected files**: `brand_extract_people_contact.j2`, domain model would need extension

---

## Deduplication Opportunities

| Concept | Current Fields | Prompts | Recommendation |
|---------|---------------|---------|----------------|
| **Archetype** | `identity.archetype` + `positioning.values.archetype` | `brand_extract_identity.j2` (#9) + `brand_extract_positioning.j2` (#4) | Unify into positioning only (where it lives alongside personality_traits and values). Remove from identity prompt or make identity prompt reference the positioning value. Currently risks producing conflicting archetypes from the same website. |
| **Description/Positioning Statement** | `identity.description` + `positioning.unique_value_proposition` + `positioning.discriminator` | `brand_extract_identity.j2` (#4) + `brand_extract_positioning.j2` (#6, #8) | These three fields address different aspects but overlap in practice. The identity `description` ("Es una [tipo] que [hace] para [quien] mediante [como]") is essentially a light UVP. Keep all three but add clarifying instructions: description = factual positioning statement, discriminator = competitive differentiation (Onliness), UVP = unique capability claim. |
| **Plan/Process Steps** | `narrative.plan[]` (StoryBrand) + `strategy.methodology_pillars[]` | `brand_extract_narrative.j2` (#4) + `brand_extract_strategy.j2` (#3) | These often capture the same "how we work" process under different labels. The narrative plan is customer-facing ("1. Agenda demo, 2. Configura tu cuenta, 3. Tu agente vende"), while methodology pillars are methodology-facing ("Pilar 1: Diagnostico, Pilar 2: Automatizacion"). Keep both but add a note to each prompt: "El plan de StoryBrand es la experiencia del CLIENTE. Los pilares de metodologia son el FRAMEWORK interno de la marca. No son lo mismo." |
| **Emotional resonance** | `positioning.benefits.emotional_benefits[]` + `narrative.outcome.success_transformation` | `brand_extract_positioning.j2` (#3) + `brand_extract_narrative.j2` (#6) | Emotional benefits are feelings (nouns: "paz mental", "confianza"), while success_transformation is a scenario (narrative). Different zoom levels of the same concept. Keep both — they serve different consumers (benefits for SDR quick-reference, transformation for storytelling). |

---

## Methodology Coverage Matrix

| Framework | Weight | Coverage | Key Gaps |
|-----------|--------|----------|----------|
| **Aaker (Brand Identity)** | PRIMARY | 4/7 atomic elements | Missing: "Brand as Person" depth (C-01), "Brand as Organization" depth (M-05), self-expressive benefits (C-03) |
| **Keller (Resonance)** | PRIMARY | 3/6 pyramid levels | Missing: Feelings (partially via emotional_benefits), Resonance/Community (C-02), Judgments beyond credibility (M-02) |
| **Gad (4D Branding)** | PRIMARY | 1/4 dimensions | Functional covered. Missing: Social (C-02), Mental (H-04), Spiritual (partially via mission/vision in story prompt) |
| **Neumeier (Onliness)** | PRIMARY | 3/7 slots | Offering type, unique benefit, target audience partially covered. Missing: category frame, specific need, moment/situation, reason to believe as structured template (M-01) |
| **Brand Love Key** | PRIMARY | 7/8 elements | Strong coverage. Missing: self-expressive benefits (C-03). Insight depth concern (H-01). |
| **StoryBrand** | PRIMARY | 7/7 elements | Structurally complete. Quality concern on success/failure specificity (H-02). |
| **Hormozi (Grand Slam)** | SECONDARY | N/A (brand-level) | Not applicable to brand extraction — but the brand's `dream_outcome` language should be capturable from the site's hero section. Currently not explicitly extracted. |
| **WbD (Impact/Critical Event)** | SECONDARY | N/A (brand-level) | No brand-level extraction needed. But the "moment/situation" trigger (Neumeier) that maps to WbD's Critical Event is not captured at brand level. |
| **Casel (Productization)** | SECONDARY | N/A (brand-level) | Not applicable to brand extraction. |

---

## SDR Readiness Score (Brand Data Only)

| SDR Question | Answerable? | Source Field(s) | Gap |
|-------------|-------------|-----------------|-----|
| "Who am I talking to?" | PARTIAL | narrative.hero.identity, positioning.insight | No structured avatar/ICP at brand level (avatars live in offers). Hero identity is a 1-2 sentence string, not a structured profile. |
| "What's their trigger to buy NOW?" | NO | -- | No brand-level critical event or urgency trigger captured. Neumeier's "moment/situation" is absent. |
| "What's at stake if they don't act?" | YES | narrative.outcome.failure_consequence | Quality depends on prompt specificity (H-02). |
| "What am I actually selling?" | PARTIAL | identity.description, positioning.discriminator | Description is factual. Missing vivid dream outcome language. |
| "Why should they believe this works?" | YES | authority_vault[], positioning.reasons_to_believe[], testimonials[] | Strong multi-source proof stack. |
| "What objections will they raise?" | NO | -- | No brand-level objection capture. Lives in offers. |
| "How do I create urgency?" | NO | -- | No urgency/scarcity mechanism at brand level. |
| "How does this brand talk?" | PARTIAL | identity.voice_tone, identity.archetype | Too shallow (C-01). 2-3 adjectives is not enough to replicate a brand voice. |

**Overall SDR Readiness from Brand Data: 3/8 questions fully answerable (YES), 3 PARTIAL, 2 NO**

Note: Some "NO" answers are expected at brand level (objections and urgency are offer-specific). The concerning items are the PARTIAL answers — particularly voice/personality (C-01) and avatar depth.

---

## Prompt-by-Prompt Atomic Verdict

| Prompt | Framework Alignment | Atomic Level? | Verdict |
|--------|-------------------|---------------|---------|
| `brand_extract_identity.j2` | Aaker (partial) | **TOO SHALLOW** on voice_tone and archetype; adequate on factual fields | Needs structured personality extraction |
| `brand_extract_positioning.j2` | Brand Love Key (strong) | **GOOD** — asks for the right atoms with formatting guidance. Consumer insight could be deeper (H-01). Missing self-expressive benefits (C-03). | Best prompt in the set |
| `brand_extract_narrative.j2` | StoryBrand (strong) | **GOOD structure, MEDIOCRE calibration** — all 7 elements present but success/failure lack vivid specificity guidance (H-02) | Add negative/positive examples |
| `brand_extract_strategy.j2` | Gad Mental (missing) | **TOO NARROW** — only captures named methodologies, misses philosophy and mental transformation (H-04) | Expand scope beyond named methods |
| `brand_extract_story.j2` | StoryBrand Guide (partial) | **ADEQUATE** — good dramatic arc structure, could better frame as empathy-building tool (M-03) | Minor improvement |
| `brand_extract_authority.j2` | Keller Judgments (partial) | **ADEQUATE for extraction** — good source-type classification. Missing superiority/consideration dimensions (M-02) | Add 2 judgment fields |
| `brand_extract_communication_assets.j2` | StoryBrand + BLK (structural) | **GENERATIVE, NOT EXTRACTIVE** — well-designed for content ideation but lacks voice constraints (H-05) | Add explicit voice matching |
| `brand_extract_visuals.j2` | Aaker Symbol (strong) | **EXCELLENT** — the most thorough prompt. Deep color, typography, and design system extraction with clear calibration. | Best-in-class |
| `brand_extract_testimonials.j2` | Keller Judgments (partial) | **ADEQUATE** — captures social proof well, good guidance on what qualifies as a testimonial | Minor |
| `brand_extract_people_contact.j2` | Aaker Organization (shallow) | **ADEQUATE for contact data, SHALLOW for organizational identity** — culture_vibe is too thin (M-05) | Expand org attributes |

---

## Next Steps (Prioritized)

1. **[C-01] Restructure voice_tone extraction** into a multi-faceted personality profile — this is the single highest-impact change because every downstream consumer (SDR, assets, emails) depends on voice quality. Requires schema change in `BrandIdentity` and prompt update.

2. **[C-02] Add Social dimension extraction** (community, tribe identity, social signaling) — either in positioning prompt or as a new extraction target. This unlocks identity-based selling for creator brands.

3. **[H-01] Add negative/positive examples to consumer insight tension** — lowest-effort, highest-impact improvement. No schema change needed, just prompt text.

4. **[H-02] Add vivid specificity examples to success/failure outcomes** — same as above, prompt-only change.

5. **[C-03] Separate self-expressive benefits** from emotional benefits — requires schema change in `BrandBenefits` model.

6. **[H-04] Expand strategy prompt** beyond named methodologies to capture philosophy and mental transformation.

7. **[M-01] Add Onliness Statement template** to discriminator extraction — prompt-only change.

8. **[H-03] Deduplicate archetype** between identity and positioning prompts — pick one home, enrich it.

9. **[H-05] Add voice constraints** to communication assets prompt — prompt-only change.

10. **[M-02, M-03, M-04, M-05]** — Lower priority improvements that individually add value but aren't blocking.
