# S7 · Brand voice integration ("Estilo Comunicacional")

> **Plan revisado 2026-04-28.** Ver `.claude/rules/sales-agent-brand-voice.md` para la rule SSoT (no negociable).

## Objetivo

Sales_agent suena como la marca real del tenant — **no como chatbot genérico**. Lee `personality_profiles.system_instruction` (Brand Studio sección "Estilo Comunicacional", `/brand-studio/estilo`) y lo inyecta en slot 5 del system prompt (S3) como bloque cacheable per-tenant. Specialists hablan con tono, vocabulario, ritmo, emojis, ejemplos do/don't, frases prohibidas del tenant — todo derivado de un compilador determinístico de 6 bloques.

## Dependencias

- S3 cerrado: `compose_system_prompt` con cache_boundary + slot 5 reservado.
- S6 cerrado: ratchet evita drift.
- Brand Studio "Estilo Comunicacional" activo desde 2026-04-21 (`docs/domains/brand/communication-style.md`).

## Hallazgos research (2026-04-28)

### Estado actual confirmado

- ✅ `PersonalityProfile` engine implementado: 3 pilares (dimensions × 6, linguistic_patterns, sample_exchanges) → `PersonalityCompiler.compile` → 5-bloque `system_instruction` cacheado en DB col.
- ✅ 6 presets construidos (`warm_close`, `electric`, `serene`, `direct`, `narrative`, `minimalist`).
- ✅ Clone via LangGraph `personality_app` (parser→janitor→psychologist→architect→embedder→simulator). Endpoint `POST /personality/clone` operativo.
- ✅ Sales_agent ya consume `personality_profile.system_instruction` vía `BrandKnowledgeDTO` en `knowledge_builder.py:124-127`.
- ✅ Frontend `/brand-studio/estilo` con 9 hooks operativos.
- ✅ Tests: preset selection, dimension update, fallback voice_tone (14 tests pass smoke).

### Gaps detectados

| # | Gap | Severidad |
|---|---|---|
| G1 | Slot 5 vacío. `personality_instruction` actualmente embebido en slot 4 (`agent_identity.j2`). Mezcla WHO+WHAT+HOW. | P0 — corregir en S7 |
| G2 | Bloque `style_anchors` en `agent_identity.j2:28-36` espera variable que `knowledge_builder` nunca pasa. Dead code; cablearlo en slot 4 rompería cache. | P0 — strip o mover |
| G3 | Sin `prompt_cache_key=tenant_id` en LLM caller. Cache routing per-tenant no garantizado. | P0 |
| G4 | Compiler v1: bloque 3 `NUNCA HACES` solo negative-only. EMNLP 2024 dice 14.4 F1 SD variance. | P1 — refactor v2 |
| G5 | Sin per-turn micro-anchor en HumanMessage envelope. Lost-in-the-Middle bites en conversaciones largas. | P1 |
| G6 | Sin domain event `PersonalityProfileUpdated`. `PUT /dimensions` recompila DB pero no invalida `PromptLoader._tenant_config_cache`. | P1 |
| G7 | Sin voice fidelity grader. Drift al cambiar modelo (V3→V4) invisible. | P1 — Fase C |
| G8 | `offer_id`/`avatar_id` columns existen pero `get_active()` filtra `IS NULL IS NULL`. Multi-profile schema-only. | P2 — deferred |
| G9 | Sin guard de voseo en clones (presets safe, hardcoded). | P2 — feature, no bug |

### Best practices SOTA validadas (research synth)

- 5/6-bloque compiler with anchor at end → **correcto** (Lost-in-the-Middle Liu et al. TACL 2024).
- Static-first / dynamic-last layout → **correcto** (Anthropic context engineering 2025; OpenAI prompt_caching_201).
- Pillar weighting dims (20%) < patterns (40%) < examples (40%) → **directionally validated** (LIWC meta-analysis 5.1% var; PersonaLLM NAACL 2024; Persona-L CHI 2025).
- Compiler-as-template vs fine-tuning per tenant → **correcto**. Production patterns 2026: Jasper IQ, Writer Palmyra, HubSpot Breeze, Salesforce Agentforce 3, 11x AI SDR. **Fine-tuning per tenant deprecated en B2B SaaS**.
- Cache per-tenant funcional con `prompt_cache_key=tenant_id` (Kimi K2.6 ~83% descuento, DeepSeek V4 ~90%).

### Refinements research-backed (4)

| # | Cambio | Source |
|---|---|---|
| R1 | `NUNCA HACES` → `ASÍ HABLAS / ASÍ NO` con pares contrastivos | EMNLP 2024 "How You Prompt Matters!"; Boonstra Prompt Engineering Guide |
| R2 | Per-turn micro-anchor en HumanMessage envelope (~15 tok/turn) | Anthropic 2025; Persona-L CHI 2025 |
| R3 | `prompt_cache_key=tenant_id` en LLM call. Arch test "no `{tenant_name}` mid-block" | OpenAI Cookbook prompt_caching_201 |
| R4 | Voice fidelity grader (G-Eval LLM-as-judge, 30 prompts/preset = 180 total) | Confident AI, Langfuse, PersonaGym EMNLP Findings 2025. **Biggest ROI inmediato** |

## Diseño definitivo

### SSoT

`personality_profiles.system_instruction` = único origen de la voz. Brand Studio = único punto de configuración del tenant.

**NO crear** `brand_voice_summary` table, `BrandVoiceUpdatedEvent`, worker `regenerate_brand_voice_summary`. Plan original v1 (LLM-distilled summary) **desechado** — duplica trabajo ya hecho con calidad inferior.

### Compiler v2 — 6 bloques

```
BLOQUE 1 — REGLAS DE PERSONALIDAD          (dims → DimensionContract.resolve)
BLOQUE 2 — HUELLA LINGÜÍSTICA              (linguistic_patterns)
BLOQUE 3 — ASÍ HABLAS / ASÍ NO             (pares contrastivos)
BLOQUE 4 — EJEMPLOS DE CONVERSACIÓN        (sample_exchanges 4-7 estáticos)
BLOQUE 5 — STYLE ANCHORS RAG (per-turn)    (vacío hasta tenant ≥50 ejemplos)
BLOQUE 6 — ANCLA DE IDENTIDAD              (REGLA SUPREMA: ESTA ES TU VOZ)
```

Bloques 1-4 + 6 → `system_instruction` (estático, slot 5 cache prefix).
Bloque 5 → volatile, HumanMessage envelope (Fase B+).

#### Bloque 3 estructura

`DimensionLevel` extender con `positive_prescriptions: list[str]` paralelo a `negative_constraints`. Compiler emite pares:

```
### ASÍ HABLAS / ASÍ NO

✅ Usa "puedes" / "tienes"        ❌ No uses "podés" / "tenés"
✅ Saluda breve y directo         ❌ No abras con preguntas personales
...
```

### Slot architecture

```python
# compose.py
slot 4 AGENT_IDENTITY      = WHO+WHAT (brand+offers+team+legal). NO voice.
slot 5 BRAND_VOICE         = personality_profile.system_instruction
```

`agent_identity.j2`: quitar bloques `personality_instruction` (líneas 19-24) y `style_anchors` (líneas 28-36).

### Per-turn micro-anchor

Orchestrator envuelve HumanMessage:

```python
def envelope_user_message(state, raw_msg):
    brand_name = state.brand_data["identity"]["brand_name"]
    preset = state.personality_profile.get("preset_key", "personalizada")
    return f"[Recordatorio: respondes como {brand_name}, voz {preset}]\n\n{raw_msg}"
```

### Cache invalidation

Domain event `PersonalityProfileUpdated`:

- Emitter: `select_preset`, `clone_from_material`, `update_dimensions`, `activate`, `delete`.
- Subscriber: `PromptLoader._tenant_config_cache.invalidate(tenant_id)`. Best-effort.

### `prompt_cache_key`

LLM caller (orchestrator) setea `prompt_cache_key=str(tenant_id)` en cada llamada. Routing per-tenant. Arch test verifica.

## Plan de fases

### Fase A — Foundation cleanup (P0, ahora)

1. **Doc decisión**: `.claude/rules/sales-agent-brand-voice.md` (rule SSoT) ✅
2. **Update plan**: este archivo ✅
3. **Smoke verify clone**: 14 tests pass ✅
4. **Strip dead `style_anchors` block** de `agent_identity.j2`. Comentario apunta a Fase B donde se cabla en volatile zone correctamente.

### Fase B — S7 core (slot split + compiler v2)

5. RED tests:
   - `test_brand_voice_in_slot_5.py` — slot 5 = system_instruction.
   - `test_agent_identity_no_personality_block.py` — slot 4 sin voice.
   - `test_compiler_v2_six_blocks.py` — bloques 1-6.
   - `test_compiler_contrastive_pairs.py` — Bloque 3 pares.
   - `test_per_turn_micro_anchor.py` — HumanMessage envelope.
   - `test_prompt_cache_key_per_tenant.py`.
   - `test_brand_voice_differentiation.py` — golden warm_close vs minimalist.
   - Arch tests: `test_no_brand_voice_summary_table`, `test_no_voice_rewriter_pass`.

6. GREEN:
   - Refactor `PersonalityCompiler` v1 → v2 (6 bloques + pares contrastivos).
   - Extender `DimensionLevel` con `positive_prescriptions`.
   - Recompile en migración (data) para profiles existentes.
   - `compose.py`: rename slot 5 `OFFER_SUMMARY` → `BRAND_VOICE`. Builder `_brand_voice(state)`.
   - `knowledge_builder` retorna `(agent_identity, brand_voice)` o builder paralelo.
   - `agent_identity.j2`: remover `personality_instruction` + `style_anchors`.
   - HumanMessage envelope helper.
   - LLM caller: `prompt_cache_key=tenant_id`.
   - Domain event `PersonalityProfileUpdated` + subscriber.

### Fase C — Voice fidelity grader (biggest ROI, post-B)

7. Golden test pack: 30 prompts/preset × 6 = 180.
8. G-Eval rubric implementación.
9. CI gate.
10. Streamlit admin `/voice-fidelity` dashboard.

### Fase D — Brand Studio UX (post-A)

11. Vista "Pares contrastivos" en `/brand-studio/estilo`. Custom pairs editables (`custom_voice_pairs` field).
12. Voice fidelity score visible al user.

### Fase E — Diferido (gated por data tenant)

13. Multi-profile per offer/avatar (>5 tenants lo pidan).
14. Per-turn RAG anchors funcional (tenant ≥50 ejemplos reales aprobados).

## Criterios de éxito

1. ✅ SSoT única `personality_profiles.system_instruction`. Sin tabla mirror.
2. Slot 5 `BRAND_VOICE` poblado con system_instruction; slot 4 sin voice.
3. Compiler v2 emite 6 bloques con Bloque 3 pares contrastivos.
4. Per-turn micro-anchor en HumanMessage envelope.
5. `prompt_cache_key=tenant_id` en cada LLM call.
6. Domain event invalida `PromptLoader` cache.
7. Voseo del tenant respetado si lo configuró (clone).
8. Goldens diff: warm_close vs minimalist con mismo input → outputs distinguibles.
9. Cache hit rate ≥60% mantenido.
10. Voice fidelity grader (Fase C): tone ≥4/5, judge-human agreement ≥85%.
11. Quality gates verdes (BE + FE + arch).

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Migración compiler v1→v2 invalida system_instructions existentes | Recompila on-read (lazy) o data migration explicita en Alembic |
| `positive_prescriptions` falta en presets actuales | Backfill catalog en mismo PR; arch test enforces |
| HumanMessage envelope rompe streaming UX | Test con channel chat y voice |
| `prompt_cache_key` no soportado por algún provider | Detect via capabilities; skip si missing (no fail) |
| Voseo del tenant choca con compliance LATAM | Documentar excepción. Decisión política tenant, no hardcodear |
| Bloque 5 (RAG anchors) confunde si vacío | Skip render si list vacía |

## Tech debt watchpoints

- Multi-profile per offer/avatar: schema permite, código no. Flag deuda en S7 closeout.
- `PromptLoader` sin TTL: domain event lo cubre, pero monitor.
- Voice fidelity grader = blocker para confianza en cambios de modelo. Priorizar Fase C antes de DeepSeek V3→V4 swap.

## Ajustes vs plan original v1

| Plan v1 (descartado) | Plan v2 (definitivo) |
|---|---|
| Crear tabla `brand_voice_summary` | NO. Usar `personality_profiles.system_instruction` |
| LLM-distilled summary regenerado por worker | Compilador determinístico Python (existente) |
| `BrandVoiceUpdatedEvent` + worker ARQ | `PersonalityProfileUpdated` event + subscriber sync |
| Inyectar lighthouse en slot 4 | Slot 5 dedicado `BRAND_VOICE` |
| 5-bloque compiler | 6-bloque compiler v2 con pares contrastivos |
| Sin per-turn anchor | Per-turn micro-anchor en HumanMessage envelope |
| Sin grader explícito | Fase C voice fidelity grader (G-Eval) |
| Sin `prompt_cache_key` mention | `prompt_cache_key=tenant_id` mandatorio |

Razón del giro: research-backed diagnosis 2026-04-28 reveló que (a) PersonalityProfile engine + 5-bloque compiler ya cumplen 90% del objetivo con calidad superior a un summary LLM-distilled, (b) 4 refinements puntuales (R1-R4) cierran el gap a SOTA, (c) duplicar el trabajo en una tabla mirror introduce drift entre dos SSoTs.
