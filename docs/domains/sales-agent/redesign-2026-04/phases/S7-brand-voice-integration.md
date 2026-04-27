# S7 · Brand voice integration ("Estilo Comunicacional")

## Objetivo

Sales_agent suena como la marca real del tenant — **no como chatbot genérico**. Lee `Estilo Comunicacional` de Brand Studio (campo del módulo `brand`), pre-renderiza un `brand_voice_summary` cacheable y lo inyecta en slot 4 del system prompt (S3). Specialists hablan con tono, vocabulario, ritmo, emojis, ejemplos do/don't, frases prohibidas del tenant.

## Dependencias

- S3 cerrado: `compose_system_prompt` con cache_boundary + slot 4 reservado para lighthouse.
- S6 cerrado: ratchet evita drift.

## Criterios de éxito

1. Tabla `brand_voice_summary` (mirror de `brand_summary` de copilot F3) con columnas: `tenant_id`, `summary_text`, `voice_examples`, `forbidden_phrases`, `dos_donts`, `last_updated_at`.
2. ARQ task `regenerate_brand_voice_summary(tenant_id)` corre cuando Brand Studio actualiza `Estilo Comunicacional` (vía domain event `BrandVoiceUpdatedEvent`).
3. `_agent_identity_lighthouse(state)` (slot 4 de S3) lee `brand_voice_summary` cacheado en lugar de Jinja render fresco.
4. Goldens diff: respuesta del agente para tenant A ≠ tenant B con mismo input cuando sus `Estilo Comunicacional` difieren significativamente.
5. Voseo / léxico marcado del tenant respetado si lo configuró (override del default Spanish neutro). Ejemplo: tenant argentino que vende a Argentina puede usar voseo en su voz de marca.
6. Specialists nodes invocan `compose_system_prompt(state)` y reciben slot 4 poblado.
7. Cache hit rate ≥60% mantenido.
8. Quality gates verdes.

## Research mandate

### Queries WebSearch obligatorias

1. `brand voice prompt engineering style transfer LLM 2026 examples-based` — best practice de transferencia de estilo.
2. `prompt cache invariance brand-specific content per-tenant 2026` — cómo cachear per-tenant manteniendo cross-tenant prefix.
3. `style guide do don't list prompt LLM positive negative examples` — formato.

### Tessl tiles

- N/A primaria.

### Lectura obligatoria

- Aprendizajes S0-S6.
- `backend/src/modules/brand/domain/` — schema completo de Brand Studio.
- **Buscar campo `Estilo Comunicacional`** en `backend/src/modules/brand/domain/` o `frontend/src/features/brand-studio/schemas/` — verificar nombre exacto, shape (free-text vs structured), si existe.
- `backend/src/modules/copilot/domain/brand_summary.py` (F3 implementation).
- `backend/src/modules/copilot/observability/workers/brand_summary_regen.py` (si existe en path post-rebuild).
- Skill `.claude/skills/brand-expert/SKILL.md`.

### Hallazgos research

> COMPLETAR. **Verificar nombre exacto del campo `Estilo Comunicacional` en Brand Studio antes de codear.** Puede llamarse `voice_tone`, `communication_style`, `brand_voice`, etc.

---

## Diseño

### `brand_voice_summary` table

```sql
CREATE TABLE IF NOT EXISTS brand_voice_summary (
    tenant_id UUID PRIMARY KEY,
    summary_text TEXT NOT NULL,
    voice_examples JSONB DEFAULT '[]',  -- list of {input, ideal_output}
    forbidden_phrases JSONB DEFAULT '[]',
    dos_donts JSONB DEFAULT '{"do": [], "dont": []}',
    last_source_hash TEXT,  -- hash of brand fields used; skip regen if unchanged
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Domain event listener

```python
# src/modules/brand/domain/events.py
class BrandVoiceUpdatedEvent(DomainEvent):
    @classmethod
    def create(cls, tenant_id, fields_changed): ...

# Brand publishes when "Estilo Comunicacional" or related fields change.
# Subscriber en sales_agent (or shared workers/) re-genera summary.
```

### ARQ task `regenerate_brand_voice_summary`

```python
async def regenerate_brand_voice_summary(ctx, tenant_id: UUID):
    brand = await brand_repo.get_full_brand(tenant_id)
    new_hash = hash_brand_voice_fields(brand)
    existing = await brand_voice_summary_repo.get(tenant_id)
    if existing and existing.last_source_hash == new_hash:
        return  # skip regen
    summary = await _build_summary_via_llm(brand)  # NANO model, tier MINI
    voice_examples = _extract_examples(brand)
    forbidden = brand.communication_style.forbidden_phrases  # adjust per actual schema
    dos_donts = brand.communication_style.dos_donts
    await brand_voice_summary_repo.upsert(BrandVoiceSummary(
        tenant_id=tenant_id, summary_text=summary, voice_examples=voice_examples,
        forbidden_phrases=forbidden, dos_donts=dos_donts, last_source_hash=new_hash,
    ))
```

### Slot 4 de S3 con lighthouse

```python
def _agent_identity_lighthouse(state) -> str:
    summary = brand_voice_summary_cache.get(state.tenant_id)  # in-process cache 5min TTL
    if summary is None:
        return ""  # graceful degradation
    return f"""## Voz de marca (cómo debes hablar)

{summary.summary_text}

### Frases que SÍ usás:
{format_examples(summary.dos_donts.get('do', []))}

### Frases que NUNCA usás:
{format_examples(summary.dos_donts.get('dont', []))}
{format_examples(summary.forbidden_phrases, label='Prohibidas:')}

### Ejemplos de tu voz:
{format_voice_examples(summary.voice_examples)}
"""
```

### Voseo / léxico marcado

`spanish-text.md` rule pide neutro. **Excepción documentada**: si el tenant define explícitamente voseo en su `Estilo Comunicacional` → respetarlo (es la voz de marca de ese negocio). Default sigue neutro. Test cubre ambos casos.

---

## Plan TDD

### RED tests

1. `tests/modules/brand/test_brand_voice_summary_regen.py`:
   - Hash inalterado → no regenera.
   - Hash distinto → regenera + persist.
   - Subscribe a `BrandVoiceUpdatedEvent` triggers task.

2. `tests/modules/sales_agent/prompts/test_lighthouse_in_slot_4.py`:
   - `compose_system_prompt(state)` slot 4 contiene `summary_text` del tenant.
   - Tenant sin lighthouse → slot 4 vacío (graceful).

3. `tests/modules/sales_agent/prompts/test_brand_voice_differentiation.py`:
   - Tenant A (formal) vs Tenant B (casual con voseo) con mismo input → outputs distinguibles.
   - Test usa goldens.

4. `tests/modules/sales_agent/test_voseo_respected_per_tenant.py`:
   - Default tenant: salida sin voseo.
   - Tenant con voseo en `Estilo Comunicacional`: salida con voseo.

5. `tests/architecture/test_brand_voice_summary_cache_invalidation.py`:
   - Update Brand → event → regen → cache invalidated → next turn usa nueva voz.

---

## Implementación step-by-step

1. **Verificar field name** en Brand Studio (research mandate).
2. Migración Alembic idempotente para `brand_voice_summary`.
3. Modelo SQLA + repo.
4. Domain event `BrandVoiceUpdatedEvent` (en `brand/domain/events.py`).
5. ARQ task `regenerate_brand_voice_summary` con hash short-circuit.
6. Subscriber en `brand_voice_summary` worker.
7. Implementar `_agent_identity_lighthouse` slot 4 en compose.py (S3).
8. Brand Studio FE wire (si necesita) — emite event al guardar campo.
9. Goldens nuevos: tenant fixture con voz formal + tenant fixture con voz casual.
10. Manual smoke: tenant test con voseo configured → verificar respuesta.

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Field `Estilo Comunicacional` no existe en Brand Studio | Research detect. Si falta → coordinar con usuario antes de S7 (puede requerir fase Brand Studio extra). |
| Voseo de tenant rompe lint Spanish neutro de FE | Distinción: spanish-text.md aplica a UI propio de Nicolify; el output del sales_agent es del tenant. Documentar excepción. |
| Cache invalidation lag | TTL 5min in-process + invalidación explícita en regen. |
| LLM-generated summary inconsistente | Stub determinístico para tests; real LLM solo en weekly cron / opt-in. |
| `voice_examples` muy largo rompe cache size | Cap 10 ejemplos. Ranking por relevancia. |

---

## Tech debt watchpoints

- Si Brand Studio NO tiene `Estilo Comunicacional` → escalar al usuario, **NO crear el campo en esta fase** (scope creep). Loggear como gap.
- Si Brand Studio cambia campo voice durante un commit reciente → coordinar con dueño del módulo.
- Si voseo del tenant choca con compliance ("MX no debe usar voseo aunque tenant es AR") → escalar políticamente, NO hardcodear.

---

## Ajustes vs plan original

> COMPLETAR.
