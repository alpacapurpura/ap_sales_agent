---
name: brand-expert
description: "Expert en arquitectura completa Brand Studio (post-refactor field-contract-platform): identity, visuals, story, strategy, positioning, narrative (StoryBrand), brand_personality (Jung), communication_assets, contact, team, testimonials, authority_vault. Incluye PersonalityProfile (3-pilar engine) + BuyerPersona (multi-persona). Habla lenguaje de negocio. Use cuando user pide modificar/agregar fields/secciones/buyer-personas/voice-tone/posicionamiento/narrativa/credenciales/equipo/testimonios. Triggers: 'cambiar voz', 'tono de marca', 'arquetipo', 'StoryBrand', 'narrativa', 'posicionamiento', 'UVP', 'unique value proposition', 'buyer persona', 'avatar', 'historia de marca', 'misión', 'visión', 'identidad visual', 'colores marca', 'logo', 'paleta', 'testimonios', 'autoridad', 'credenciales', 'equipo', 'instructor', 'methodology', 'metodología', 'pilares', 'agregar campo brand', 'modificar marca', 'fusionar buyer persona'."
---

# Brand Expert — Skill

## Modo conversación

User pide cambio brand → habla **español neutro LATAM**, tono experto branding/posicionamiento (microempresario LATAM), NO caveman. Caveman solo body SKILL.md (eficiencia tokens). Antes de codear:
- **Pregunta** producto-side (ej. "¿esto va al sales-agent prompt o solo a landing? ¿es público o solo del owner?").
- **Web search 2026 best practices** según concepto:
  - Voice/tone copy: "brand voice tone framework 2026 SMB"
  - Positioning (Brand Love Key): "brand positioning canvas 2026 LATAM small business"
  - StoryBrand: "donald miller storybrand 2026 update"
  - Buyer persona: "ideal customer profile 2026 microempresario"
  - Archetype copy: "jung archetype brand voice 2026"

## Mental model — Brand aggregates

```
BrandSettings (raíz, vive en Tenant.config_json["brand_settings"])
├── identity (BrandIdentity)         nombre, tagline, descripción, industria, contacto legal
├── visuals (BrandVisuals)           colores, tipografía, logo, fotografía
├── story (BrandStory)               origen, misión, visión, milestones[]
├── strategy (BrandStrategy)         methodology_name + pillars[]
├── positioning (BrandPositioning)   UVP, brand_essence, discriminator, insight, benefits, values, RTB[]
├── narrative (BrandNarrative)       StoryBrand: hero, problem, guide, plan[], cta, outcome, one_liner
├── contact (BrandContact)           support/sales email, phone, social, address
├── brand_personality (BrandPersonality)  archetype (Jung 12), core_values, traits
└── communication_assets             creative_concepts[], assets[]

Collections externas brand-scoped:
├── team[] (KeyFigure)               miembros del equipo + bio
├── testimonials[] (BrandTestimonial)  M:N placements via social_proof
├── authority_vault[] (BrandAuthorityItem)  certificaciones, premios, hitos
└── buyer_personas[] (BuyerPersona)  multi-persona, optional offer-scoped

Aggregate separado (mismo BC):
PersonalityProfile (motor 3-pilar)
├── dimensions (6 axes 0..1: energy, warmth, humor, expressiveness, narrative, verbosity)
├── linguistic_patterns (emoji_style, greeting, farewell, fillers[], punctuation, humor_type, vocab[])
└── sample_exchanges[] (context + other_message + author_response)
                                        compila a 5-block system_instruction (PersonalityCompiler)
```

## Files canon SSoT

| Layer | File |
|---|---|
| L0 raíz | `backend/src/modules/brand/domain/aggregates.py` (BrandSettings) |
| L0 sub-models | `identity.py`, `visuals.py` (en identity.py), `story.py`, `strategy.py`, `positioning.py`, `narrative.py`, `team.py` (BrandContact + KeyFigure + BrandTestimonial + BrandAuthorityItem), `personality.py` (BrandPersonality + PersonalityCompiler), `communication_assets.py`, `buyer_persona.py` |
| L1 FieldContract | `brand/domain/field_contract.py` (BRAND_SECTION_MAP + BRAND_FIELD_OVERRIDES) |
| L1 Buyer | `brand/domain/buyer_persona_field_contract.py` (BUYER_PERSONA_SECTION_MAP + dict_subkeys) |
| Personality | `brand/domain/personality.py` (DimensionContract, PersonalityCompiler) |
| Repos | `brand/infrastructure/repositories/{brand,buyer_persona,personality,avatar}_repository.py` |
| Cross-module port | `shared/links/ports/brand.py` (`BrandDataPort`, `create_brand_data_port`) — **única forma** cross-module read |
| Schema FE | `frontend/src/features/brand-studio/schemas/*.schema.ts` (no se deriva auto, manual mirror) |

## BrandIdentity — 30+ fields

```
brand_name, tagline, description, industry, website, founding_year,
language, timezone, voice_tone (DEPRECATED — use brand_personality)
[Legal/regulatory/compliance — 18 fields]
legal_name, legal_entity_type, tax_id, tax_regime,
country_of_registration, commercial_registry_number,
fiscal_address, legal_representative,
legal_email, dpo_email,
terms_url, privacy_url, cookies_url, refund_policy_url, acceptable_use_url,
regulated_profession_body, professional_license_number,
professional_license_holder, operating_authorization,
liability_insurance_carrier,
sales_agent_disclaimer, sales_agent_out_of_scope, escalation_contact
```

## BrandPositioning (Brand Love Key)

```
unique_value_proposition (UVP)         — "qué te hace único"
discriminator                          — "en qué categoría compites"
brand_essence                          — esencia 3-5 palabras
competitive_environment (sub-objeto)   — direct_competitors[]
insight (sub-objeto)                   — tension + cultural_truth + audience_belief
benefits (sub-objeto)                  — functional + emotional + social
values (sub-objeto)                    — core + aspirational + behavioral
reasons_to_believe[] (RTB collection)  — proof points
```

## BrandNarrative (StoryBrand framework — Donald Miller)

```
one_liner                              — synthesis 1 frase
hero (sub-objeto)                      — quién es el cliente
problem (sub-objeto)                   — external + internal + philosophical
guide (sub-objeto)                     — empathy + authority
plan[] (collection)                    — 3-5 pasos clear
cta (sub-objeto)                       — direct + transitional
outcome (sub-objeto)                   — success + failure
```

## BrandPersonality (Jung 12)

```
archetype                              — sage/hero/creator/lover/jester/everyman/
                                          caregiver/innocent/explorer/outlaw/magician/ruler
core_values[]                          — 3-5 valores
personality_traits[]                   — 3-5 adjetivos
```

## PersonalityProfile (3-pilar engine — feedback memo)

**Crítico**: dimensions (20%) NO alcanzan. MUST include:
- `dimensions` (40% peso real) — 6 axes en `personality.py:DimensionContract`
- `linguistic_patterns` (40%) — surface fingerprint
- `sample_exchanges` (40%) — few-shot anchors
- `_NEGATIVE_THRESHOLD = 0.3` → emite "NUNCA HACES" constraints

`PersonalityCompiler.compile()` → 5-block `system_instruction`:
```
1. REGLAS DE PERSONALIDAD       — 1 instruction por dimension
2. HUELLA LINGÜÍSTICA            — surface patterns
3. NUNCA HACES                   — negative constraints (dim < 0.3)
4. EJEMPLOS DE CONVERSACIÓN      — few-shot
5. ANCLA DE IDENTIDAD            — immutable identity
```

## BuyerPersona — multi-persona

Vive en `brand/domain/buyer_persona.py` (módulo brand, registra como `"buyer_persona"` en FieldContract registry).

```
identity:        name, tagline, scope (GLOBAL | offer_scoped), offer_id, is_primary
demographics:    age_range, location, occupation, income_range, education, family_status (JSONB sub-keys)
psychographics:  values, beliefs, lifestyle, personality_traits, media_consumption, aspirations (JSONB sub-keys)
pain_points[]:   list[dict] — items con emotional_impact (form-runtime CRUD)
desires[]:       list[dict] — items con urgency
objections[]:    list[dict]
preferred_channels[]: list[dict] — channel + frequency + tone
buyer_journey:   awareness, consideration, decision (JSONB sub-keys)
purchase_triggers: list[str]  (sin UX hoy)
anti_patterns:    list[str]   (sin UX hoy)
```

Walker handles JSONB sub-keys via `dict_subkeys` arg (Fase 07).

## SOPs por operación de negocio

### "Quiero modificar voice / tone / personality"

User dice "quiero que el copilot suene más cálido / más serio / con más humor / menos emoji":
1. **Pregunta**: ¿afecta sales-agent (chat) o copilot (asistente onboarding) o landing copy?
2. Si tone para chat → `PersonalityProfile`:
   - Edit `dimensions` (warmth↑, humor↑, energy↓, etc.).
   - Edit `linguistic_patterns` (emoji_style, fillers[], greeting/farewell).
   - Add `sample_exchanges[]` con tone target (mínimo 3 con contexts distintos: `greeting`, `objection`, `closing`).
   - Si dim < 0.3 → constraint negativo auto generado por compiler.
3. Si tone para landing/copy estática → `BrandPersonality.archetype` + `core_values`. Cambia voice subyacente.
4. **`identity.voice_tone` está DEPRECATED** (`brand/domain/field_contract.py:255`). NUNCA tocar.
5. PersonalityCompiler regenera `system_instruction` runtime — sin cache invalidation manual.
6. **Web search**: "brand voice 2026 [arquetipo]" si user duda en arquetipo.
7. Test: ejecutar conversación con sales-agent post cambio (qualitative).

### "Quiero modificar arquetipo Jung"

12 arquetipos clásicos. Pregunta:
- ¿Tu marca **enseña** (sage)? **transforma** (magician/hero)? **acompaña** (caregiver)? **rompe reglas** (outlaw)? **crea** (creator)? **divierte** (jester)? **conecta** (lover)? **explora** (explorer)? **gobierna** (ruler)? **simplifica** (innocent/everyman)?

Edit `brand_personality.archetype`. Cambio cascada:
- PersonalityProfile dimensions deberían alinear (sage → low energy, high narrative; jester → high humor; caregiver → high warmth).
- Sales-agent prompt regenera (knowledge_builder.build_identity).
- Landing copy debería refrescar — pero copy estática no se regenera auto. Indica al user que hay que re-extraer / re-generar landings.

### "Quiero cambiar UVP / posicionamiento / Brand Love Key"

Decisión PRODUCTO. UVP es **anchor cross-feature** (sales-agent prompt + landing hero + copilot context). Cambio cascada:
1. Edit `positioning.unique_value_proposition` + opcional `brand_essence`/`discriminator`.
2. Considerá refresh `narrative.one_liner` si se contradice.
3. **Pregunta** al user: "¿es ajuste de copy o re-posicionamiento real? Si re-positioning, ¿re-extraemos buyer-personas?"
4. Sales-agent reactive (lee runtime).
5. Landing pages: NO regenera auto. Indica al user.

### "Quiero modificar StoryBrand narrative"

7 elementos del framework Donald Miller. Asegurate cubrir:
- **hero** = el cliente (NO la marca). Frecuente error: marcas se ponen como hero.
- **problem** = external + internal + philosophical (3 niveles).
- **guide** = la marca = empathy + authority.
- **plan** = 3-5 pasos claros.
- **cta** = direct (compra ya) + transitional (free download).
- **outcome** = success + failure (consequences).
- **one_liner** = síntesis 1 frase.

Edit en `BrandNarrative`. Si user describe en lenguaje propio, traducí al framework con preguntas. Web search "storybrand framework 2026" si dudás definición elemento.

### "Quiero crear/modificar buyer persona"

Multi-persona. Cada persona puede ser:
- `scope=GLOBAL` (default tenant-wide).
- `scope=offer_scoped` con `offer_id=<UUID>` (specific to one offer).
- `is_primary=True` (primary avatar).

CRUD via `BuyerPersonaRepository`. Fields validados via `buyer_persona_field_contract.py`. JSONB sub-keys (demographics.age_range etc) registradas en `dict_subkeys`.

Add new persona:
1. POST `/api/v1/brand/buyer-personas` con `name` + `scope` + (opcional) `offer_id`.
2. Fill demographics/psychographics/pain_points/desires.
3. Si `is_primary=True`, otros se demoten.

**Fusionar 2 personas**: decisión PRODUCTO.
- Identificar source-of-truth.
- Migrar offer references (`offer_id` apuntando al persona eliminado).
- Soft-delete persona fusionada.
- Update sales-agent prompt context.
- NO existe API "merge personas" — script ad-hoc.

### "Quiero crear nuevo buyer persona scope" (ej. cohort-scoped)

Ya hay `scope: str` field con values "GLOBAL" + "offer_scoped". Para nuevo scope (ej. "channel_scoped"):
1. Add scope value en validation (Pydantic + repo).
2. Add `<scope_id>` field si necesita FK (ej. `channel_id` para channel_scoped).
3. Update FE filter.
4. Update sales-agent context resolver (qual persona aplica per conversación).

### "Quiero agregar/modificar field a brand"

Workflow refactor field-contract-platform (post-Fase-09):
1. Decidir sub-model (identity / story / positioning / narrative / etc.).
2. Add field a Pydantic model.
3. **Add path → section** en `BRAND_SECTION_MAP` (`brand/domain/field_contract.py`).
4. **Add Override** en `BRAND_FIELD_OVERRIDES`:
   ```python
   "narrative.tag_anchor": Override(
       priority=80,
       is_required_semantic=True,
       human_question_es="¿Cuál es la frase ancla que recordás siempre?",
       expects="frase corta (5-12 palabras)",
       gate="narrative.one_liner",   # opcional
       label_es="Frase ancla",
   ),
   ```
5. Walker `dict_subkeys` arg si el field es JSONB sub-key (buyer_persona pattern).
6. Migration NO requerida (BrandSettings vive en `Tenant.config_json` JSONB).
7. Run `tests/architecture/test_brand_editable_fields_baseline.py` + `test_field_contract_platform.py`. Pydantic ⊆ FieldContract enforced.
8. **FE schema** `frontend/src/features/brand-studio/schemas/<section>.schema.ts` — alineá manual.
9. **Copilot: zero-touch.** `propose_field_updates`, `next_question`, `extract_structured` ya consumen FieldContract.
10. Si descripción visible al copilot system prompt → check baseline `description_preserved` test (puede fallar — actualizar intencionalmente).

### "Quiero crear nueva sección en Brand Studio"

Brand sections (catalog): `identity`, `story`, `positioning`, `narrative`, `avatars`, `visuals`, `personality`, `team`, `testimonials`, `authority`, `communication_assets`. Si **realmente** nueva (no fits ninguna):
1. Add slug a `BRAND_SECTION_MAP` paths.
2. **No** hay catalog `brand_section_catalog.py` separado (a diferencia de offer). Las sections se infer del map.
3. FE schema file new + register en FSD.
4. URL routing: `/brand-studio/<section-slug>`.

### "Quiero modificar testimonios / autoridad / equipo"

Collections con M:N placement vía `social_proof` BC:
- `testimonials[]` (BrandTestimonial) — clientes que validaron.
- `authority_vault[]` (BrandAuthorityItem) — certificaciones, premios, prensa.
- `team[]` (KeyFigure) — miembros activos del equipo.

CRUD via repos individuales en `brand/infrastructure/repositories/`. Placements (qual offer/landing usa cuál) viven en `social_proof` (M:N table). NO duplicar testimonio per offer — placement decide visibilidad.

**Fusionar testimonios duplicados**: API CRUD + script si volume.

### "Quiero modificar metodología (strategy.methodology)"

`BrandStrategy`:
- `methodology_name` — nombre propio (ej. "Sistema CALMA", "Método 3D").
- `methodology_description` — qué es.
- `methodology_pillars[]` — 3-7 pilares con name + description.

Cambios cascada:
- Sales-agent prompt: si menciona la metodología.
- Landing copy: si menciona.
- Reactive vía repo read runtime.

### "Quiero modificar identity legal / compliance"

18 fields legal/regulatory en `BrandIdentity`. Ej. `legal_name`, `tax_id`, `dpo_email`, `terms_url`, `regulated_profession_body`. Si tenant es regulado (salud, legal, financiero) → fields **obligatorios**. Considerá agregar gate condicional (`gate="identity.regulated_profession_body"`) para fields que solo aplican.

### "Quiero modificar visuals (colores, logo, fotografía)"

`BrandVisuals`:
- `primary_color`, `text_secondary_color` (hex).
- `photography_style` (string descriptive).
- `logo_url`, `favicon_url`.
- **Derived (auto-generados, can_propose=False)**: `semantic_colors`, `font_weights`, `typography_scale`, `border_radius_values`, `brand_mood`, `logos`. NO editar directamente — viene de design system tokens.

Colores cambia → re-genera tokens design system (proceso aparte). Logo cambia → invalidate landing assets cache.

### "Quiero modificar communication_assets"

`CommunicationAssets`:
- `creative_concepts[]` (lista). Cada uno: name + description + reference_url. **can_propose=False** — form-runtime CRUD, item-by-item.
- `assets[]` (lista). Material producido (mockups, videos, copies). 8 fields → split form. **can_propose=False**.

Cambios via FE form-runtime CRUD. Copilot NO propone wholesale replace.

### "Quiero modificar descripciones (label_es / description_es / human_question_es / help_text_es)"

User dice "no se entiende" / "muy genérico" / "querés que pregunte mejor":
1. **Pregunta tenant target**: ¿qué `ExpertBusinessType`? Lenguaje varía (PROFESIONAL_SALUD técnico vs NEGOCIO_LOCAL coloquial).
2. **Web search 2026 best practices** según concepto:
   - Brand identity copy: "brand identity questionnaire 2026 SMB"
   - StoryBrand: "storybrand brandscript template 2026"
   - Buyer persona: "buyer persona template 2026 microempresario LATAM"
   - Personality: "brand voice spectrum 2026"
3. Spanish neutro LATAM (`.claude/rules/spanish-text.md`) — sin voseo.
4. Para `human_question_es`: pregunta natural conversational. Ej. "¿En qué industria opera tu marca?" (no "Industria: …").
5. Edit Override del field.
6. **Baseline tests** (`test_brand_editable_fields_baseline.py`, `test_buyer_persona_editable_fields_baseline.py`): si descripción cambia → update baseline (intencional, doc en commit).

## Cosas que DEBE inform al copilot

| Cambio | Copilot acción | Porqué |
|---|---|---|
| Nuevo field en Pydantic + Override | **zero-touch** | Catalog derivado del FieldContract — auto |
| Cambio `human_question_es` / `gate` / `priority` | **zero-touch** | `next_question` lee runtime |
| Cambio `can_propose=False` | **zero-touch** | `propose_field_updates` filtra |
| Nuevo section path slug | **zero-touch** | `validate_field_path` deriva del registry |
| **PersonalityProfile dimensions / patterns / exchanges** | **zero-touch** | Compiler genera prompt runtime |
| **Buyer persona nuevo** | **zero-touch** | Sales-agent context resolver lee runtime |
| **Cambio archetype Jung** | **zero-touch + flag** que sales-agent prompt vuelve a renderizar | Reactive |
| **Cambio UVP** | **zero-touch sales-agent** + indicar "regenera landing" al user | Landing copy estática no auto-refresca |
| **Drop field DEPRECATED** | **zero-touch** | Status filter en projection |
| **Cambio que rompe baseline tests** | Update baseline + commit msg explica | Intencional |

**Resumen**: arquitectura post-Fase-09 = mostly reactive. Copilot lee FieldContract registry + repos en runtime. Solo cambios que afectan **assets generados estáticamente** (landings) requieren acción extra: indicar al user "regenera tu landing".

## Limitantes arquitectónicas (no romper)

- ❌ Nunca importar `brand.domain` directo cross-module — usá `shared/links/ports/brand.py::BrandDataPort`. DDD arch test falla.
- ❌ Nunca tocar `identity.voice_tone` — DEPRECATED desde 2026-04-24 (Fase 06). Use `brand_personality` / `PersonalityProfile`.
- ❌ Nunca duplicar metadata FE — consumá hook + catalog.
- ❌ Nunca add new sub-model sin entry en `BRAND_SECTION_MAP`. Arch test cross-cutting `Pydantic ⊆ FieldContract` falla.
- ❌ Nunca crear fields nested-of-nested proposable (e.g. `positioning.insight.tension`). Walker emite OBJECT con `can_propose=False` para sub-objects. Si necesitás propose deep, extender walker depth + FE validate_field_path.
- ❌ Nunca modificar `derived` visuals (semantic_colors, typography_scale, etc.) directamente. Viene de design system tokens.
- ❌ Nunca PersonalityProfile sin las 3 capas (dimensions + patterns + exchanges). Solo dimensions = sales-agent suena robótico (feedback memo `feedback_personality_3_pillars`).
- ❌ Nunca edit `BrandStrategy.unique_value_proposition` o `competitors` (DEPRECATED — model_validator migra a positioning). Edit positioning directo.
- ❌ Nunca duplicar testimonios per offer. Use M:N placement via `social_proof` BC.
- ❌ Nunca buyer_persona como aggregate separado en módulo BE distinto. Vive bajo `brand/domain/`, registra como `"buyer_persona"` en FieldContract.

## Tests gates (correr siempre tras cambio)

```bash
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short
cd backend && .venv/bin/pytest tests/architecture/test_brand_editable_fields_baseline.py tests/architecture/test_buyer_persona_editable_fields_baseline.py -x -q
cd backend && .venv/bin/pytest tests/modules/copilot/test_conversational_questioning.py -x -q
cd backend && .venv/bin/pytest tests/modules/brand/ -x -q
cd frontend && npx vitest run src/__tests__/architecture/
cd frontend && npx vitest run src/features/brand-studio/
```

507 BE arch + 38 FE arch baseline post-Fase-09. Sin regression.

## Cuando dudar, **preguntar** al user

Antes codear, si:
- Cambio toca persisted brand data → **¿hay tenants en prod? ¿re-extraemos buyer personas?**
- UVP / posicionamiento → **¿es ajuste copy o re-positioning? ¿qué EBT? ¿te alineá con narrative one_liner actual?**
- Personality → **¿chat o copy estática? ¿target tone (warmth/humor/energy)?**
- Buyer persona → **¿GLOBAL o offer-scoped? ¿es_primary?**
- Archetype → **¿qué hace tu marca (enseña/transforma/acompaña/etc.)?**
- Voice copy → **¿target EBT? ¿microempresario en qué tier de marketing literacy?**

## Pattern conversacional (cuando skill se invoca)

1. User describe en lenguaje negocio (ej. "querés que el copilot suene más cercano").
2. Mapeá a layer/aggregate (PersonalityProfile.dimensions.warmth + linguistic_patterns.greeting).
3. Confirmá ("Voy a subir warmth de 0.4 a 0.7 + cambiar greeting de 'Hola' a 'Hola, ¿qué tal?'. ¿OK?").
4. Web search 2026 si dudás copy/framework.
5. Implementá Override / repo update / etc.
6. Run tests gates.
7. Reportá: archivos tocados + assets a regenerar (landings) + copilot impact.

## Docs anchor

- `docs/domains/brand/INDEX.md` (todos los docs brand)
- `docs/refactors/field-contract-platform/DESIGN.md` (FieldContract platform — Fase 04-09)
- `docs/refactors/field-contract-platform/LEARNINGS.md` (descubrimientos Fase 06 brand + Fase 07 buyer)
- `~/.claude/projects/.../memory/feedback_personality_3_pillars.md` (PersonalityProfile arq)
- `~/.claude/projects/.../memory/feedback_form_runtime_autosave.md` (form-runtime no-negociable)
- `.claude/rules/spanish-text.md` (neutro LATAM)
- `.claude/rules/tdd-mandatory.md` (test antes impl)

## Peer skills

- `offer-expert` — cuando el cambio toca offers (incluye lead-magnet, archetype, presets).
- `offer-type-preset-expert` — narrow scope preset catalog.
- `sales-agent-expert` — si cambio toca sales-agent graph / prompts / tools.
- `content-hunter` — si quiere ideas de contenido (consumes brand voice + offer promise).
- `brand-offer-auditor` — audita cobertura framework marketing (10 frameworks).
