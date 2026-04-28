# Learnings · S7 · brand-voice-integration

> Retroactivo (creado en S8 — handoff repair). Commit `f13914de`.

---

## Resumen (3 líneas)

- **Entregado**: voz del sales_agent migrada a `personality_profiles.system_instruction` (SSoT única). Compiler v2 (6 bloques con Bloque 3 pares contrastivos `ASÍ HABLAS / ASÍ NO`). Slot 5 `BRAND_VOICE` cacheable per-tenant. Per-turn micro-anchor en HumanMessage. `prompt_cache_key=tenant_id`. Domain event `PersonalityProfileUpdatedEvent`. Voice fidelity grader (Fase C/G-Eval) implementado.
- **Decisión no obvia**: descartar plan v1 (`brand_voice_summary` table + LLM-distilled summary worker). Reusar engine determinístico existente `PersonalityCompiler`. Ahorra una tabla mirror, evita drift entre 2 SSoTs, calidad superior (research-backed: PersonaLLM NAACL 2024, LIWC, Persona-L CHI 2025).
- **Listo para S8**: `compose_system_prompt(state)` slot 5 inyecta voz tenant; tools nuevos del scheduler heredan voz vía LLM call con `prompt_cache_key=tenant_id`. `agent_identity.j2` ya sin `personality_instruction` ni `style_anchors` → libre para WHO+WHAT del scheduler.

---

## Decisiones clave

- **`personality_profiles.system_instruction` como SSoT vs tabla mirror `brand_voice_summary`**:
  - Tomada: SSoT única en `personality_profiles`.
  - Razón: el compilador determinístico ya rinde calidad superior a un summary LLM-distilled. Crear tabla mirror introduce drift inevitable entre 2 SSoTs y duplica trabajo (worker regen + invalidación + tests). Brand Studio "Estilo Comunicacional" ya es punto único de configuración del tenant.
  - Alternativa descartada: `brand_voice_summary` table + worker `regenerate_brand_voice_summary` (plan v1). Razón: PersonalityCompiler v1 con 5 bloques ya cubría 90% del objetivo; los gaps eran 4 refinements puntuales (R1–R4) que se cierran sin tabla nueva.

- **Compiler v2 con `ASÍ HABLAS / ASÍ NO` (pares contrastivos) vs solo `NUNCA HACES` (negative-only)**:
  - Tomada: pares contrastivos. Cada `negative_constraint` emparejado con `positive_prescription`.
  - Razón: research EMNLP 2024 ("How You Prompt Matters!") muestra que negative-only causa 14.4 F1 SD variance vs negative+positive. El LLM internaliza mejor el "qué hacer" cuando ve el espejo del "qué no".
  - Alternativa descartada: mantener compiler v1 (5 bloques, negative-only). Razón: drift latente al cambiar modelo (DeepSeek V3→V4, Kimi K2.5→K2.6) sin grader es invisible.

- **Per-turn micro-anchor en HumanMessage envelope vs anclar solo en system prompt**:
  - Tomada: `[Recordatorio: respondes como {brand}, voz {preset}]\n\n{user_msg}` (~15 tok/turn).
  - Razón: Lost-in-the-Middle (Liu et al. TACL 2024) — 30% drop attention en posición media. Conversaciones largas degradan voz. Micro-anchor fuera del cache prefix (volatile) garantiza re-grounding sin matar cache hit.
  - Alternativa descartada: solo confiar en slot 5 cacheado. Razón: validado en goldens diff long-context que la voz drifteaba post-turn 12.

- **`prompt_cache_key=tenant_id` vs sin routing key**:
  - Tomada: setear en cada LLM call.
  - Razón: OpenAI Cookbook prompt_caching_201 + Kimi/DeepSeek auto-cache disk-based requieren routing per-tenant para hit rate ≥60%. Sin key, cross-tenant evictions destruyen el ahorro.
  - Alternativa descartada: confiar en cache automático sin key. Razón: research-backed (Anthropic 2025, OpenAI Cookbook) que el routing explícito es necesario para multi-tenant.

- **Domain event `PersonalityProfileUpdated` (sync subscriber) vs TTL en `PromptLoader._tenant_config_cache`**:
  - Tomada: event-driven invalidation, sync, best-effort.
  - Razón: tenant edita preset/dimensions/clone → invalidación inmediata visible en próximo turn, sin race entre TTL clock y user expectation. TTL implícito esconde drift no-determinístico.
  - Alternativa descartada: TTL `cachetools.TTLCache(maxsize=N, ttl=300)`. Razón: tenant prueba cambio + manda mensaje al canal en <1min — TTL daría miss inconsistente.

---

## Sorpresas / gotchas críticos

- **`agent_identity.j2` mezclaba WHO+WHAT+HOW**: bloque `personality_instruction` (línea 19-24) y `style_anchors` (línea 28-36) vivían dentro del slot 4 (AGENT_IDENTITY). Ese slot debía ser brand+offers+team+legal — strip obligatorio antes de poblar slot 5 limpio. Cualquier feature futuro que toque `agent_identity.j2` debe respetar la separación: voz NO vive ahí.

- **`style_anchors` era dead code**: el bloque Jinja esperaba variable que `knowledge_builder` nunca pasaba. Apareció vivo en grep pero no llegaba al render. Mover a Bloque 5 RAG anchors per-turn (Fase E, gated por tenant ≥50 ejemplos reales aprobados).

- **2-active-profiles bug latente**: `personality_profiles` tenía `(tenant_id, is_active=True)` sin unique index cuando `offer_id IS NULL AND avatar_id IS NULL`. Activación de un nuevo profile sin desactivar el anterior dejaba 2 ACTIVE — `get_active()` retornaba el primero arbitrario. Fix en S7: enforcer Python en `activate()` + DB unique partial index. Multi-profile (offer/avatar overrides) sigue schema-only en S7 — gated a >5 tenants pidiéndolo.

- **`spanish-text.md` rule NO aplica al output del sales_agent**: la rule cubre UI propio de Nicolify. Tenant que clonó voz desde un chat con voseo argentino quiere que el agente respete voseo — es feature, no bug. Compliance excepción ("MX no debe usar voseo aunque tenant es AR") = decisión política del tenant, NO hardcodear filtro.

---

## Recomendaciones accionables para S8

- [x] **Tools nuevos del scheduler invocan LLM con `prompt_cache_key=tenant_id`** — heredan voz tenant via slot 5 sin trabajo extra.
- [x] **Reminder messages (T-24h/T-1h/T+1h) renderizan template Jinja + LLM call** — no concatenar string. Garantiza voz consistente con conversación.
- [x] **NO crear tabla mirror `*_voice_summary`** — antipatrón validado. SSoT en `personality_profiles.system_instruction`.
- [x] **NO inyectar voz mid-block en cache prefix** (kill cache hit). Mantener slot 5 contiguo.
- [x] **NO hardcodear voseo/lexicon en templates de sales_agent** — la voz viene del compilado del tenant, no del template.
- [x] **Subscribers a domain events** que muten state visible al usuario deben ser sync best-effort (mismo pattern que `PersonalityProfileUpdated` invalidation).

---

## Hooks listos

- `backend/src/modules/sales_agent/application/prompts/compose.py::compose_system_prompt(state)` — slot 5 ya populated con `personality_profile.system_instruction`. Tools que llamen LLM heredan automático.
- `backend/src/modules/sales_agent/application/services/knowledge_builder.py::build_knowledge` — retorna `BrandKnowledgeDTO` con `personality_instruction` + `personality_preset_key`. Reuse en reminders.
- `backend/src/shared/domain/events.py::PersonalityProfileUpdatedEvent` — mismo pattern para nuevos eventos S8 (BookingLinkCreatedEvent, BookingMissedEvent).
- `backend/src/modules/brand/application/voice_fidelity/grader.py` — G-Eval rubric base. Reusable para validar reminders post-S8.
- `.claude/rules/sales-agent-brand-voice.md` — rule SSoT. Cualquier feature de voz pasa por ahí.

---

## Riesgos abiertos

- **Voice fidelity grader (Fase C) aún no integrado a CI gate**. Sigue como Streamlit admin `/voice-fidelity` + script manual. Hasta wiring en `/test-all`, drift al cambiar modelo es invisible. Watchpoint S10.
- **Multi-profile per offer/avatar** (G8): schema permite (`offer_id`, `avatar_id` nullable) pero código `get_active()` filtra `IS NULL IS NULL`. Si tenant pide variant voz por oferta antes de S+1, reabrir.
- **Bloque 5 STYLE ANCHORS RAG vacío** hasta tenant ≥50 mensajes reales aprobados. Si voz suena monótona porque sample_exchanges (4-7 estáticos) repite, escalar la curación de anchors.

---

## Tech debt detectado (NO arreglado)

- [LOW] Voice fidelity grader sin CI gate → `05-tech-debt-log.md` (DEFERRED-S10).
- [LOW] Multi-profile per offer/avatar (G8) → `05-tech-debt-log.md` (DEFERRED-deferred-gated por demand).
- [LOW] Custom voice pairs per-tenant editables (Fase D UX) → backlog Brand Studio.

---

## Fuentes research útiles

- [Persona-L CHI 2025] — RAG ejemplos reales > dims descriptions on consistency. Cambió: priorizar sample_exchanges + linguistic_patterns sobre solo dims (40/40/20 weighting).
- [How You Prompt Matters! EMNLP 2024] — negative-only 14.4 F1 SD variance. Cambió: Bloque 3 pasa de `NUNCA HACES` solo a pares contrastivos `ASÍ HABLAS / ASÍ NO`.
- [Lost-in-the-Middle TACL 2024 · Liu et al.] — 30% drop attention posición media. Cambió: per-turn micro-anchor en HumanMessage envelope.
- [OpenAI Cookbook prompt_caching_201] — `prompt_cache_key` mandatorio multi-tenant. Cambió: añadir routing key explícito.
- [PersonaGym EMNLP Findings 2025] — benchmark canónico. Cambió: rúbricas del grader Fase C derivadas de ahí.

---

## Métricas medidas

- Compiler v2 emite 6 bloques con Bloque 3 pares contrastivos: tests `test_personality_compiler_v2.py` + `test_personality_compiler_contrastive_pairs.py` verde.
- Slot 5 = system_instruction; slot 4 sin voz: tests `test_brand_voice_slot.py` + `test_agent_identity_no_personality_block.py` verde.
- Goldens warm_close vs minimalist con mismo input → outputs distinguibles: `test_brand_voice_differentiation.py` verde.
- 2065 insertions / 344 deletions / 31 archivos (commit `f13914de`).
