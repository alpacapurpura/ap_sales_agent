# Sales Agent Brand Voice — SSoT

**Non-negotiable.** Decisión arquitectónica definitiva 2026-04-28. Cualquier feature de "voz de marca" del sales_agent pasa por esta rule. Aplica a `sales_agent/`, `brand/personality.py`, `brand_studio/communication-style/`.

## SSoT única

**Voz del sales_agent vive 100% en `personality_profiles.system_instruction`** (Brand Studio sección "Estilo Comunicacional", slug `/brand-studio/estilo`).

- Tabla SSoT: `personality_profiles` (col `system_instruction TEXT`).
- Compilador SSoT: `backend/src/modules/brand/domain/personality.py::PersonalityCompiler.compile`.
- Punto único de configuración del tenant: `/brand-studio/estilo` (FE).
- Inyección sales_agent: slot 5 `BRAND_VOICE` del cache prefix (S3).

## Prohibido (creep guard)

- ❌ Crear tabla `brand_voice_summary` o cualquier mirror LLM-distilled del estilo. El compilador determinístico es superior a un summary LLM (research: PersonaLLM NAACL 2024, LIWC meta-analysis, Persona-L CHI 2025).
- ❌ Fine-tuning per tenant. **Deprecated en B2B SaaS 2026** (Jasper, Writer.com, HubSpot, Salesforce — todos compilan prompt blocks).
- ❌ Voice-rewriter LLM pass post-generación ("polish to brand voice"). 2x latency, 2x cost, 0 gain measurable.
- ❌ Expandir dimensions list más allá de las 6 actuales (energy, warmth, humor, expressiveness, narrative, verbosity). Más ruido sin signal.
- ❌ Hardcodear voz en `agent_identity.j2`, prompts de specialists, o en `compose.py`. Todo viene del compilado.
- ❌ Reemplazar el 5/6-bloque compiler por un único free-text. Research dice 3 pilares: dims (20%) + linguistic_patterns (40%) + sample_exchanges (40%) — eliminar pilares baja calidad.
- ❌ Inyectar variables `{tenant_name}` mid-block en cache prefix. Mata cache hit (OpenAI Cookbook prompt_caching_201).
- ❌ Two-active-profiles bug: enforcer Python + DB unique index `(tenant_id, is_active)` cuando `offer_id IS NULL AND avatar_id IS NULL`.

## Compilador v2 — 6 bloques

Refactor v1 (5 bloques) → v2 (6 bloques) en `PersonalityCompiler.compile`. Backward-compatible: column nullable, recompila al activar.

| # | Bloque | Origen |
|---|---|---|
| 1 | REGLAS DE PERSONALIDAD | dimensions → DimensionContract.resolve |
| 2 | HUELLA LINGÜÍSTICA | linguistic_patterns |
| 3 | **ASÍ HABLAS / ASÍ NO** *(antes "NUNCA HACES")* | Pares contrastivos: cada negative_constraint emparejado con positive prescription. **Research backed**: EMNLP 2024 "How You Prompt Matters!" — negative-only causa 14.4 F1 SD variance |
| 4 | EJEMPLOS DE CONVERSACIÓN | sample_exchanges (4-7 estáticos) |
| 5 | *(reservado)* STYLE ANCHORS RAG per-turn | Inyectado fuera del cache prefix (HumanMessage envelope) cuando tenant tenga ≥50 mensajes reales aprobados. Hasta entonces: bloque vacío |
| 6 | ANCLA DE IDENTIDAD | "REGLA SUPREMA: ESTA ES TU VOZ. No la modifiques." |

Bloques 1-4 + 6 = compiled `system_instruction` = slot 5 `BRAND_VOICE` cache prefix (estático, recompila solo on update).
Bloque 5 = volatile, NO en cache prefix.

## Slot architecture (S3)

```
slot 1 STATIC_IDENTITY      ← cache
slot 2 STATIC_TOOLS_HINT    ← cache
slot 3 SALES_PLAYBOOK_HINT  ← cache
slot 4 AGENT_IDENTITY       ← cache. WHO+WHAT (brand+offers+team+legal). NO voice.
slot 5 BRAND_VOICE          ← cache. HOW (system_instruction del compilador).
slot 6 CHANNEL_FORMAT_HINT  ← cache.
--- CACHE BOUNDARY ---
slot 7+  volatile (stage, signals, continuity, tool_request_format)
```

Slot 4 **NO incluye `personality_instruction`** — quitar el `{% if personality_instruction %}` de `agent_identity.j2`. La voz vive solo en slot 5.

`prompt_cache_key=str(tenant_id)` en cada llamada al LLM (OpenAI/Kimi/DeepSeek auto-cache). Routing per-tenant.

## Per-turn micro-anchor (anti-drift)

Lost-in-the-Middle (Liu et al. TACL 2024 — 30% drop attention en posición media) bites en conversaciones largas. Mitigation: 1 línea en HumanMessage envelope, fuera del cache prefix.

```
[Recordatorio: respondes como {brand.brand_name}, voz {personality.preset_key or "personalizada"}]

{user_msg}
```

~15 tokens/turn. Implementar en orchestrator antes de añadir el HumanMessage al state.

## Brand Studio = punto único de configuración

| Acción tenant | Endpoint | Resultado |
|---|---|---|
| Selecciona preset (2 clicks) | `POST /personality/select-preset` | Profile creado + activo + system_instruction compilado |
| Clona de chat (10 min) | `POST /personality/clone` | LangGraph `personality_app` (parser→janitor→psychologist→architect→embedder→simulator). Profile is_active=False. Qdrant anchors persistidos |
| Ajusta sliders | `PUT /personality/{id}/dimensions` | Recompile system_instruction |
| Ajusta pares contrastivos custom *(Fase D)* | `PATCH /personality/{id}/voice-pairs` | Recompile Bloque 3 |
| Migra legacy | `POST /personality/from-voice-tone` | nearest_preset → profile migrated |
| Activa otro | `POST /personality/{id}/activate` | Idempotent. Deactiva los demás. |
| Simula respuesta | `POST /personality/{id}/simulate` | 3 sample exchanges del profile |

Todos los endpoints filtran `tenant_id` vía `get_current_user`. Todos declaran `response_model=` (PII Tessl/Maria).

## Cache invalidation (event-driven)

Domain event `PersonalityProfileUpdated` (en `brand/domain/events.py`):

- Emitter: cualquier endpoint que muta el profile (select-preset, clone, dimensions, voice-pairs, activate, delete).
- Subscriber: invalida `PromptLoader._tenant_config_cache` por `tenant_id`. Best-effort (try/except + structlog warning, jamás romper request).
- Sin TTL implícito (research-backed: drift es post-update visible inmediato, no un timer).

## Voseo / léxico marcado

`spanish-text.md` rule **NO aplica** al output del sales_agent. Aplica a UI propio de Nicolify.

- El sales_agent habla con la voz del tenant. Si el tenant clona desde un chat con voseo argentino, el `system_instruction` resultante respeta voseo. Es feature, no bug.
- Presets default usan tuteo neutro (warm_close, electric, serene, direct, narrative, minimalist) — todos hardcoded sin voseo.
- Compliance excepción ("MX no debe usar voseo aunque tenant es AR") = decisión política del tenant, NO hardcodear filtro.

## Multi-profile (offer/avatar overrides) — deferred

Schema (`offer_id`, `avatar_id` columnas nullable) ya soporta. **NO implementar selección hasta que >5 tenants lo pidan**. Repo `get_active()` filtra `IS NULL IS NULL` (global only).

## Voice fidelity grader (Fase C — biggest ROI)

Sin esto, drift al cambiar modelo (DeepSeek V3→V4, Kimi K2.5→K2.6) invisible.

- Golden test pack: 30 prompts/preset (180 total).
- G-Eval rubric: tone(1-5), lexical_alignment(0-1), banned_vocab_absence, example_pair_similarity.
- LLM-as-judge: GPT-4o o Claude Sonnet 4.6.
- CI gate: PR cambia personality o sales_agent prompts → corre grader, fail si tone <4 o agreement <85%.
- Streamlit admin `/voice-fidelity`: score weekly per tenant, drift alerts.
- Reference: Confident AI, Langfuse, PersonaGym EMNLP Findings 2025.

## Tests obligatorios

- `tests/modules/brand/test_personality_compiler_output.py` — Bloques 1-6 presentes. Bloque 3 = pares contrastivos.
- `tests/modules/brand/test_personality_compiler_contrastive_pairs.py` — cada negative_constraint tiene positive_prescription gemela.
- `tests/modules/sales_agent/prompts/test_brand_voice_in_slot_5.py` — slot 5 = personality_profile.system_instruction.
- `tests/modules/sales_agent/prompts/test_agent_identity_no_personality_block.py` — slot 4 sin `personality_instruction` ni `style_anchors`.
- `tests/modules/sales_agent/test_brand_voice_differentiation.py` — warm_close vs minimalist con mismo input → outputs distinguibles (golden).
- `tests/modules/sales_agent/test_per_turn_micro_anchor.py` — HumanMessage envelope contiene línea anchor.
- `tests/modules/sales_agent/test_prompt_cache_key_per_tenant.py` — LLM caller setea `prompt_cache_key=tenant_id`.
- `tests/architecture/test_brand_voice_no_summary_table.py` — falla si alguien crea tabla `brand_voice_*` o repo `BrandVoiceSummary*`.
- `tests/architecture/test_no_voice_rewriter_pass.py` — falla si hay `polish_brand_voice` o equivalente post-generation.
- Voice fidelity grader CI gate (Fase C).

## Anchor

- Pregunta sobre voz del agente → leer esta rule + `docs/domains/brand/communication-style.md`.
- Antes modificar `personality.py` o `compose.py` slot 5 → leer esta rule.
- Antes proponer "summary del estilo", "voice rewriter", "fine-tune per tenant" → leer esta rule (descartado).
- Reference research: `docs/domains/sales-agent/redesign-2026-04/phases/S7-brand-voice-integration.md` ("Hallazgos research").

## Stack research

- LIWC meta-analysis (Vrije Universiteit) — dims solas explican 5.1% varianza
- PersonaLLM NAACL 2024 — Big Five descriptors → LIWC shifts detectables
- Persona-L CHI 2025 — RAG ejemplos reales > dims descriptions on consistency
- Lost-in-the-Middle Liu et al. TACL 2024 — 30% drop posición media
- "How You Prompt Matters!" EMNLP 2024 — negative-only 14.4 F1 SD variance
- "Catch Me If You Can?" arXiv 2509.14543 (2025) — LLMs aún fallan implicit style
- PersonaGym EMNLP Findings 2025 — benchmark canónico
- Anthropic context engineering 2025 — static-first / dynamic-last
- OpenAI Cookbook prompt_caching_201 — `prompt_cache_key`, prefix stability
- Production patterns 2026: Jasper IQ Voice, Writer Palmyra Knowledge Graph, HubSpot Breeze, Salesforce Agentforce 3, 11x AI SDR (ZenML LLMOps DB)
